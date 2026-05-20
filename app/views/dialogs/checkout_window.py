from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
)

from app.assets.themes.theme import (
    PRIMARY_COLOR,
    BUTTON_STYLE,
)

from app.views.dialogs.cash_payment_dialog import (
    CashPaymentDialog
)

from app.database.database import SessionLocal

from app.models.ticket_model import Ticket

from app.models.product_model import Product

from app.models.cash_session_model import (
    CashSession
)

from app.services.ticket_service import (
    TicketService
)


class CheckoutWindow(QDialog):

    def __init__(
        self,
        total,
        cart,
        username,
        sales_page,
        sales_detail_page
    ):
        super().__init__()

        self.total = total

        self.cart = cart

        self.username = username

        self.sales_page = sales_page

        self.sales_detail_page = sales_detail_page

        self.setWindowTitle("Cobrar venta")

        self.setFixedSize(450, 500)

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

        title = QLabel("Cobrar Venta")

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
            font-size: 38px;
            font-weight: bold;
            margin-bottom: 20px;
        """)

        layout.addWidget(total_label)

        # =====================================
        # CASH BUTTON
        # =====================================

        cash_button = QPushButton(
            "Cobrar en efectivo"
        )

        cash_button.setMinimumHeight(70)

        cash_button.setStyleSheet(
            BUTTON_STYLE
        )

        cash_button.clicked.connect(
            self.open_cash_payment
        )

        layout.addWidget(cash_button)

        # =====================================
        # MP BUTTON
        # =====================================

        mp_button = QPushButton(
            "Cobrar con Mercado Pago QR"
        )

        mp_button.setMinimumHeight(70)

        mp_button.setStyleSheet(
            BUTTON_STYLE
        )

        layout.addWidget(mp_button)

        # =====================================
        # QR BUTTON
        # =====================================

        qr_button = QPushButton(
            "Cobrar con QR fijo"
        )

        qr_button.setMinimumHeight(70)

        qr_button.setStyleSheet(
            BUTTON_STYLE
        )

        layout.addWidget(qr_button)

        layout.addStretch()

        self.setLayout(layout)

    # =====================================
    # OPEN CASH PAYMENT
    # =====================================

    def open_cash_payment(self):

        dialog = CashPaymentDialog(
            self.total
        )

        result = dialog.exec()

        if result and dialog.payment_confirmed:

            self.save_ticket()

            self.discount_stock()

            # =====================================
            # GENERATE TICKET
            # =====================================

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
                    "Ticket generado",
                    (
                        "Ticket generado e impreso correctamente\n\n"
                        f"Archivo:\n{ticket_path}"
                    )
                )

            else:

                QMessageBox.warning(
                    self,
                    "Error impresión",
                    (
                        "El ticket fue generado pero no pudo imprimirse"
                    )
                )

            self.sales_page.clear_cart()

            self.sales_page.load_products()

            self.sales_page.refresh_products_list()

            self.sales_detail_page.refresh_data()

            self.accept()

    # =====================================
    # SAVE TICKET
    # =====================================

    def save_ticket(self):

        db = SessionLocal()

        cash_session = db.query(CashSession).filter(
            CashSession.is_open == True
        ).first()

        products_text = ""

        for product_name, data in self.cart.items():

            quantity = data["quantity"]

            subtotal = (
                data["price"] * quantity
            )

            products_text += (
                f"{product_name} "
                f"x{quantity} "
                f"$ {subtotal} | "
            )

        ticket = Ticket(
            cash_session_id=(
                cash_session.id
                if cash_session else None
            ),
            username=self.username,
            products=products_text,
            total=self.total
        )

        db.add(ticket)

        db.commit()

        db.close()

    # =====================================
    # DISCOUNT STOCK
    # =====================================

    def discount_stock(self):

        db = SessionLocal()

        for product_name, data in self.cart.items():

            quantity = data["quantity"]

            product = db.query(Product).filter(
                Product.name == product_name
            ).first()

            if product:

                product.stock -= quantity

                if product.stock < 0:

                    product.stock = 0

        db.commit()

        db.close()
