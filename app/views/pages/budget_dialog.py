from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
    QMessageBox,
)

from PySide6.QtCore import Qt


class BudgetDialog(QDialog):

    def __init__(self, total, ticket_id, cart, parent=None, on_confirm=None):
        super().__init__(parent)

        self.total = total
        self.ticket_id = ticket_id
        self.cart = cart
        self.on_confirm = on_confirm

        self.setWindowTitle("Enviar presupuesto")
        self.setFixedWidth(440)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog { background-color: #F4F5F7; }
            QLabel { background-color: transparent; }
            QLabel#title { font-size: 18px; font-weight: bold; color: #1E293B; }
            QLabel#total_label { font-size: 13px; color: #64748B; }
            QLabel#total_value { font-size: 38px; font-weight: bold; color: #4A6A92; }
            QLabel#hint { font-size: 13px; color: #64748B; }
            QFrame#card { background-color: white; border-radius: 16px; }
            QFrame#divider { background-color: #E2E8F0; max-height: 1px; }
            QLineEdit {
                background-color: #F8FAFC;
                border: 2px solid #B8C4D0;
                border-radius: 10px;
                padding: 12px;
                font-size: 15px;
                color: #1E293B;
            }
            QLineEdit:focus { border: 2px solid #4A6A92; }
            QPushButton#send_btn {
                background-color: #4A6A92; color: white; border: none;
                border-radius: 12px; padding: 16px; font-size: 16px; font-weight: bold;
            }
            QPushButton#send_btn:hover { background-color: #3D5A80; }
            QPushButton#send_btn:disabled { background-color: #B8C4D0; }
            QPushButton#cancel_btn {
                background-color: transparent; color: #94A3B8;
                border: none; font-size: 13px; padding: 8px;
            }
            QPushButton#cancel_btn:hover { color: #64748B; }
        """)

        self.init_ui()

    def init_ui(self):

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(0)

        title = QLabel("Enviar presupuesto por email")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        card_layout.addSpacing(16)

        total_lbl = QLabel("Total del presupuesto")
        total_lbl.setObjectName("total_label")
        total_lbl.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(total_lbl)

        card_layout.addSpacing(4)

        total_val = QLabel(f"$ {int(self.total)}")
        total_val.setObjectName("total_value")
        total_val.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(total_val)

        card_layout.addSpacing(20)

        div = QFrame()
        div.setObjectName("divider")
        div.setFixedHeight(1)
        card_layout.addWidget(div)

        card_layout.addSpacing(20)

        hint = QLabel("Email del cliente")
        hint.setObjectName("hint")
        hint.setAlignment(Qt.AlignLeft)
        card_layout.addWidget(hint)

        card_layout.addSpacing(6)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("cliente@ejemplo.com")
        self.email_input.setMinimumHeight(48)
        card_layout.addWidget(self.email_input)

        card_layout.addSpacing(8)

        layout.addWidget(card)
        layout.addSpacing(4)

        self.send_btn = QPushButton("  Enviar presupuesto")
        self.send_btn.setObjectName("send_btn")
        self.send_btn.setMinimumHeight(52)
        self.send_btn.clicked.connect(self.send_budget)
        layout.addWidget(self.send_btn)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn, alignment=Qt.AlignCenter)

    def send_budget(self):

        email = self.email_input.text().strip()

        if not email or "@" not in email:
            self.show_message("Error", "Ingresá un email válido")
            return

        self.send_btn.setText("Enviando...")
        self.send_btn.setEnabled(False)

        # Registrar la venta recién aquí
        ticket_id = None
        cart_snapshot = self.cart

        if self.on_confirm:
            result = self.on_confirm(email)
            if result is None:
                self.send_btn.setText("  Enviar presupuesto")
                self.send_btn.setEnabled(True)
                return
            ticket_id, cart_snapshot, email = result

        from app.utils.mail_sender import send_budget_email
        success, msg = send_budget_email(
            to_email=email,
            ticket_id=ticket_id,
            cart=cart_snapshot,
            total=self.total
        )

        self.send_btn.setText("  Enviar presupuesto")
        self.send_btn.setEnabled(True)

        self.show_message(
            "Presupuesto enviado" if success else "Error",
            msg
        )

        if success:
            self.accept()

    def show_message(self, title, message):

        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(message)
        box.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1E293B; font-size: 15px; font-weight: bold; min-width: 280px; }
            QPushButton {
                background-color: #4A6A92; color: white; border: none;
                border-radius: 10px; padding: 10px 20px; min-width: 80px;
                min-height: 32px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #3D5A80; }
        """)
        box.exec()