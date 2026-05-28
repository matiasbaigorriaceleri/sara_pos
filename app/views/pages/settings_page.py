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
from app.database.database import SessionLocal
from app.models.settings_model import Setting
from app.models.user_model import User
from app.components.collapsible_section import CollapsibleSection


SMTP_PROVIDERS = {
    "Gmail": ("smtp.gmail.com", "587"),
    "Outlook / Hotmail": ("smtp.office365.com", "587"),
    "Yahoo": ("smtp.mail.yahoo.com", "587"),
    "Otro (manual)": ("", ""),
}


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

        btn_save_smtp = QPushButton("Guardar configuración de email")
        btn_save_smtp.setMinimumHeight(48)
        btn_save_smtp.setStyleSheet(BUTTON_STYLE)
        btn_save_smtp.clicked.connect(self.save_smtp)
        smtp_layout.addWidget(btn_save_smtp)

        smtp_widget.setLayout(smtp_layout)
        content_layout.addWidget(CollapsibleSection("Email", smtp_widget))

        # ── Backup ────────────────────────────────────
        backup_widget = QWidget()
        backup_layout = QVBoxLayout()
        backup_layout.setContentsMargins(16, 16, 16, 16)
        backup_layout.setSpacing(12)

        # Backup manual
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

        # Restore backup
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

        btn_restore_backup = QPushButton("Restaurar backup")
        btn_restore_backup.setMinimumHeight(48)
        btn_restore_backup.setStyleSheet(BUTTON_STYLE_SECONDARY)
        btn_restore_backup.clicked.connect(self.do_restore_backup)
        backup_layout.addWidget(btn_restore_backup)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #E2E8F0; margin: 8px 0;")
        backup_layout.addWidget(sep)

        # Backup automático
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

        # Carpeta de backup
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

        # Último backup
        self.last_backup_label = QLabel("Último backup: nunca")
        self.last_backup_label.setStyleSheet("font-size: 12px; color: #94A3B8; background: transparent;")
        backup_layout.addWidget(self.last_backup_label)

        btn_save_backup = QPushButton("Guardar configuración de backup")
        btn_save_backup.setMinimumHeight(48)
        btn_save_backup.setStyleSheet(BUTTON_STYLE)
        btn_save_backup.clicked.connect(self.save_backup_config)
        backup_layout.addWidget(btn_save_backup)

        backup_widget.setLayout(backup_layout)
        content_layout.addWidget(CollapsibleSection("Backup", backup_widget))

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

        content_layout.addStretch()
        content.setLayout(content_layout)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

        self.load_settings()
        self.load_users()
        self.check_auto_backup()

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

        self.business_name_input.setText(data.get("business_name", ""))
        self.business_cuit_input.setText(data.get("business_cuit", ""))
        self.business_address_input.setText(data.get("business_address", ""))
        self.business_phone_input.setText(data.get("business_phone", ""))
        self.ticket_legend_input.setText(data.get("ticket_legend", ""))
        self.ticket_footer_input.setText(data.get("ticket_footer", ""))
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
        auto_backup = data.get("backup_auto", "0")
        self.auto_backup_check.setChecked(auto_backup == "1")

        freq = data.get("backup_freq_days", "7")
        try:
            self.backup_freq_spin.setValue(int(freq))
        except Exception:
            self.backup_freq_spin.setValue(7)

        backup_folder = data.get("backup_folder", "")
        if backup_folder:
            self.backup_folder_label.setText(f"Carpeta: {backup_folder}")

        last_backup = data.get("backup_last_date", "")
        if last_backup:
            self.last_backup_label.setText(f"Último backup: {last_backup}")

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
            # Hacer un backup de seguridad del estado actual antes de restaurar
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
                days_since = (datetime.now() - last_backup).days
                if days_since >= freq_days:
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