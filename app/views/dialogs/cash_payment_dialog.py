
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QLineEdit,
    QMessageBox,
    QHBoxLayout,
)

from app.assets.themes.theme import (
    PRIMARY_COLOR,
    INPUT_STYLE,
    BUTTON_STYLE,
)


class CashPaymentDialog(QDialog):

    def __init__(self, total):
        super().__init__()

        self.total = total

        self.payment_confirmed = False

        self.setWindowTitle("Cobro en efectivo")

        self.setFixedSize(450, 550)

        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)

        layout = QVBoxLayout()

        layout.setContentsMargins(
            30,
            30,
            30,
            30
        )

        layout.setSpacing(20)

        # =====================================
        # TITLE
        # =====================================

        title = QLabel("Cobro en efectivo")

        title.setStyleSheet(f"""
            font-size: 30px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
        """)

        layout.addWidget(title)

        # =====================================
        # TOTAL
        # =====================================

        total_label = QLabel(
            f"TOTAL: $ {self.total}"
        )

        total_label.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
        """)

        layout.addWidget(total_label)

        # =====================================
        # RECEIVED
        # =====================================

        received_label = QLabel(
            "Dinero recibido"
        )

        received_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
        """)

        layout.addWidget(received_label)

        self.received_input = QLineEdit()

        self.received_input.setPlaceholderText(
            "Ingrese el monto recibido"
        )

        self.received_input.setMinimumHeight(50)

        self.received_input.setStyleSheet(INPUT_STYLE)

        self.received_input.textChanged.connect(
            self.calculate_change
        )

        layout.addWidget(self.received_input)

        # =====================================
        # CHANGE
        # =====================================

        change_title = QLabel("VUELTO")

        change_title.setStyleSheet("""
            font-size: 16px;
            color: #666;
        """)

        layout.addWidget(change_title)

        self.change_label = QLabel("$ 0")

        self.change_label.setStyleSheet(f"""
            font-size: 42px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
        """)

        layout.addWidget(self.change_label)

        layout.addStretch()

        # =====================================
        # BUTTONS
        # =====================================

        buttons_layout = QHBoxLayout()

        cancel_button = QPushButton("Cancelar")

        cancel_button.setMinimumHeight(55)

        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #E5E7EB;
                color: black;
                border-radius: 14px;
                font-size: 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #D1D5DB;
            }
        """)

        cancel_button.clicked.connect(
            self.reject
        )

        confirm_button = QPushButton(
            "Confirmar pago"
        )

        confirm_button.setMinimumHeight(55)

        confirm_button.setStyleSheet(BUTTON_STYLE)

        confirm_button.clicked.connect(
            self.confirm_payment
        )

        buttons_layout.addWidget(cancel_button)

        buttons_layout.addWidget(confirm_button)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    # =====================================
    # CALCULATE CHANGE
    # =====================================

    def calculate_change(self):

        text = self.received_input.text()

        if not text:

            self.change_label.setText("$ 0")

            return

        try:

            received = int(text)

            change = received - self.total

            self.change_label.setText(
                f"$ {change}"
            )

        except:

            self.change_label.setText("$ 0")

    # =====================================
    # CONFIRM PAYMENT
    # =====================================

    def confirm_payment(self):

        text = self.received_input.text()

        if not text:

            QMessageBox.warning(
                self,
                "Error",
                "Ingrese el dinero recibido"
            )

            return

        try:

            received = int(text)

        except:

            QMessageBox.warning(
                self,
                "Error",
                "Monto inválido"
            )

            return

        if received < self.total:

            QMessageBox.warning(
                self,
                "Error",
                "El dinero recibido es menor al total"
            )

            return

        self.payment_confirmed = True

        self.accept()
