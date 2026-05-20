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

        # =====================================
        # MAIN LAYOUT
        # =====================================

        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(
            20,
            20,
            20,
            20
        )

        main_layout.setSpacing(15)

        # =====================================
        # TITLE
        # =====================================

        title = QLabel("Configuración")

        title.setStyleSheet(f"""
            font-size: 34px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
        """)

        main_layout.addWidget(title)

        # =====================================
        # SCROLL AREA
        # =====================================

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        # =====================================
        # CONTENT
        # =====================================

        content = QWidget()

        content_layout = QVBoxLayout()

        content_layout.setSpacing(20)

        # =====================================
        # BUSINESS SECTION
        # =====================================

        business_widget = QWidget()

        business_layout = QVBoxLayout()

        business_layout.setSpacing(15)

        self.business_name_input = (
            self.create_input(
                "Nombre negocio"
            )
        )

        business_layout.addWidget(
            self.business_name_input
        )

        self.business_cuit_input = (
            self.create_input(
                "CUIT/CUIL"
            )
        )

        business_layout.addWidget(
            self.business_cuit_input
        )

        self.business_address_input = (
            self.create_input(
                "Dirección"
            )
        )

        business_layout.addWidget(
            self.business_address_input
        )

        self.business_phone_input = (
            self.create_input(
                "Teléfono"
            )
        )

        business_layout.addWidget(
            self.business_phone_input
        )

        self.ticket_footer_input = (
            self.create_input(
                "Pie ticket"
            )
        )

        business_layout.addWidget(
            self.ticket_footer_input
        )

        business_widget.setLayout(
            business_layout
        )

        business_section = (
            CollapsibleSection(
                "Negocio",
                business_widget
            )
        )

        content_layout.addWidget(
            business_section
        )

        # =====================================
        # PRINTER SECTION
        # =====================================

        printer_widget = QWidget()

        printer_layout = QVBoxLayout()

        printer_layout.setSpacing(15)

        self.printer_name_input = (
            self.create_input(
                "Nombre impresora"
            )
        )

        printer_layout.addWidget(
            self.printer_name_input
        )

        self.printer_size_input = (
            self.create_input(
                "58mm / 80mm"
            )
        )

        printer_layout.addWidget(
            self.printer_size_input
        )

        printer_widget.setLayout(
            printer_layout
        )

        printer_section = (
            CollapsibleSection(
                "Impresora",
                printer_widget
            )
        )

        content_layout.addWidget(
            printer_section
        )

        # =====================================
        # PAYMENT SECTION
        # =====================================

        payment_widget = QWidget()

        payment_layout = QVBoxLayout()

        payment_layout.setSpacing(15)

        self.mp_alias_input = (
            self.create_input(
                "Alias MercadoPago"
            )
        )

        payment_layout.addWidget(
            self.mp_alias_input
        )

        self.qr_path_label = QLabel(
            "QR no configurado"
        )

        self.qr_path_label.setStyleSheet("""
            color: #64748B;
            font-size: 14px;
        """)

        payment_layout.addWidget(
            self.qr_path_label
        )

        qr_button = QPushButton(
            "Seleccionar QR"
        )

        qr_button.setMinimumHeight(50)

        qr_button.setStyleSheet(
            BUTTON_STYLE
        )

        qr_button.clicked.connect(
            self.select_qr
        )

        payment_layout.addWidget(
            qr_button
        )

        payment_widget.setLayout(
            payment_layout
        )

        payment_section = (
            CollapsibleSection(
                "Métodos de pago",
                payment_widget
            )
        )

        content_layout.addWidget(
            payment_section
        )

        # =====================================
        # SMTP SECTION
        # =====================================

        smtp_widget = QWidget()

        smtp_layout = QVBoxLayout()

        smtp_layout.setSpacing(15)

        self.smtp_host_input = (
            self.create_input(
                "SMTP Host"
            )
        )

        smtp_layout.addWidget(
            self.smtp_host_input
        )

        self.smtp_port_input = (
            self.create_input(
                "SMTP Port"
            )
        )

        smtp_layout.addWidget(
            self.smtp_port_input
        )

        self.smtp_email_input = (
            self.create_input(
                "Email"
            )
        )

        smtp_layout.addWidget(
            self.smtp_email_input
        )

        self.smtp_password_input = (
            self.create_input(
                "Password App"
            )
        )

        self.smtp_password_input.setEchoMode(
            QLineEdit.Password
        )

        smtp_layout.addWidget(
            self.smtp_password_input
        )

        smtp_widget.setLayout(
            smtp_layout
        )

        smtp_section = (
            CollapsibleSection(
                "Email SMTP",
                smtp_widget
            )
        )

        content_layout.addWidget(
            smtp_section
        )

        # =====================================
        # SAVE BUTTON
        # =====================================

        save_button = QPushButton(
            "Guardar configuración"
        )

        save_button.setMinimumHeight(60)

        save_button.setStyleSheet(
            BUTTON_STYLE
        )

        save_button.clicked.connect(
            self.save_settings
        )

        content_layout.addWidget(
            save_button
        )

        content_layout.addStretch()

        content.setLayout(content_layout)

        scroll.setWidget(content)

        main_layout.addWidget(scroll)

        self.setLayout(main_layout)

        self.load_settings()

    # =====================================
    # CREATE INPUT
    # =====================================

    def create_input(self, placeholder):

        input_field = QLineEdit()

        input_field.setPlaceholderText(
            placeholder
        )

        input_field.setMinimumHeight(50)

        input_field.setStyleSheet(
            INPUT_STYLE
        )

        return input_field

    # =====================================
    # LOAD SETTINGS
    # =====================================

    def load_settings(self):

        db = SessionLocal()

        settings = db.query(Setting).all()

        data = {}

        for setting in settings:

            data[setting.key] = setting.value

        db.close()

        self.business_name_input.setText(
            data.get("business_name", "")
        )

        self.business_cuit_input.setText(
            data.get("business_cuit", "")
        )

        self.business_address_input.setText(
            data.get("business_address", "")
        )

        self.business_phone_input.setText(
            data.get("business_phone", "")
        )

        self.ticket_footer_input.setText(
            data.get("ticket_footer", "")
        )

        self.printer_name_input.setText(
            data.get("printer_name", "")
        )

        self.printer_size_input.setText(
            data.get("printer_size", "")
        )

        self.mp_alias_input.setText(
            data.get("mp_alias", "")
        )

        self.smtp_host_input.setText(
            data.get("smtp_host", "")
        )

        self.smtp_port_input.setText(
            data.get("smtp_port", "")
        )

        self.smtp_email_input.setText(
            data.get("smtp_email", "")
        )

        self.smtp_password_input.setText(
            data.get("smtp_password", "")
        )

        qr_path = data.get(
            "payment_qr_path",
            ""
        )

        if qr_path:

            self.qr_path_label.setText(
                qr_path
            )

    # =====================================
    # SELECT QR
    # =====================================

    def select_qr(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar QR",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )

        if not file_path:
            return

        qr_folder = Path(
            "app/assets/payment_qr"
        )

        qr_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        destination = (
            qr_folder / "mercadopago_qr.png"
        )

        shutil.copy(
            file_path,
            destination
        )

        self.qr_path_label.setText(
            str(destination)
        )

    # =====================================
    # SAVE SETTINGS
    # =====================================

    def save_settings(self):

        db = SessionLocal()

        settings_map = {

            "business_name":
                self.business_name_input.text(),

            "business_cuit":
                self.business_cuit_input.text(),

            "business_address":
                self.business_address_input.text(),

            "business_phone":
                self.business_phone_input.text(),

            "ticket_footer":
                self.ticket_footer_input.text(),

            "printer_name":
                self.printer_name_input.text(),

            "printer_size":
                self.printer_size_input.text(),

            "mp_alias":
                self.mp_alias_input.text(),

            "payment_qr_path":
                self.qr_path_label.text(),

            "smtp_host":
                self.smtp_host_input.text(),

            "smtp_port":
                self.smtp_port_input.text(),

            "smtp_email":
                self.smtp_email_input.text(),

            "smtp_password":
                self.smtp_password_input.text(),
        }

        for key, value in settings_map.items():

            setting = db.query(Setting).filter(
                Setting.key == key
            ).first()

            if setting:

                setting.value = value

        db.commit()

        db.close()

        QMessageBox.information(
            self,
            "Correcto",
            "Configuración guardada"
        )