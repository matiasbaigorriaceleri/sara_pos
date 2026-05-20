from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
)

from PySide6.QtCore import Qt

from app.assets.themes.theme import (
    PRIMARY_COLOR,
    BUTTON_STYLE,
)

from app.services.ticket_service import (
    TicketService
)


class QRPaymentDialog(QDialog):

    def __init__(
        self,
        total,
        cart,
        username
    ):
        super().__init__()

        self.total = total

        self.cart = cart

        self.username = username

        self.setWindowTitle(
            "Cobro QR fijo"
        )

        self.setFixedSize(420, 620)

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

        title = QLabel(
            "Cobro con QR fijo"
        )

        title.setAlignment(Qt.AlignCenter)

        title.setStyleSheet(f"""
            font-size: 28px;
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

        total_label.setAlignment(
            Qt.AlignCenter
        )

        total_label.setStyleSheet("""
            font-size: 34px;
            font-weight: bold;
            color: #1E293B;
        """)

        layout.addWidget(total_label)

        # =====================================
        # QR PLACEHOLDER
        # =====================================

        qr_label = QLabel()

        qr_label.setFixedSize(260, 260)

        qr_label.setAlignment(Qt.AlignCenter)

        qr_label.setStyleSheet("""
            background-color: #F1F5F9;
            border: 2px dashed #CBD5E1;
            border-radius: 20px;
            font-size: 18px;
            color: #64748B;
        """)

        qr_label.setText(
            "QR MercadoPago"
        )

        layout.addWidget(
            qr_label,
            alignment=Qt.AlignCenter
        )

        # =====================================
        # INFO
        # =====================================

        info = QLabel(
            "El cliente debe escanear\n"
            "el QR y realizar el pago"
        )

        info.setAlignment(Qt.AlignCenter)

        info.setStyleSheet("""
            font-size: 16px;
            color: #64748B;
        """)

        layout.addWidget(info)

        # =====================================
        # PRINT BUTTON
        # =====================================

        print_button = QPushButton(
            "Imprimir ticket"
        )

        print_button.setMinimumHeight(60)

        print_button.setStyleSheet(
            BUTTON_STYLE
        )

        print_button.clicked.connect(
            self.print_ticket
        )

        layout.addWidget(print_button)

        # =====================================
        # CLOSE BUTTON
        # =====================================

        close_button = QPushButton(
            "Cancelar"
        )

        close_button.setMinimumHeight(55)

        close_button.setStyleSheet("""
            QPushButton {
                background-color: #E2E8F0;
                color: #1E293B;
                border-radius: 14px;
                font-size: 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #CBD5E1;
            }
        """)

        close_button.clicked.connect(
            self.reject
        )

        layout.addWidget(close_button)

        self.setLayout(layout)

    # =====================================
    # PRINT TICKET
    # =====================================

    def print_ticket(self):

        ticket_text = (
            TicketService.generate_ticket_text(
                self.cart,
                self.total,
                self.username
            )
        )

        ticket_path = (
            TicketService.save_ticket_file(
                ticket_text
            )
        )

        printed = (
            TicketService.print_ticket(
                ticket_path
            )
        )

        if printed:

            QMessageBox.information(
                self,
                "Correcto",
                "Ticket impreso correctamente"
            )

            self.accept()

        else:

            QMessageBox.warning(
                self,
                "Error",
                "No pudo imprimirse"
            )