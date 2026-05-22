from pathlib import Path
import shutil

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
)

from app.assets.themes.theme import PRIMARY_COLOR, INPUT_STYLE, BUTTON_STYLE
from app.database.database import SessionLocal
from app.models.settings_model import Setting
from app.models.user_model import User
from app.components.collapsible_section import CollapsibleSection


class SettingsPage(QWidget):

    def __init__(self):
        super().__init__()

        self.selected_user_id = None

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
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

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

        # ── Guardar configuración ─────────────────────
        save_button = QPushButton("Guardar configuración")
        save_button.setMinimumHeight(60)
        save_button.setStyleSheet(BUTTON_STYLE)
        save_button.clicked.connect(self.save_settings)
        content_layout.addWidget(save_button)

        # ── ABM Usuarios ──────────────────────────────
        users_widget = QWidget()
        users_layout = QVBoxLayout()
        users_layout.setSpacing(15)

        # Formulario usuarios
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
        self.user_role_combo = QComboBox()
        self.user_role_combo.addItems(["ADMIN", "ANALISTA"])
        self.user_role_combo.setMinimumHeight(50)
        self.user_role_combo.setStyleSheet("""
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
        """)

        BLUE = "QPushButton { background-color: #4A6A92; color: white; border: none; border-radius: 12px; font-size: 14px; font-weight: bold; padding: 12px; } QPushButton:hover { background-color: #3D5A80; }"
        RED = "QPushButton { background-color: #FF003D; color: white; border: none; border-radius: 12px; font-size: 14px; font-weight: bold; padding: 12px; } QPushButton:hover { background-color: #D90429; }"

        btn_save_user = QPushButton("Crear usuario")
        btn_save_user.setMinimumHeight(50)
        btn_save_user.setStyleSheet(BLUE)
        btn_save_user.clicked.connect(self.save_user)

        btn_update_user = QPushButton("Actualizar")
        btn_update_user.setMinimumHeight(50)
        btn_update_user.setStyleSheet(BLUE)
        btn_update_user.clicked.connect(self.update_user)

        btn_toggle_user = QPushButton("Activar / Desactivar")
        btn_toggle_user.setMinimumHeight(50)
        btn_toggle_user.setStyleSheet(RED)
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

        # Tabla usuarios
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "Usuario", "Rol", "Estado"
        ])
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

    def create_input(self, placeholder):
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setMinimumHeight(50)
        input_field.setStyleSheet(INPUT_STYLE)
        return input_field

    # ── Configuración ─────────────────────────────────

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
            self, "Seleccionar QR", "", "Images (*.png *.jpg *.jpeg)"
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
                setting = db.query(Setting).filter(Setting.key == key).first()
                if setting:
                    setting.value = value
                else:
                    db.add(Setting(key=key, value=value))

            db.commit()

        except Exception as e:
            db.rollback()
            self.show_message("Error", f"Error al guardar: {str(e)}")
            return
        finally:
            db.close()

        self.show_message("Correcto", "Configuración guardada correctamente")

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
            from PySide6.QtCore import Qt
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
                password=password,
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
                user.password = password

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