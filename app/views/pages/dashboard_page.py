from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QListWidget,
)

from app.assets.themes.theme import (
    PRIMARY_COLOR,
)

from app.database.database import SessionLocal

from app.models.ticket_model import Ticket

from app.models.product_model import Product

from app.models.cash_session_model import (
    CashSession
)


class DashboardPage(QWidget):

    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout()

        main_layout.setSpacing(20)

        # =====================================
        # TITLE
        # =====================================

        title = QLabel("Dashboard")

        title.setStyleSheet(f"""
            font-size: 34px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
        """)

        main_layout.addWidget(title)

        # =====================================
        # LOAD DATA
        # =====================================

        db = SessionLocal()

        tickets = db.query(Ticket).all()

        products = db.query(Product).filter(
            Product.is_active == True
        ).all()

        cash_session = db.query(CashSession).filter(
            CashSession.is_open == True
        ).first()

        db.close()

        total_sales = sum(
            ticket.total for ticket in tickets
        )

        total_tickets = len(tickets)

        total_products = len(products)

        low_stock = [
            product
            for product in products
            if product.stock <= product.minimum_stock
        ]

        # =====================================
        # CARDS
        # =====================================

        cards_layout = QHBoxLayout()

        sales_card = self.create_card(
            "Ventas Totales",
            f"$ {total_sales}"
        )

        tickets_card = self.create_card(
            "Tickets",
            str(total_tickets)
        )

        products_card = self.create_card(
            "Productos",
            str(total_products)
        )

        if cash_session:

            cash_text = (
                f"$ {cash_session.opening_amount}"
            )

        else:

            cash_text = "Caja cerrada"

        cash_card = self.create_card(
            "Caja Actual",
            cash_text
        )

        cards_layout.addWidget(sales_card)

        cards_layout.addWidget(tickets_card)

        cards_layout.addWidget(products_card)

        cards_layout.addWidget(cash_card)

        main_layout.addLayout(cards_layout)

        # =====================================
        # BOTTOM SECTION
        # =====================================

        bottom_layout = QHBoxLayout()

        # =====================================
        # LAST SALES
        # =====================================

        sales_frame = QFrame()

        sales_frame.setStyleSheet("""
            background-color: white;
            border-radius: 20px;
        """)

        sales_layout = QVBoxLayout()

        sales_title = QLabel("Últimas ventas")

        sales_title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1E293B;
        """)

        sales_layout.addWidget(sales_title)

        sales_list = QListWidget()

        sales_list.setStyleSheet("""
            QListWidget {
                border: none;
                background: transparent;
                font-size: 16px;
                color: #1E293B;
            }

            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #E5E7EB;
            }
        """)

        last_tickets = tickets[-10:]

        last_tickets.reverse()

        for ticket in last_tickets:

            sales_list.addItem(
                f"{ticket.username} - "
                f"$ {ticket.total}"
            )

        sales_layout.addWidget(sales_list)

        sales_frame.setLayout(sales_layout)

        # =====================================
        # LOW STOCK
        # =====================================

        stock_frame = QFrame()

        stock_frame.setStyleSheet("""
            background-color: white;
            border-radius: 20px;
        """)

        stock_layout = QVBoxLayout()

        stock_title = QLabel(
            "Productos bajo stock"
        )

        stock_title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1E293B;
        """)

        stock_layout.addWidget(stock_title)

        stock_list = QListWidget()

        stock_list.setStyleSheet("""
            QListWidget {
                border: none;
                background: transparent;
                font-size: 16px;
                color: #1E293B;
            }

            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #E5E7EB;
            }
        """)

        if low_stock:

            for product in low_stock:

                stock_list.addItem(
                    f"{product.name} | "
                    f"Stock: {product.stock}"
                )

        else:

            stock_list.addItem(
                "Sin alertas de stock"
            )

        stock_layout.addWidget(stock_list)

        stock_frame.setLayout(stock_layout)

        bottom_layout.addWidget(sales_frame)

        bottom_layout.addWidget(stock_frame)

        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

    # =====================================
    # CREATE CARD
    # =====================================

    def create_card(self, title, value):

        frame = QFrame()

        frame.setMinimumHeight(160)

        frame.setStyleSheet("""
            background-color: white;
            border-radius: 20px;
        """)

        layout = QVBoxLayout()

        layout.setContentsMargins(
            20,
            20,
            20,
            20
        )

        title_label = QLabel(title)

        title_label.setStyleSheet("""
            font-size: 18px;
            color: #64748B;
        """)

        value_label = QLabel(value)

        value_label.setStyleSheet(f"""
            font-size: 34px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
        """)

        layout.addWidget(title_label)

        layout.addStretch()

        layout.addWidget(value_label)

        frame.setLayout(layout)

        return frame
