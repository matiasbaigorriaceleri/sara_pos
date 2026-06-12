import os
import sys
import bcrypt
import shutil
import subprocess
import platform
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFileDialog,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QSpinBox,
    QCheckBox,
)

from PySide6.QtCore import Qt
from app.assets.themes.theme import PRIMARY_COLOR, INPUT_STYLE, BUTTON_STYLE
from app.database.database import SessionLocal, reload_engine, test_connection, get_db_mode
from app.utils.license_manager import (
    validate_license, save_license, load_license,
    get_current_plan, get_plan_limits, is_feature_allowed,
)
from app.models.settings_model import Setting
from app.models.user_model import User
from app.components.collapsible_section import CollapsibleSection


SMTP_PROVIDERS = {
    "Gmail": ("smtp.gmail.com", "587"),
    "Outlook / Hotmail": ("smtp.office365.com", "587"),
    "Yahoo": ("smtp.mail.yahoo.com", "587"),
    "Otro (manual)": ("", ""),
}

BUTTON_STYLE_SECONDARY = """
    QPushButton {
        background-color: white;
        color: #4A6A92;
        border: 2px solid #4A6A92;
        border-radius: 12px;
        font-size: 15px;
        font-weight: bold;
        padding: 10px;
    }
    QPushButton:hover {
        background-color: #EFF6FF;
    }
"""


def get_installed_printers():
    system = platform.system()
    try:
        if system in ("Darwin", "Linux"):
            result = subprocess.run(["lpstat", "-a"], capture_output=True, text=True)
            printers = []
            for line in result.stdout.splitlines():
                if line.strip():
                    printers.append(line.split()[0])
            return printers if printers else ["Sin impresoras detectadas"]
        elif system == "Windows":
            import winreg
            printers = []
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                "SYSTEM\\CurrentControlSet\\Control\\Print\\Printers")
            for i in range(winreg.QueryInfoKey(key)[0]):
                printers.append(winreg.EnumKey(key, i))
            return printers if printers else ["Sin impresoras detectadas"]
    except Exception:
        return ["Sin impresoras detectadas"]


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def get_db_path():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    return os.path.join(base, "database.db")


class SettingsPage(QWidget):

    def __init__(self):
        super().__init__()
        self.selected_user_id = None

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Configuración")
        title.setStyleSheet(f"font-size: 34px; font-weight: bold; color: {PRIMARY_COLOR};")
        main_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(12)

        # ── Licencia ──────────────────────────────────
        license_widget = QWidget()
        license_layout = QVBoxLayout()
        license_layout.setContentsMargins(16, 16, 16, 16)
        license_layout.setSpacing(14)

        # Estado actual
        plan_info = get_current_plan()
        if plan_info["plan"] == "SARA+":
            status_color = "#DCFCE7"
            status_border = "#86EFAC"
            status_text_color = "#166534"
            status_icon = "✅"
        else:
            status_color = "#FEF3C7"
            status_border = "#F59E0B"
            status_text_color = "#92400E"
            status_icon = "⚠️"

        self.license_status_label = QLabel(f"{status_icon}  {plan_info['message']}")
        self.license_status_label.setStyleSheet(
            f"font-size: 13px; color: {status_text_color}; background-color: {status_color}; "
            f"border-radius: 8px; padding: 12px; border: 1px solid {status_border};"
        )
        self.license_status_label.setWordWrap(True)
        license_layout.addWidget(self.license_status_label)

        # Campo de clave
        key_label = QLabel("Clave de licencia SARA+:")
        key_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        license_layout.addWidget(key_label)

        self.license_key_input = self.create_input("SARA-XXXX-XXXX-XXXX-XXXX-XXXX")
        current_key = load_license()
        if current_key:
            self.license_key_input.setText(current_key)
        license_layout.addWidget(self.license_key_input)

        key_hint = QLabel("💡 Ingresá la clave que recibiste al adquirir SARA+. Al vencer, el sistema opera automáticamente en modo FREE.")
        key_hint.setStyleSheet("font-size: 12px; color: #94A3B8; background: transparent;")
        key_hint.setWordWrap(True)
        license_layout.addWidget(key_hint)

        license_btn_row = QHBoxLayout()
        license_btn_row.setSpacing(12)

        btn_activate = QPushButton("Activar licencia")
        btn_activate.setMinimumHeight(48)
        btn_activate.setStyleSheet(BUTTON_STYLE)
        btn_activate.clicked.connect(self.activate_license)

        btn_remove_license = QPushButton("Eliminar clave")
        btn_remove_license.setMinimumHeight(48)
        btn_remove_license.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #DC2626;
                border: 2px solid #DC2626;
                border-radius: 12px;
                font-size: 15px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover { background-color: #FEF2F2; }
        """)
        btn_remove_license.clicked.connect(self.remove_license)

        license_btn_row.addWidget(btn_activate)
        license_btn_row.addWidget(btn_remove_license)
        license_layout.addLayout(license_btn_row)

        # Límites del plan activo
        sep_lic = QFrame()
        sep_lic.setFrameShape(QFrame.HLine)
        sep_lic.setStyleSheet("color: #E2E8F0; margin: 4px 0;")
        license_layout.addWidget(sep_lic)

        limits_title = QLabel("Límites del plan activo:")
        limits_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #1E293B; background: transparent;")
        license_layout.addWidget(limits_title)

        self.license_limits_label = QLabel()
        self.license_limits_label.setStyleSheet("font-size: 12px; color: #64748B; background: transparent;")
        self.license_limits_label.setWordWrap(True)
        license_layout.addWidget(self.license_limits_label)
        self._update_license_limits_label()

        license_widget.setLayout(license_layout)
        content_layout.addWidget(CollapsibleSection("Licencia", license_widget))

        # ── Negocio ───────────────────────────────────
        business_widget = QWidget()
        business_layout = QVBoxLayout()
        business_layout.setContentsMargins(16, 16, 16, 16)
        business_layout.setSpacing(12)

        self.business_name_input = self.create_input("Nombre negocio")
        business_layout.addWidget(self.business_name_input)
        self.business_cuit_input = self.create_input("CUIT/CUIL")
        business_layout.addWidget(self.business_cuit_input)
        self.business_address_input = self.create_input("Dirección")
        business_layout.addWidget(self.business_address_input)
        self.business_phone_input = self.create_input("Teléfono")
        business_layout.addWidget(self.business_phone_input)
        self.ticket_legend_input = self.create_input("Leyenda ticket (ej: Comprobante no válido como factura)")
        business_layout.addWidget(self.ticket_legend_input)
        self.ticket_footer_input = self.create_input("Pie ticket (ej: Gracias por su compra)")
        business_layout.addWidget(self.ticket_footer_input)

        btn_save_business = QPushButton("Guardar datos del negocio")
        btn_save_business.setMinimumHeight(48)
        btn_save_business.setStyleSheet(BUTTON_STYLE)
        btn_save_business.clicked.connect(self.save_business)
        business_layout.addWidget(btn_save_business)

        business_widget.setLayout(business_layout)
        content_layout.addWidget(CollapsibleSection("Negocio", business_widget))

        # ── Impresora ─────────────────────────────────
        printer_widget = QWidget()
        printer_layout = QVBoxLayout()
        printer_layout.setContentsMargins(16, 16, 16, 16)
        printer_layout.setSpacing(12)

        printer_label = QLabel("Impresora instalada en el sistema:")
        printer_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        printer_layout.addWidget(printer_label)

        self.printer_combo = QComboBox()
        self.printer_combo.setMinimumHeight(50)
        self.printer_combo.setStyleSheet(self.combo_style())
        self.printer_combo.addItems(get_installed_printers())
        printer_layout.addWidget(self.printer_combo)

        btn_refresh = QPushButton("Actualizar lista de impresoras")
        btn_refresh.setMinimumHeight(44)
        btn_refresh.setStyleSheet(BUTTON_STYLE)
        btn_refresh.clicked.connect(self.refresh_printers)
        printer_layout.addWidget(btn_refresh)

        size_label = QLabel("Tamaño del papel:")
        size_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        printer_layout.addWidget(size_label)

        self.printer_size_combo = QComboBox()
        self.printer_size_combo.addItems(["80mm", "58mm"])
        self.printer_size_combo.setMinimumHeight(50)
        self.printer_size_combo.setStyleSheet(self.combo_style())
        printer_layout.addWidget(self.printer_size_combo)

        btn_save_printer = QPushButton("Guardar configuración de impresora")
        btn_save_printer.setMinimumHeight(48)
        btn_save_printer.setStyleSheet(BUTTON_STYLE)
        btn_save_printer.clicked.connect(self.save_printer)
        printer_layout.addWidget(btn_save_printer)

        printer_widget.setLayout(printer_layout)
        content_layout.addWidget(CollapsibleSection("Impresora", printer_widget))

        # ── Métodos de pago ───────────────────────────
        payment_widget = QWidget()
        payment_layout = QVBoxLayout()
        payment_layout.setContentsMargins(16, 16, 16, 16)
        payment_layout.setSpacing(12)

        self.mp_alias_input = self.create_input("Alias MercadoPago")
        payment_layout.addWidget(self.mp_alias_input)

        self.qr_path_label = QLabel("QR no configurado")
        self.qr_path_label.setStyleSheet("color: #64748B; font-size: 14px;")
        payment_layout.addWidget(self.qr_path_label)

        qr_button = QPushButton("Seleccionar QR")
        qr_button.setMinimumHeight(48)
        qr_button.setStyleSheet(BUTTON_STYLE)
        qr_button.clicked.connect(self.select_qr)
        payment_layout.addWidget(qr_button)

        btn_save_payment = QPushButton("Guardar métodos de pago")
        btn_save_payment.setMinimumHeight(48)
        btn_save_payment.setStyleSheet(BUTTON_STYLE)
        btn_save_payment.clicked.connect(self.save_payment)
        payment_layout.addWidget(btn_save_payment)

        payment_widget.setLayout(payment_layout)
        content_layout.addWidget(CollapsibleSection("Métodos de pago", payment_widget))

        # ── Email ─────────────────────────────────────
        smtp_widget = QWidget()
        smtp_layout = QVBoxLayout()
        smtp_layout.setContentsMargins(16, 16, 16, 16)
        smtp_layout.setSpacing(12)

        provider_label = QLabel("Proveedor de email:")
        provider_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        smtp_layout.addWidget(provider_label)

        self.smtp_provider_combo = QComboBox()
        self.smtp_provider_combo.addItems(list(SMTP_PROVIDERS.keys()))
        self.smtp_provider_combo.setMinimumHeight(50)
        self.smtp_provider_combo.setStyleSheet(self.combo_style())
        self.smtp_provider_combo.currentTextChanged.connect(self.on_provider_changed)
        smtp_layout.addWidget(self.smtp_provider_combo)

        self.smtp_email_input = self.create_input("Tu email")
        smtp_layout.addWidget(self.smtp_email_input)

        self.smtp_password_input = self.create_input("Contraseña / Contraseña de app")
        self.smtp_password_input.setEchoMode(QLineEdit.Password)
        smtp_layout.addWidget(self.smtp_password_input)

        self.smtp_manual_frame = QFrame()
        self.smtp_manual_frame.setStyleSheet("background: transparent;")
        manual_layout = QVBoxLayout(self.smtp_manual_frame)
        manual_layout.setContentsMargins(0, 0, 0, 0)
        manual_layout.setSpacing(10)
        self.smtp_host_input = self.create_input("Servidor SMTP")
        manual_layout.addWidget(self.smtp_host_input)
        self.smtp_port_input = self.create_input("Puerto (ej: 587)")
        manual_layout.addWidget(self.smtp_port_input)
        self.smtp_manual_frame.hide()
        smtp_layout.addWidget(self.smtp_manual_frame)

        hint = QLabel("💡 Para Gmail usá una Contraseña de App (no tu contraseña normal).")
        hint.setStyleSheet("font-size: 12px; color: #94A3B8; background: transparent;")
        hint.setWordWrap(True)
        smtp_layout.addWidget(hint)

        btn_help_gmail = QPushButton("❓  ¿Cómo genero la Contraseña de App en Gmail?")
        btn_help_gmail.setMinimumHeight(40)
        btn_help_gmail.setStyleSheet("""
            QPushButton {
                background-color: #EFF6FF;
                color: #4A6A92;
                border: 1px solid #BFDBFE;
                border-radius: 10px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 14px;
            }
            QPushButton:hover { background-color: #DBEAFE; }
        """)
        btn_help_gmail.clicked.connect(self.show_gmail_help)
        smtp_layout.addWidget(btn_help_gmail)

        btn_save_smtp = QPushButton("Guardar configuración de email")
        btn_save_smtp.setMinimumHeight(48)
        btn_save_smtp.setStyleSheet(BUTTON_STYLE)
        btn_save_smtp.clicked.connect(self.save_smtp)
        smtp_layout.addWidget(btn_save_smtp)

        smtp_widget.setLayout(smtp_layout)
        if is_feature_allowed("email"):
            content_layout.addWidget(CollapsibleSection("Email", smtp_widget))

        # ── Backup ────────────────────────────────────
        backup_widget = QWidget()
        backup_layout = QVBoxLayout()
        backup_layout.setContentsMargins(16, 16, 16, 16)
        backup_layout.setSpacing(12)

        manual_backup_label = QLabel("Backup manual")
        manual_backup_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E293B; background: transparent;")
        backup_layout.addWidget(manual_backup_label)

        manual_backup_desc = QLabel("Guardá una copia de seguridad de la base de datos en la carpeta que elijas.")
        manual_backup_desc.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        manual_backup_desc.setWordWrap(True)
        backup_layout.addWidget(manual_backup_desc)

        btn_manual_backup = QPushButton("Hacer backup ahora")
        btn_manual_backup.setMinimumHeight(48)
        btn_manual_backup.setStyleSheet(BUTTON_STYLE)
        btn_manual_backup.clicked.connect(self.do_manual_backup)
        backup_layout.addWidget(btn_manual_backup)

        btn_restore_backup = QPushButton("Restaurar backup")
        btn_restore_backup.setMinimumHeight(48)
        btn_restore_backup.setStyleSheet(BUTTON_STYLE_SECONDARY)
        btn_restore_backup.clicked.connect(self.do_restore_backup)
        backup_layout.addWidget(btn_restore_backup)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #E2E8F0; margin: 8px 0;")
        backup_layout.addWidget(sep)

        auto_backup_label = QLabel("Backup automático")
        auto_backup_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E293B; background: transparent;")
        backup_layout.addWidget(auto_backup_label)

        auto_row = QHBoxLayout()
        auto_row.setSpacing(12)

        self.auto_backup_check = QCheckBox("Activar backup automático")
        self.auto_backup_check.setStyleSheet("font-size: 14px; color: #1E293B; background: transparent;")
        auto_row.addWidget(self.auto_backup_check)

        freq_label = QLabel("cada")
        freq_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        auto_row.addWidget(freq_label)

        self.backup_freq_spin = QSpinBox()
        self.backup_freq_spin.setMinimum(1)
        self.backup_freq_spin.setMaximum(30)
        self.backup_freq_spin.setValue(7)
        self.backup_freq_spin.setMinimumHeight(44)
        self.backup_freq_spin.setStyleSheet("""
            QSpinBox {
                background-color: white;
                border: 2px solid #B8C4D0;
                border-radius: 12px;
                padding: 8px 14px;
                font-size: 14px;
                color: #1E293B;
                min-width: 80px;
            }
        """)
        auto_row.addWidget(self.backup_freq_spin)

        days_label = QLabel("días")
        days_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        auto_row.addWidget(days_label)
        auto_row.addStretch()
        backup_layout.addLayout(auto_row)

        folder_row = QHBoxLayout()
        folder_row.setSpacing(12)

        self.backup_folder_label = QLabel("Carpeta: no configurada")
        self.backup_folder_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")

        btn_select_folder = QPushButton("Seleccionar carpeta")
        btn_select_folder.setFixedHeight(44)
        btn_select_folder.setStyleSheet(BUTTON_STYLE)
        btn_select_folder.clicked.connect(self.select_backup_folder)

        folder_row.addWidget(self.backup_folder_label, 3)
        folder_row.addWidget(btn_select_folder)
        backup_layout.addLayout(folder_row)

        self.last_backup_label = QLabel("Último backup: nunca")
        self.last_backup_label.setStyleSheet("font-size: 12px; color: #94A3B8; background: transparent;")
        backup_layout.addWidget(self.last_backup_label)

        btn_save_backup = QPushButton("Guardar configuración de backup")
        btn_save_backup.setMinimumHeight(48)
        btn_save_backup.setStyleSheet(BUTTON_STYLE)
        btn_save_backup.clicked.connect(self.save_backup_config)
        backup_layout.addWidget(btn_save_backup)

        backup_widget.setLayout(backup_layout)
        if is_feature_allowed("backup"):
            content_layout.addWidget(CollapsibleSection("Backup", backup_widget))

        # ── Factura Electrónica ARCA ──────────────────
        arca_widget = QWidget()
        arca_layout = QVBoxLayout()
        arca_layout.setContentsMargins(16, 16, 16, 16)
        arca_layout.setSpacing(14)

        # Aviso informativo
        arca_info = QLabel(
            "⚠️  Esta sección es para configurar la integración con ARCA (ex-AFIP). "
            "Requiere certificado digital, punto de venta habilitado y CUIT activo con Clave Fiscal nivel 3. "
            "Dejá todo configurado aquí para cuando estés listo para activarlo."
        )
        arca_info.setStyleSheet(
            "font-size: 12px; color: #92400E; background-color: #FEF3C7; "
            "border-radius: 8px; padding: 10px; border: 1px solid #F59E0B;"
        )
        arca_info.setWordWrap(True)
        arca_layout.addWidget(arca_info)

        # Activar módulo
        self.arca_enabled_check = QCheckBox("Activar facturación electrónica ARCA")
        self.arca_enabled_check.setStyleSheet("font-size: 14px; color: #1E293B; background: transparent; font-weight: bold;")
        arca_layout.addWidget(self.arca_enabled_check)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("color: #E2E8F0; margin: 4px 0;")
        arca_layout.addWidget(sep1)

        # ── Datos del emisor
        arca_emisor_label = QLabel("Datos del emisor")
        arca_emisor_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B; background: transparent;")
        arca_layout.addWidget(arca_emisor_label)

        self.arca_cuit_input = self.create_input("CUIT del emisor (sin guiones, ej: 20123456789)")
        arca_layout.addWidget(self.arca_cuit_input)

        cond_iva_label = QLabel("Condición IVA del emisor:")
        cond_iva_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        arca_layout.addWidget(cond_iva_label)

        self.arca_cond_iva_emisor_combo = QComboBox()
        self.arca_cond_iva_emisor_combo.addItems([
            "Responsable Inscripto",
            "Monotributista",
            "Exento",
        ])
        self.arca_cond_iva_emisor_combo.setMinimumHeight(50)
        self.arca_cond_iva_emisor_combo.setStyleSheet(self.combo_style())
        arca_layout.addWidget(self.arca_cond_iva_emisor_combo)

        pdv_row = QHBoxLayout()
        pdv_row.setSpacing(12)
        pdv_label = QLabel("Punto de venta N°:")
        pdv_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        self.arca_pdv_spin = QSpinBox()
        self.arca_pdv_spin.setMinimum(1)
        self.arca_pdv_spin.setMaximum(9999)
        self.arca_pdv_spin.setValue(1)
        self.arca_pdv_spin.setMinimumHeight(50)
        self.arca_pdv_spin.setMinimumWidth(120)
        self.arca_pdv_spin.setStyleSheet("""
            QSpinBox {
                background-color: white;
                border: 2px solid #B8C4D0;
                border-radius: 12px;
                padding: 8px 14px;
                font-size: 14px;
                color: #1E293B;
            }
        """)
        pdv_row.addWidget(pdv_label)
        pdv_row.addWidget(self.arca_pdv_spin)
        pdv_row.addStretch()
        arca_layout.addLayout(pdv_row)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #E2E8F0; margin: 4px 0;")
        arca_layout.addWidget(sep2)

        # ── Certificado digital
        arca_cert_label = QLabel("Certificado digital")
        arca_cert_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B; background: transparent;")
        arca_layout.addWidget(arca_cert_label)

        cert_hint = QLabel("Generá el certificado desde el portal de ARCA → Administración de Certificados Digitales.")
        cert_hint.setStyleSheet("font-size: 12px; color: #94A3B8; background: transparent;")
        cert_hint.setWordWrap(True)
        arca_layout.addWidget(cert_hint)

        # Archivo .crt
        crt_row = QHBoxLayout()
        crt_row.setSpacing(12)
        self.arca_crt_label = QLabel("Certificado (.crt): no cargado")
        self.arca_crt_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        btn_select_crt = QPushButton("Cargar .crt")
        btn_select_crt.setFixedHeight(44)
        btn_select_crt.setStyleSheet(BUTTON_STYLE)
        btn_select_crt.clicked.connect(self.select_arca_crt)
        crt_row.addWidget(self.arca_crt_label, 3)
        crt_row.addWidget(btn_select_crt)
        arca_layout.addLayout(crt_row)

        # Archivo .key
        key_row = QHBoxLayout()
        key_row.setSpacing(12)
        self.arca_key_label = QLabel("Clave privada (.key): no cargada")
        self.arca_key_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        btn_select_key = QPushButton("Cargar .key")
        btn_select_key.setFixedHeight(44)
        btn_select_key.setStyleSheet(BUTTON_STYLE)
        btn_select_key.clicked.connect(self.select_arca_key)
        key_row.addWidget(self.arca_key_label, 3)
        key_row.addWidget(btn_select_key)
        arca_layout.addLayout(key_row)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        sep3.setStyleSheet("color: #E2E8F0; margin: 4px 0;")
        arca_layout.addWidget(sep3)

        # ── Configuración fiscal
        arca_fiscal_label = QLabel("Configuración fiscal")
        arca_fiscal_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B; background: transparent;")
        arca_layout.addWidget(arca_fiscal_label)

        iva_default_label = QLabel("Alícuota IVA por defecto:")
        iva_default_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        arca_layout.addWidget(iva_default_label)

        self.arca_iva_combo = QComboBox()
        self.arca_iva_combo.addItems(["21%", "10.5%", "0%", "Exento"])
        self.arca_iva_combo.setMinimumHeight(50)
        self.arca_iva_combo.setStyleSheet(self.combo_style())
        arca_layout.addWidget(self.arca_iva_combo)

        cond_cliente_label = QLabel("Condición IVA del cliente por defecto:")
        cond_cliente_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        arca_layout.addWidget(cond_cliente_label)

        self.arca_cond_iva_cliente_combo = QComboBox()
        self.arca_cond_iva_cliente_combo.addItems([
            "Consumidor Final",
            "Responsable Inscripto",
            "Monotributista",
            "Exento",
        ])
        self.arca_cond_iva_cliente_combo.setMinimumHeight(50)
        self.arca_cond_iva_cliente_combo.setStyleSheet(self.combo_style())
        arca_layout.addWidget(self.arca_cond_iva_cliente_combo)

        umbral_row = QHBoxLayout()
        umbral_row.setSpacing(12)
        umbral_label = QLabel("Umbral identificación cliente ($ monto):")
        umbral_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        umbral_label.setWordWrap(True)
        self.arca_umbral_input = self.create_input("10000000")
        self.arca_umbral_input.setMaximumWidth(200)
        umbral_row.addWidget(umbral_label, 2)
        umbral_row.addWidget(self.arca_umbral_input, 1)
        arca_layout.addLayout(umbral_row)

        umbral_hint = QLabel(
            "💡 Desde julio 2026, operaciones superiores a este monto requieren CUIT/CUIL del cliente obligatoriamente (RG 5824/2026)."
        )
        umbral_hint.setStyleSheet("font-size: 12px; color: #94A3B8; background: transparent;")
        umbral_hint.setWordWrap(True)
        arca_layout.addWidget(umbral_hint)

        sep4 = QFrame()
        sep4.setFrameShape(QFrame.HLine)
        sep4.setStyleSheet("color: #E2E8F0; margin: 4px 0;")
        arca_layout.addWidget(sep4)

        # ── Numeración de comprobantes
        arca_num_label = QLabel("Numeración de comprobantes")
        arca_num_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B; background: transparent;")
        arca_layout.addWidget(arca_num_label)

        num_hint = QLabel("Se actualiza automáticamente con cada factura emitida. No modificar salvo que sea necesario sincronizar con ARCA.")
        num_hint.setStyleSheet("font-size: 12px; color: #94A3B8; background: transparent;")
        num_hint.setWordWrap(True)
        arca_layout.addWidget(num_hint)

        num_row = QHBoxLayout()
        num_row.setSpacing(16)

        for label_text, attr_name in [
            ("Último N° Factura A:", "arca_num_a_spin"),
            ("Último N° Factura B:", "arca_num_b_spin"),
            ("Último N° Factura C:", "arca_num_c_spin"),
        ]:
            col = QVBoxLayout()
            col.setSpacing(6)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 12px; color: #64748B; background: transparent;")
            spin = QSpinBox()
            spin.setMinimum(0)
            spin.setMaximum(9999999)
            spin.setValue(0)
            spin.setMinimumHeight(50)
            spin.setStyleSheet("""
                QSpinBox {
                    background-color: white;
                    border: 2px solid #B8C4D0;
                    border-radius: 12px;
                    padding: 8px 14px;
                    font-size: 14px;
                    color: #1E293B;
                }
            """)
            setattr(self, attr_name, spin)
            col.addWidget(lbl)
            col.addWidget(spin)
            num_row.addLayout(col)

        arca_layout.addLayout(num_row)

        sep5 = QFrame()
        sep5.setFrameShape(QFrame.HLine)
        sep5.setStyleSheet("color: #E2E8F0; margin: 4px 0;")
        arca_layout.addWidget(sep5)

        # ── Ambiente
        arca_env_label = QLabel("Ambiente")
        arca_env_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B; background: transparent;")
        arca_layout.addWidget(arca_env_label)

        env_label = QLabel("Entorno de conexión con ARCA:")
        env_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        arca_layout.addWidget(env_label)

        self.arca_ambiente_combo = QComboBox()
        self.arca_ambiente_combo.addItems(["Homologación (pruebas)", "Producción"])
        self.arca_ambiente_combo.setMinimumHeight(50)
        self.arca_ambiente_combo.setStyleSheet(self.combo_style())
        arca_layout.addWidget(self.arca_ambiente_combo)

        sep6 = QFrame()
        sep6.setFrameShape(QFrame.HLine)
        sep6.setStyleSheet("color: #E2E8F0; margin: 4px 0;")
        arca_layout.addWidget(sep6)

        # ── Entrega de factura
        arca_entrega_label = QLabel("Entrega de factura al cliente")
        arca_entrega_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B; background: transparent;")
        arca_layout.addWidget(arca_entrega_label)

        entrega_label = QLabel("¿Cómo se entrega la factura electrónica al cliente?")
        entrega_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        arca_layout.addWidget(entrega_label)

        self.arca_entrega_combo = QComboBox()
        self.arca_entrega_combo.addItems(["Impresa (impresora térmica)", "Por email"])
        self.arca_entrega_combo.setMinimumHeight(50)
        self.arca_entrega_combo.setStyleSheet(self.combo_style())
        arca_layout.addWidget(self.arca_entrega_combo)

        # Botón guardar
        btn_save_arca = QPushButton("Guardar configuración ARCA")
        btn_save_arca.setMinimumHeight(48)
        btn_save_arca.setStyleSheet(BUTTON_STYLE)
        btn_save_arca.clicked.connect(self.save_arca_config)
        arca_layout.addWidget(btn_save_arca)

        arca_widget.setLayout(arca_layout)
        if is_feature_allowed("arca"):
            content_layout.addWidget(CollapsibleSection("Factura Electrónica ARCA", arca_widget))

        # ── Base de datos / Red ───────────────────────
        db_widget = QWidget()
        db_layout = QVBoxLayout()
        db_layout.setContentsMargins(16, 16, 16, 16)
        db_layout.setSpacing(14)

        # Aviso
        db_info = QLabel(
            "⚙️  Por defecto SARA usa SQLite (base de datos local). "
            "Activá PostgreSQL para conectar múltiples PCs en red local (SARA+)."
        )
        db_info.setStyleSheet(
            "font-size: 12px; color: #1E3A5F; background-color: #DBEAFE; "
            "border-radius: 8px; padding: 10px; border: 1px solid #93C5FD;"
        )
        db_info.setWordWrap(True)
        db_layout.addWidget(db_info)

        # Modo
        mode_label = QLabel("Modo de base de datos:")
        mode_label.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        db_layout.addWidget(mode_label)

        self.db_mode_combo = QComboBox()
        self.db_mode_combo.addItems(["SQLite (local, 1 PC)", "PostgreSQL (red, múltiples PCs)"])
        self.db_mode_combo.setMinimumHeight(50)
        self.db_mode_combo.setStyleSheet(self.combo_style())
        self.db_mode_combo.currentIndexChanged.connect(self.on_db_mode_changed)
        db_layout.addWidget(self.db_mode_combo)

        # Frame campos PostgreSQL (se oculta si modo SQLite)
        self.pg_frame = QFrame()
        self.pg_frame.setStyleSheet("background: transparent;")
        pg_layout = QVBoxLayout(self.pg_frame)
        pg_layout.setContentsMargins(0, 0, 0, 0)
        pg_layout.setSpacing(10)

        sep_pg = QFrame()
        sep_pg.setFrameShape(QFrame.HLine)
        sep_pg.setStyleSheet("color: #E2E8F0; margin: 4px 0;")
        pg_layout.addWidget(sep_pg)

        pg_title = QLabel("Datos de conexión PostgreSQL")
        pg_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B; background: transparent;")
        pg_layout.addWidget(pg_title)

        pg_hint = QLabel(
            "Instalá PostgreSQL en la PC servidor y creá una base de datos y usuario para SARA+. "
            "Todas las PCs deben estar en la misma red local."
        )
        pg_hint.setStyleSheet("font-size: 12px; color: #94A3B8; background: transparent;")
        pg_hint.setWordWrap(True)
        pg_layout.addWidget(pg_hint)

        host_row = QHBoxLayout()
        host_row.setSpacing(12)
        self.pg_host_input = self.create_input("IP del servidor (ej: 192.168.1.100)")
        self.pg_port_input = self.create_input("Puerto (5432)")
        self.pg_port_input.setMaximumWidth(120)
        host_row.addWidget(self.pg_host_input, 3)
        host_row.addWidget(self.pg_port_input, 1)
        pg_layout.addLayout(host_row)

        self.pg_database_input = self.create_input("Nombre de la base de datos (ej: sara_pos)")
        pg_layout.addWidget(self.pg_database_input)

        creds_row = QHBoxLayout()
        creds_row.setSpacing(12)
        self.pg_user_input = self.create_input("Usuario PostgreSQL (ej: sara)")
        self.pg_password_input = self.create_input("Contraseña")
        self.pg_password_input.setEchoMode(QLineEdit.Password)
        creds_row.addWidget(self.pg_user_input)
        creds_row.addWidget(self.pg_password_input)
        pg_layout.addLayout(creds_row)

        # Botón probar conexión
        btn_test_db = QPushButton("🔌 Probar conexión")
        btn_test_db.setMinimumHeight(48)
        btn_test_db.setStyleSheet(BUTTON_STYLE_SECONDARY)
        btn_test_db.clicked.connect(self.test_db_connection)
        pg_layout.addWidget(btn_test_db)

        self.pg_frame.setLayout(pg_layout)
        db_layout.addWidget(self.pg_frame)

        # Botón guardar
        btn_save_db = QPushButton("Guardar configuración de base de datos")
        btn_save_db.setMinimumHeight(48)
        btn_save_db.setStyleSheet(BUTTON_STYLE)
        btn_save_db.clicked.connect(self.save_db_config)
        db_layout.addWidget(btn_save_db)

        db_widget.setLayout(db_layout)
        if is_feature_allowed("postgresql"):
            content_layout.addWidget(CollapsibleSection("Base de datos / Red", db_widget))

        # ── ABM Usuarios ──────────────────────────────
        users_widget = QWidget()
        users_layout = QVBoxLayout()
        users_layout.setContentsMargins(16, 16, 16, 16)
        users_layout.setSpacing(12)

        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: #F8FAFC; border-radius: 12px;")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(16, 16, 16, 16)
        form_layout.setSpacing(10)

        row1 = QHBoxLayout()
        self.user_username_input = self.create_input("Usuario *")
        self.user_password_input = self.create_input("Contraseña *")
        self.user_password_input.setEchoMode(QLineEdit.Password)
        row1.addWidget(self.user_username_input)
        row1.addWidget(self.user_password_input)
        form_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(10)

        self.user_role_combo = QComboBox()
        self.user_role_combo.addItems(["ADMIN", "ANALISTA"])
        self.user_role_combo.setMinimumHeight(50)
        self.user_role_combo.setStyleSheet(self.combo_style())

        BLUE = "QPushButton { background-color: #4A6A92; color: white; border: none; border-radius: 12px; font-size: 14px; font-weight: bold; padding: 12px; } QPushButton:hover { background-color: #3D5A80; }"
        RED_BTN = "QPushButton { background-color: #FF003D; color: white; border: none; border-radius: 12px; font-size: 14px; font-weight: bold; padding: 12px; } QPushButton:hover { background-color: #D90429; }"

        btn_save_user = QPushButton("Crear")
        btn_save_user.setMinimumHeight(50)
        btn_save_user.setStyleSheet(BLUE)
        btn_save_user.clicked.connect(self.save_user)

        btn_update_user = QPushButton("Actualizar")
        btn_update_user.setMinimumHeight(50)
        btn_update_user.setStyleSheet(BLUE)
        btn_update_user.clicked.connect(self.update_user)

        btn_toggle_user = QPushButton("Activar / Desactivar")
        btn_toggle_user.setMinimumHeight(50)
        btn_toggle_user.setStyleSheet(RED_BTN)
        btn_toggle_user.clicked.connect(self.toggle_user)

        btn_clear_user = QPushButton("Limpiar")
        btn_clear_user.setMinimumHeight(50)
        btn_clear_user.setStyleSheet(BLUE)
        btn_clear_user.clicked.connect(self.clear_user_form)

        row2.addWidget(self.user_role_combo)
        row2.addWidget(btn_save_user)
        row2.addWidget(btn_update_user)
        row2.addWidget(btn_toggle_user)
        row2.addWidget(btn_clear_user)
        form_layout.addLayout(row2)

        users_layout.addWidget(form_frame)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["ID", "Usuario", "Rol", "Estado"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_table.verticalHeader().setVisible(False)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.users_table.setMinimumHeight(200)
        self.users_table.setStyleSheet("""
            QTableWidget { background-color: white; border-radius: 12px; font-size: 14px; color: #1E293B; border: none; }
            QHeaderView::section { background-color: #4A6A92; color: white; padding: 10px; border: none; font-weight: bold; }
            QTableWidget::item { padding: 10px; }
            QTableWidget::item:selected { background-color: #DBEAFE; color: #1E293B; }
        """)
        self.users_table.cellClicked.connect(self.select_user)
        users_layout.addWidget(self.users_table)

        users_widget.setLayout(users_layout)
        content_layout.addWidget(CollapsibleSection("ABM Usuarios", users_widget))

        # ── Acerca de ─────────────────────────────────
        about_widget = QWidget()
        about_layout = QVBoxLayout()
        about_layout.setContentsMargins(16, 16, 16, 16)
        about_layout.setSpacing(12)

        # Logo / nombre
        about_title = QLabel("SARA POS")
        about_title.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {PRIMARY_COLOR}; background: transparent;")
        about_title.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(about_title)

        about_version = QLabel("Versión 1.0")
        about_version.setStyleSheet("font-size: 13px; color: #64748B; background: transparent;")
        about_version.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(about_version)

        about_sep = QFrame()
        about_sep.setFrameShape(QFrame.HLine)
        about_sep.setStyleSheet("color: #E2E8F0; margin: 4px 0;")
        about_layout.addWidget(about_sep)

        # Empresa
        about_company = QLabel("Desarrollado por BIMABA™")
        about_company.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B; background: transparent;")
        about_company.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(about_company)

        about_copyright = QLabel("© 2026 BIMABA™. Todos los derechos reservados.")
        about_copyright.setStyleSheet("font-size: 12px; color: #64748B; background: transparent;")
        about_copyright.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(about_copyright)

        about_sep2 = QFrame()
        about_sep2.setFrameShape(QFrame.HLine)
        about_sep2.setStyleSheet("color: #E2E8F0; margin: 4px 0;")
        about_layout.addWidget(about_sep2)

        # Contacto
        about_contact_title = QLabel("Soporte y contacto")
        about_contact_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #1E293B; background: transparent;")
        about_contact_title.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(about_contact_title)

        about_email = QLabel("✉  soportesara@bimaba.com")
        about_email.setStyleSheet("font-size: 13px; color: #4A6A92; background: transparent;")
        about_email.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(about_email)

        about_web = QLabel("🌐  www.bimaba.com")
        about_web.setStyleSheet("font-size: 13px; color: #4A6A92; background: transparent;")
        about_web.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(about_web)

        about_widget.setLayout(about_layout)
        content_layout.addWidget(CollapsibleSection("Acerca de", about_widget))

        content_layout.addStretch()
        content.setLayout(content_layout)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

        self.load_settings()
        self.load_users()
        self.check_auto_backup()

    # ── Licencia ──────────────────────────────────────

    def remove_license(self):
        reply = QMessageBox(self)
        reply.setWindowTitle("Eliminar licencia")
        reply.setText(
            "¿Estás seguro que querés eliminar la clave de licencia?\n\n"
            "El sistema volverá a operar en modo FREE."
        )
        reply.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        reply.setDefaultButton(QMessageBox.No)
        reply.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1E293B; font-size: 14px; min-width: 350px; }
            QPushButton {
                background-color: #4A6A92; color: white; border: none;
                border-radius: 10px; padding: 10px 20px; min-width: 80px;
                min-height: 32px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #3D5A80; }
        """)
        if reply.exec() != QMessageBox.Yes:
            return

        from app.utils.license_manager import _get_license_path
        import os
        path = _get_license_path()
        try:
            if os.path.exists(path):
                os.remove(path)
            self.license_key_input.clear()
            self.license_status_label.setStyleSheet(
                "font-size: 13px; color: #92400E; background-color: #FEF3C7; "
                "border-radius: 8px; padding: 12px; border: 1px solid #F59E0B;"
            )
            self.license_status_label.setText("⚠️  Sin licencia activa. Operando en modo FREE.")
            self._update_license_limits_label()
            self.show_message("OK", "Licencia eliminada. El sistema opera en modo FREE.")
        except Exception as e:
            self.show_message("Error", f"Error al eliminar la licencia:\n{str(e)}")

    def activate_license(self):
        key = self.license_key_input.text().strip()
        if not key:
            self.show_message("Error", "Ingresá una clave de licencia")
            return

        result = validate_license(key)

        if result["valid"]:
            save_license(key)
            self.license_status_label.setStyleSheet(
                "font-size: 13px; color: #166534; background-color: #DCFCE7; "
                "border-radius: 8px; padding: 12px; border: 1px solid #86EFAC;"
            )
            self.license_status_label.setText(f"✅  {result['message']}")
            self._update_license_limits_label()
            self.show_message("✅ Licencia activada", result["message"])
        else:
            # Clave inválida o vencida — guardar igual para mostrar el estado
            save_license(key)
            self.license_status_label.setStyleSheet(
                "font-size: 13px; color: #92400E; background-color: #FEF3C7; "
                "border-radius: 8px; padding: 12px; border: 1px solid #F59E0B;"
            )
            self.license_status_label.setText(f"⚠️  {result['message']}")
            self._update_license_limits_label()
            self.show_message("Licencia no válida", result["message"])

    def _update_license_limits_label(self):
        limits = get_plan_limits()
        plan = get_current_plan()["plan"]

        productos = "Ilimitados" if limits["max_products"] is None else f"Hasta {limits['max_products']}"
        clientes  = "Ilimitados" if limits["max_clients"]  is None else f"Hasta {limits['max_clients']}"
        usuarios  = "Ilimitados" if limits["max_users"]    is None else f"Hasta {limits['max_users']} (admin + 1 adicional)" if limits["max_users"] == 2 else str(limits["max_users"])

        def si_no(val):
            return "✅  Incluido" if val else "❌  No disponible en este plan"

        if plan == "SARA+":
            header = "✅  Plan SARA+ activo"
            header_style = "font-size: 14px; font-weight: bold; color: #16A34A;"
        else:
            header = "⚠️  Plan FREE activo"
            header_style = "font-size: 14px; font-weight: bold; color: #F59E0B;"

        texto = (
            f"{header}\n"
            f"─────────────────────────────────\n"
            f"📦  Productos:            {productos}\n"
            f"👥  Clientes:             {clientes}\n"
            f"👤  Usuarios:             {usuarios}\n"
            f"─────────────────────────────────\n"
            f"🏭  Proveedores:          {si_no(limits['suppliers'])}\n"
            f"📊  Reportes y análisis:  {si_no(limits['reports'])}\n"
            f"✉️   Envío por email:      {si_no(limits['email'])}\n"
            f"💾  Backup automático:    {si_no(limits['backup'])}\n"
            f"🧾  Factura electrónica:  {si_no(limits['arca'])}\n"
            f"🌐  Multi-PC (red local): {si_no(limits['postgresql'])}\n"
            f"🖨️   Marca de agua ticket: {'Sí (plan FREE)' if limits['ticket_watermark'] else '❌  Sin marca de agua'}\n"
        )

        if plan == "FREE":
            texto += (
                f"─────────────────────────────────\n"
                f"💡  Activá SARA+ para desbloquear\n"
                f"    proveedores, reportes, email,\n"
                f"    backup y usuarios ilimitados."
            )

        self.license_limits_label.setText(texto)

    # ── Helpers UI ────────────────────────────────────

    def combo_style(self):
        return """
            QComboBox {
                background-color: white;
                border: 2px solid #B8C4D0;
                border-radius: 12px;
                padding: 10px 14px;
                font-size: 15px;
                color: #1E293B;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #1E293B;
                selection-background-color: #D8E6F5;
            }
        """

    def create_input(self, placeholder):
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setMinimumHeight(50)
        field.setStyleSheet(INPUT_STYLE)
        return field

    def on_provider_changed(self, provider):
        if provider == "Otro (manual)":
            self.smtp_manual_frame.show()
        else:
            self.smtp_manual_frame.hide()

    def refresh_printers(self):
        self.printer_combo.clear()
        self.printer_combo.addItems(get_installed_printers())

    # ── Base de datos ─────────────────────────────────

    def save_section(self, keys_map):
        db = SessionLocal()
        try:
            for key, value in keys_map.items():
                setting = db.query(Setting).filter(Setting.key == key).first()
                if setting:
                    setting.value = value
                else:
                    db.add(Setting(key=key, value=value))
            db.commit()
        except Exception as e:
            db.rollback()
            self.show_message("Error", f"Error al guardar: {str(e)}")
            return False
        finally:
            db.close()
        return True

    def load_settings(self):
        db = SessionLocal()
        try:
            settings = db.query(Setting).all()
            data = {s.key: s.value for s in settings}
        finally:
            db.close()

        # Negocio
        self.business_name_input.setText(data.get("business_name", ""))
        self.business_cuit_input.setText(data.get("business_cuit", ""))
        self.business_address_input.setText(data.get("business_address", ""))
        self.business_phone_input.setText(data.get("business_phone", ""))
        self.ticket_legend_input.setText(data.get("ticket_legend", ""))
        self.ticket_footer_input.setText(data.get("ticket_footer", ""))

        # Email
        self.mp_alias_input.setText(data.get("mp_alias", ""))
        self.smtp_email_input.setText(data.get("smtp_email", ""))
        self.smtp_password_input.setText(data.get("smtp_password", ""))
        self.smtp_host_input.setText(data.get("smtp_host", ""))
        self.smtp_port_input.setText(data.get("smtp_port", ""))

        provider = data.get("smtp_provider", "Gmail")
        index = self.smtp_provider_combo.findText(provider)
        if index >= 0:
            self.smtp_provider_combo.setCurrentIndex(index)
        self.on_provider_changed(provider)

        # Impresora
        printer_name = data.get("printer_name", "")
        if printer_name:
            index = self.printer_combo.findText(printer_name)
            if index >= 0:
                self.printer_combo.setCurrentIndex(index)

        printer_size = data.get("printer_size", "80mm")
        index = self.printer_size_combo.findText(printer_size)
        if index >= 0:
            self.printer_size_combo.setCurrentIndex(index)

        qr_path = data.get("payment_qr_path", "")
        if qr_path:
            self.qr_path_label.setText(qr_path)

        # Backup
        self.auto_backup_check.setChecked(data.get("backup_auto", "0") == "1")
        try:
            self.backup_freq_spin.setValue(int(data.get("backup_freq_days", "7")))
        except Exception:
            self.backup_freq_spin.setValue(7)

        backup_folder = data.get("backup_folder", "")
        if backup_folder:
            self.backup_folder_label.setText(f"Carpeta: {backup_folder}")

        last_backup = data.get("backup_last_date", "")
        if last_backup:
            self.last_backup_label.setText(f"Último backup: {last_backup}")

        # ARCA
        self.arca_enabled_check.setChecked(data.get("arca_enabled", "0") == "1")
        self.arca_cuit_input.setText(data.get("arca_cuit", ""))

        cond_emisor = data.get("arca_cond_iva_emisor", "Responsable Inscripto")
        idx = self.arca_cond_iva_emisor_combo.findText(cond_emisor)
        if idx >= 0:
            self.arca_cond_iva_emisor_combo.setCurrentIndex(idx)

        try:
            self.arca_pdv_spin.setValue(int(data.get("arca_pdv", "1")))
        except Exception:
            self.arca_pdv_spin.setValue(1)

        crt_path = data.get("arca_crt_path", "")
        if crt_path:
            self.arca_crt_label.setText(f"Certificado (.crt): {os.path.basename(crt_path)}")

        key_path = data.get("arca_key_path", "")
        if key_path:
            self.arca_key_label.setText(f"Clave privada (.key): {os.path.basename(key_path)}")

        iva_default = data.get("arca_iva_default", "21%")
        idx = self.arca_iva_combo.findText(iva_default)
        if idx >= 0:
            self.arca_iva_combo.setCurrentIndex(idx)

        cond_cliente = data.get("arca_cond_iva_cliente", "Consumidor Final")
        idx = self.arca_cond_iva_cliente_combo.findText(cond_cliente)
        if idx >= 0:
            self.arca_cond_iva_cliente_combo.setCurrentIndex(idx)

        self.arca_umbral_input.setText(data.get("arca_umbral_identificacion", "10000000"))

        try:
            self.arca_num_a_spin.setValue(int(data.get("arca_ultimo_num_a", "0")))
            self.arca_num_b_spin.setValue(int(data.get("arca_ultimo_num_b", "0")))
            self.arca_num_c_spin.setValue(int(data.get("arca_ultimo_num_c", "0")))
        except Exception:
            pass

        ambiente = data.get("arca_ambiente", "Homologación (pruebas)")
        idx = self.arca_ambiente_combo.findText(ambiente)
        if idx >= 0:
            self.arca_ambiente_combo.setCurrentIndex(idx)

        entrega = data.get("arca_entrega", "Impresa (impresora térmica)")
        idx = self.arca_entrega_combo.findText(entrega)
        if idx >= 0:
            self.arca_entrega_combo.setCurrentIndex(idx)

    # ── Guardar secciones ─────────────────────────────

        # Base de datos / Red
        db_mode = get_db_mode()
        if db_mode == "postgresql":
            self.db_mode_combo.setCurrentIndex(1)
        else:
            self.db_mode_combo.setCurrentIndex(0)
        self.on_db_mode_changed(self.db_mode_combo.currentIndex())

        # Leer config de db_config.ini para poblar los campos PG
        from app.database.database import _get_db_config
        db_cfg = _get_db_config()
        self.pg_host_input.setText(db_cfg.get("host", "localhost"))
        self.pg_port_input.setText(db_cfg.get("port", "5432"))
        self.pg_database_input.setText(db_cfg.get("database", "sara_pos"))
        self.pg_user_input.setText(db_cfg.get("user", "sara"))
        self.pg_password_input.setText(db_cfg.get("password", ""))

    def save_business(self):
        if self.save_section({
            "business_name": self.business_name_input.text(),
            "business_cuit": self.business_cuit_input.text(),
            "business_address": self.business_address_input.text(),
            "business_phone": self.business_phone_input.text(),
            "ticket_legend": self.ticket_legend_input.text(),
            "ticket_footer": self.ticket_footer_input.text(),
        }):
            self.show_message("OK", "Datos del negocio guardados")

    def save_printer(self):
        if self.save_section({
            "printer_name": self.printer_combo.currentText(),
            "printer_size": self.printer_size_combo.currentText(),
        }):
            self.show_message("OK", "Configuración de impresora guardada")

    def save_payment(self):
        if self.save_section({
            "mp_alias": self.mp_alias_input.text(),
            "payment_qr_path": self.qr_path_label.text(),
        }):
            self.show_message("OK", "Métodos de pago guardados")

    def save_smtp(self):
        provider = self.smtp_provider_combo.currentText()
        host, port = SMTP_PROVIDERS.get(provider, ("", ""))
        if provider == "Otro (manual)":
            host = self.smtp_host_input.text().strip()
            port = self.smtp_port_input.text().strip()
        if self.save_section({
            "smtp_provider": provider,
            "smtp_host": host,
            "smtp_port": port,
            "smtp_email": self.smtp_email_input.text().strip(),
            "smtp_password": self.smtp_password_input.text().strip(),
        }):
            self.show_message("OK", "Configuración de email guardada")

    def show_gmail_help(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea, QWidget
        from PySide6.QtCore import Qt

        dialog = QDialog(self)
        dialog.setWindowTitle("Cómo generar la Contraseña de App en Gmail")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(420)
        dialog.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("🔐  Contraseña de App — Gmail")
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #4A6A92;")
        layout.addWidget(title)

        intro = QLabel("Gmail no permite usar tu contraseña normal en apps externas. Necesitás generar una Contraseña de App específica para SARA POS.")
        intro.setStyleSheet("font-size: 13px; color: #64748B;")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        steps = [
            ("1", "Entrá a", "myaccount.google.com"),
            ("2", "Andá a", "Seguridad → Verificación en dos pasos\n       (debe estar activada para continuar)"),
            ("3", "Bajá hasta", "Contraseñas de aplicaciones"),
            ("4", "Creá una nueva →", "elegí \"Otra (nombre personalizado)\"\n       → escribí SARA POS"),
            ("5", "Google te genera", "una clave de 16 caracteres\n       tipo: xxxx xxxx xxxx xxxx"),
            ("6", "Copiala y pegala en", "SARA → Configuración → Email\n       → campo Contraseña"),
            ("7", "Presioná", "Guardar configuración de email"),
        ]

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        for num, action, detail in steps:
            row_widget = QWidget()
            row_widget.setStyleSheet("background-color: #F8FAFC; border-radius: 8px;")
            row_layout = QVBoxLayout(row_widget)
            row_layout.setContentsMargins(12, 10, 12, 10)
            row_layout.setSpacing(2)

            step_label = QLabel(f"Paso {num} — {action}")
            step_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #1E293B; background: transparent;")
            row_layout.addWidget(step_label)

            detail_label = QLabel(f"       {detail}")
            detail_label.setStyleSheet("font-size: 13px; color: #4A6A92; background: transparent;")
            detail_label.setWordWrap(True)
            row_layout.addWidget(detail_label)

            scroll_layout.addWidget(row_widget)

        scroll_area = QScrollArea()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: white; }")
        layout.addWidget(scroll_area)

        btn_ok = QPushButton("Entendido")
        btn_ok.setMinimumHeight(46)
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #4A6A92; color: white;
                border: none; border-radius: 10px;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #3D5A80; }
        """)
        btn_ok.clicked.connect(dialog.accept)
        layout.addWidget(btn_ok)

        dialog.exec()

    def select_qr(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar QR", "", "Images (*.png *.jpg *.jpeg)"
        )
        if not file_path:
            return
        qr_folder = Path("app/assets/payment_qr")
        qr_folder.mkdir(parents=True, exist_ok=True)
        destination = qr_folder / "mercadopago_qr.png"
        shutil.copy(file_path, destination)
        self.qr_path_label.setText(str(destination))

    def on_db_mode_changed(self, index):
        if index == 1:
            self.pg_frame.show()
        else:
            self.pg_frame.hide()

    def test_db_connection(self):
        config = self._build_pg_config()
        if not config:
            return
        ok, msg = test_connection(config)
        if ok:
            self.show_message("✅ Conexión exitosa", f"SARA+ se conectó correctamente a PostgreSQL en:\n{config['host']}:{config['port']}/{config['database']}")
        else:
            self.show_message("❌ Error de conexión", f"No se pudo conectar a PostgreSQL:\n\n{msg}\n\nVerificá los datos e intentá de nuevo.")

    def save_db_config(self):
        mode_index = self.db_mode_combo.currentIndex()

        if mode_index == 0:
            # SQLite local
            new_config = {
                "mode": "sqlite",
                "host": "localhost",
                "port": "5432",
                "database": "sara_pos",
                "user": "sara",
                "password": "",
            }
        else:
            # PostgreSQL
            new_config = self._build_pg_config()
            if not new_config:
                return

            # Probar conexión antes de guardar
            ok, msg = test_connection(new_config)
            if not ok:
                self.show_message(
                    "Error de conexión",
                    f"No se pudo conectar a PostgreSQL:\n\n{msg}\n\nVerificá los datos antes de guardar."
                )
                return

        try:
            reload_engine(new_config)
            modo = "SQLite (local)" if new_config["mode"] == "sqlite" else f"PostgreSQL ({new_config['host']}:{new_config['port']})"
            self.show_message("OK", f"Configuración guardada.\nModo activo: {modo}\n\nLa conexión fue aplicada correctamente.")
        except Exception as e:
            self.show_message("Error", f"Error al aplicar la configuración:\n{str(e)}")

    def _build_pg_config(self):
        host = self.pg_host_input.text().strip()
        port = self.pg_port_input.text().strip() or "5432"
        database = self.pg_database_input.text().strip()
        user = self.pg_user_input.text().strip()
        password = self.pg_password_input.text().strip()

        if not host:
            self.show_message("Error", "Ingresá la IP del servidor PostgreSQL")
            return None
        if not database:
            self.show_message("Error", "Ingresá el nombre de la base de datos")
            return None
        if not user:
            self.show_message("Error", "Ingresá el usuario de PostgreSQL")
            return None

        return {
            "mode": "postgresql",
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
        }

    def save_arca_config(self):
        umbral = self.arca_umbral_input.text().strip()
        if not umbral.isdigit():
            self.show_message("Error", "El umbral de identificación debe ser un número entero (ej: 10000000)")
            return

        cuit = self.arca_cuit_input.text().strip().replace("-", "").replace(" ", "")
        if cuit and (not cuit.isdigit() or len(cuit) != 11):
            self.show_message("Error", "El CUIT debe tener 11 dígitos sin guiones (ej: 20123456789)")
            return

        if self.save_section({
            "arca_enabled": "1" if self.arca_enabled_check.isChecked() else "0",
            "arca_cuit": cuit,
            "arca_cond_iva_emisor": self.arca_cond_iva_emisor_combo.currentText(),
            "arca_pdv": str(self.arca_pdv_spin.value()),
            "arca_iva_default": self.arca_iva_combo.currentText(),
            "arca_cond_iva_cliente": self.arca_cond_iva_cliente_combo.currentText(),
            "arca_umbral_identificacion": umbral,
            "arca_ultimo_num_a": str(self.arca_num_a_spin.value()),
            "arca_ultimo_num_b": str(self.arca_num_b_spin.value()),
            "arca_ultimo_num_c": str(self.arca_num_c_spin.value()),
            "arca_ambiente": self.arca_ambiente_combo.currentText(),
            "arca_entrega": self.arca_entrega_combo.currentText(),
        }):
            self.show_message("OK", "Configuración ARCA guardada correctamente")

    # ── Certificados ARCA ─────────────────────────────

    def select_arca_crt(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar certificado", "", "Certificado (*.crt *.pem)"
        )
        if not file_path:
            return
        try:
            cert_folder = Path("app/assets/arca")
            cert_folder.mkdir(parents=True, exist_ok=True)
            destination = cert_folder / "cert.crt"
            shutil.copy(file_path, destination)
            self.arca_crt_label.setText(f"Certificado (.crt): {os.path.basename(file_path)}")
            self.save_section({"arca_crt_path": str(destination)})
        except Exception as e:
            self.show_message("Error", f"Error al cargar el certificado: {str(e)}")

    def select_arca_key(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar clave privada", "", "Clave privada (*.key *.pem)"
        )
        if not file_path:
            return
        try:
            cert_folder = Path("app/assets/arca")
            cert_folder.mkdir(parents=True, exist_ok=True)
            destination = cert_folder / "private.key"
            shutil.copy(file_path, destination)
            self.arca_key_label.setText(f"Clave privada (.key): {os.path.basename(file_path)}")
            self.save_section({"arca_key_path": str(destination)})
        except Exception as e:
            self.show_message("Error", f"Error al cargar la clave privada: {str(e)}")

    # ── Backup ────────────────────────────────────────

    def do_manual_backup(self):
        db_path = get_db_path()

        if not os.path.exists(db_path):
            self.show_message("Error", f"No se encontró la base de datos en:\n{db_path}")
            return

        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para backup")
        if not folder:
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = os.path.join(folder, f"sara_pos_backup_{timestamp}.db")
            shutil.copy2(db_path, dest)
            now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
            self.save_section({"backup_last_date": now_str})
            self.last_backup_label.setText(f"Último backup: {now_str}")
            self.show_message("OK", f"Backup guardado correctamente en:\n{dest}")
        except Exception as e:
            self.show_message("Error", f"Error al hacer backup: {str(e)}")

    def do_restore_backup(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo de backup", "", "Base de datos (*.db)"
        )
        if not file_path:
            return

        reply = QMessageBox(self)
        reply.setWindowTitle("Restaurar backup")
        reply.setText(
            "⚠️ Esto reemplazará TODOS los datos actuales con el backup seleccionado.\n\n"
            "Se creará una copia de seguridad automática antes de restaurar.\n\n"
            "¿Estás seguro?"
        )
        reply.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        reply.setDefaultButton(QMessageBox.No)
        reply.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1E293B; font-size: 14px; min-width: 350px; }
            QPushButton {
                background-color: #4A6A92; color: white; border: none;
                border-radius: 10px; padding: 10px 20px; min-width: 80px;
                min-height: 32px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #3D5A80; }
        """)
        if reply.exec() != QMessageBox.Yes:
            return

        db_path = get_db_path()

        try:
            if os.path.exists(db_path):
                safety_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                safety_dest = db_path + f".pre_restore_{safety_ts}.bak"
                shutil.copy2(db_path, safety_dest)
            shutil.copy2(file_path, db_path)
            self.show_message(
                "OK",
                "✅ Backup restaurado correctamente.\n\nReiniciá la aplicación para que los cambios tomen efecto."
            )
        except Exception as e:
            self.show_message("Error", f"Error al restaurar el backup: {str(e)}")

    def select_backup_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de backup automático")
        if folder:
            self.backup_folder_label.setText(f"Carpeta: {folder}")

    def save_backup_config(self):
        folder_text = self.backup_folder_label.text()
        folder = folder_text.replace("Carpeta: ", "") if folder_text != "Carpeta: no configurada" else ""
        if self.save_section({
            "backup_auto": "1" if self.auto_backup_check.isChecked() else "0",
            "backup_freq_days": str(self.backup_freq_spin.value()),
            "backup_folder": folder,
        }):
            self.show_message("OK", "Configuración de backup guardada")

    def check_auto_backup(self):
        db = SessionLocal()
        try:
            settings = db.query(Setting).all()
            data = {s.key: s.value for s in settings}
        finally:
            db.close()

        if data.get("backup_auto", "0") != "1":
            return

        backup_folder = data.get("backup_folder", "")
        if not backup_folder:
            return

        freq_days = int(data.get("backup_freq_days", "7"))
        last_backup_str = data.get("backup_last_date", "")
        should_backup = False

        if not last_backup_str:
            should_backup = True
        else:
            try:
                last_backup = datetime.strptime(last_backup_str, "%d/%m/%Y %H:%M")
                if (datetime.now() - last_backup).days >= freq_days:
                    should_backup = True
            except Exception:
                should_backup = True

        if should_backup:
            try:
                db_path = get_db_path()
                if not os.path.exists(db_path):
                    return
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest = os.path.join(backup_folder, f"sara_pos_backup_{timestamp}.db")
                shutil.copy2(db_path, dest)
                now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
                self.save_section({"backup_last_date": now_str})
                self.last_backup_label.setText(f"Último backup: {now_str}")
            except Exception:
                pass

    # ── ABM Usuarios ──────────────────────────────────

    def load_users(self):
        db = SessionLocal()
        try:
            users = db.query(User).all()
        finally:
            db.close()

        self.users_table.setRowCount(0)
        for row, user in enumerate(users):
            self.users_table.insertRow(row)
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user.id)))
            self.users_table.setItem(row, 1, QTableWidgetItem(user.username or ""))
            self.users_table.setItem(row, 2, QTableWidgetItem(user.role or ""))
            estado = "Activo" if user.is_active else "Inactivo"
            estado_item = QTableWidgetItem(estado)
            estado_item.setForeground(Qt.darkGreen if user.is_active else Qt.red)
            self.users_table.setItem(row, 3, estado_item)

    def select_user(self, row):
        self.selected_user_id = int(self.users_table.item(row, 0).text())
        self.user_username_input.setText(self.users_table.item(row, 1).text())
        role = self.users_table.item(row, 2).text()
        index = self.user_role_combo.findText(role)
        if index >= 0:
            self.user_role_combo.setCurrentIndex(index)
        self.user_password_input.clear()

    def save_user(self):
        username = self.user_username_input.text().strip()
        password = self.user_password_input.text().strip()
        role = self.user_role_combo.currentText()

        if not username or not password:
            self.show_message("Error", "Usuario y contraseña son obligatorios")
            return

        db = SessionLocal()
        try:
            existing = db.query(User).filter(User.username == username).first()
            if existing:
                self.show_message("Error", f"El usuario '{username}' ya existe")
                return
            user = User(
                username=username,
                password=hash_password(password),
                role=role,
                is_active=True
            )
            db.add(user)
            db.commit()
            self.show_message("OK", f"Usuario '{username}' creado correctamente")
            self.load_users()
            self.clear_user_form()
        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def update_user(self):
        if not self.selected_user_id:
            self.show_message("Error", "Seleccione un usuario")
            return

        username = self.user_username_input.text().strip()
        password = self.user_password_input.text().strip()
        role = self.user_role_combo.currentText()

        if not username:
            self.show_message("Error", "El usuario es obligatorio")
            return

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == self.selected_user_id).first()
            if not user:
                self.show_message("Error", "Usuario no encontrado")
                return
            user.username = username
            user.role = role
            if password:
                user.password = hash_password(password)
            db.commit()
            self.show_message("OK", "Usuario actualizado correctamente")
            self.load_users()
            self.clear_user_form()
        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def toggle_user(self):
        if not self.selected_user_id:
            self.show_message("Error", "Seleccione un usuario")
            return

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == self.selected_user_id).first()
            if not user:
                self.show_message("Error", "Usuario no encontrado")
                return
            if user.username == "admin":
                self.show_message("Error", "No se puede desactivar el usuario admin")
                return
            user.is_active = not user.is_active
            db.commit()
            estado = "activado" if user.is_active else "desactivado"
            self.show_message("OK", f"Usuario {estado} correctamente")
            self.load_users()
            self.clear_user_form()
        except Exception as e:
            db.rollback()
            self.show_message("Error", str(e))
        finally:
            db.close()

    def clear_user_form(self):
        self.selected_user_id = None
        self.user_username_input.clear()
        self.user_password_input.clear()
        self.user_role_combo.setCurrentIndex(0)

    def show_message(self, title, message):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1E293B; font-size: 15px; font-weight: bold; min-width: 300px; }
            QPushButton {
                background-color: #4A6A92; color: white; border: none;
                border-radius: 10px; padding: 10px 20px; min-width: 80px;
                min-height: 32px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #3D5A80; }
        """)
        msg.exec()