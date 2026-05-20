from pathlib import Path
import shutil

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QFrame,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFileDialog,
    QScrollArea,
)

from app.assets.themes.theme import (
    PRIMARY_COLOR,
    INPUT_STYLE,
    BUTTON_STYLE,
)

from app.database.database import (
    SessionLocal
)

from app.models.settings_model import (
    Setting
)

from app.components.collapsible_section import (
    CollapsibleSection
)


class SettingsPage(QWidget):

    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Configuración")
        title.setStyleSheet(f"""
            font-size: 34px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
        """)
        main_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)

        # ── Negocio ───────────────────────────────────
        business_widget = QWidget()
        business_layout = QVBoxLayout()
        business_layout.setSpacing(15)

        self.business_name_input = self.create_input("Nombre negocio")
        business_layout.addWidget(self.business_name_input)

        self.business_cuit_input = self.create_input("CUIT/CUIL")
        business_layout.addWidget(self.business_cuit_input)

        self.business_address_input = self.create_input("Dirección")
        business_layout.addWidget(self.business_address_input)

        self.business_phone_input = self.create_input("Teléfono")
        business_layout.addWidget(self.business_phone_input)

        self.ticket_footer_input = self.create_input("Pie ticket")
        business_layout.addWidget(self.ticket_footer_input)

        business_widget.setLayout(business_layout)
        content_layout.addWidget(CollapsibleSection("Negocio", business_widget))

        # ── Impresora ─────────────────────────────────
        printer_widget = QWidget()
        printer_layout = QVBoxLayout()
        printer_layout.setSpacing(15)

        self.printer_name_input = self.create_input("Nombre impresora")
        printer_layout.addWidget(self.printer_name_input)

        self.printer_size_input = self.create_input("58mm / 80mm")
        printer_layout.addWidget(self.printer_size_input)

        printer_widget.setLayout(printer_layout)
        content_layout.addWidget(CollapsibleSection("Impresora", printer_widget))

        # ── Métodos de pago ───────────────────────────
        payment_widget = QWidget()
        payment_layout = QVBoxLayout()
        payment_layout.setSpacing(15)

        self.mp_alias_input = self.create_input("Alias MercadoPago")
        payment_layout.addWidget(self.mp_alias_input)

        self.qr_path_label = QLabel("QR no configurado")
        self.qr_path_label.setStyleSheet("color: #64748B; font-size: 14px;")
        payment_layout.addWidget(self.qr_path_label)

        qr_button = QPushButton("Seleccionar QR")
        qr_button.setMinimumHeight(50)
        qr_button.setStyleSheet(BUTTON_STYLE)
        qr_button.clicked.connect(self.select_qr)
        payment_layout.addWidget(qr_button)

        payment_widget.setLayout(payment_layout)
        content_layout.addWidget(CollapsibleSection("Métodos de pago", payment_widget))

        # ── Email SMTP ────────────────────────────────
        smtp_widget = QWidget()
        smtp_layout = QVBoxLayout()
        smtp_layout.setSpacing(15)

        self.smtp_host_input = self.create_input("SMTP Host")
        smtp_layout.addWidget(self.smtp_host_input)

        self.smtp_port_input = self.create_input("SMTP Port")
        smtp_layout.addWidget(self.smtp_port_input)

        self.smtp_email_input = self.create_input("Email")
        smtp_layout.addWidget(self.smtp_email_input)

        self.smtp_password_input = self.create_input("Password App")
        self.smtp_password_input.setEchoMode(QLineEdit.Password)
        smtp_layout.addWidget(self.smtp_password_input)

        smtp_widget.setLayout(smtp_layout)
        content_layout.addWidget(CollapsibleSection("Email SMTP", smtp_widget))

        # ── Guardar ───────────────────────────────────
        save_button = QPushButton("Guardar configuración")
        save_button.setMinimumHeight(60)
        save_button.setStyleSheet(BUTTON_STYLE)
        save_button.clicked.connect(self.save_settings)
        content_layout.addWidget(save_button)

        content_layout.addStretch()
        content.setLayout(content_layout)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

        self.load_settings()

    def create_input(self, placeholder):

        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setMinimumHeight(50)
        input_field.setStyleSheet(INPUT_STYLE)
        return input_field

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
        self.ticket_footer_input.setText(data.get("ticket_footer", ""))
        self.printer_name_input.setText(data.get("printer_name", ""))
        self.printer_size_input.setText(data.get("printer_size", ""))
        self.mp_alias_input.setText(data.get("mp_alias", ""))
        self.smtp_host_input.setText(data.get("smtp_host", ""))
        self.smtp_port_input.setText(data.get("smtp_port", ""))
        self.smtp_email_input.setText(data.get("smtp_email", ""))
        self.smtp_password_input.setText(data.get("smtp_password", ""))

        qr_path = data.get("payment_qr_path", "")
        if qr_path:
            self.qr_path_label.setText(qr_path)

    def select_qr(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar QR",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )

        if not file_path:
            return

        qr_folder = Path("app/assets/payment_qr")
        qr_folder.mkdir(parents=True, exist_ok=True)
        destination = qr_folder / "mercadopago_qr.png"
        shutil.copy(file_path, destination)
        self.qr_path_label.setText(str(destination))

    def save_settings(self):

        db = SessionLocal()

        try:
            settings_map = {
                "business_name": self.business_name_input.text(),
                "business_cuit": self.business_cuit_input.text(),
                "business_address": self.business_address_input.text(),
                "business_phone": self.business_phone_input.text(),
                "ticket_footer": self.ticket_footer_input.text(),
                "printer_name": self.printer_name_input.text(),
                "printer_size": self.printer_size_input.text(),
                "mp_alias": self.mp_alias_input.text(),
                "payment_qr_path": self.qr_path_label.text(),
                "smtp_host": self.smtp_host_input.text(),
                "smtp_port": self.smtp_port_input.text(),
                "smtp_email": self.smtp_email_input.text(),
                "smtp_password": self.smtp_password_input.text(),
            }

            for key, value in settings_map.items():
                setting = db.query(Setting).filter(
                    Setting.key == key
                ).first()

                if setting:
                    # Actualizar existente
                    setting.value = value
                else:
                    # Crear nuevo
                    new_setting = Setting(key=key, value=value)
                    db.add(new_setting)

            db.commit()

        except Exception as e:
            db.rollback()
            QMessageBox.warning(self, "Error", f"Error al guardar: {str(e)}")
            return

        finally:
            db.close()

        msg = QMessageBox(self)
        msg.setWindowTitle("Correcto")
        msg.setText("Configuración guardada correctamente")
        msg.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel {
                color: #1E293B;
                font-size: 15px;
                font-weight: bold;
                min-width: 300px;
            }
            QPushButton {
                background-color: #4A6A92;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                min-width: 80px;
                min-height: 32px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3D5A80; }
        """)
        msg.exec()