
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QMessageBox,
)

from PySide6.QtCore import Qt

from app.assets.themes.theme import (
    PRIMARY_COLOR,
    BACKGROUND_COLOR,
    INPUT_STYLE,
    BUTTON_STYLE,
)

from app.database.database import SessionLocal

from app.models.product_model import Product
from app.models.cash_session_model import CashSession


class SalesPage(QWidget):

    def __init__(self):
        super().__init__()

        self.cart = {}

        self.setup_ui()
        self.load_products()

    def setup_ui(self):

        self.setStyleSheet(f"""
            background-color: {BACKGROUND_COLOR};
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        title = QLabel("Punto de Venta")
        title.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
        """)
        main_layout.addWidget(title)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar producto...")
        self.search_input.setMinimumHeight(42)
        self.search_input.setStyleSheet(INPUT_STYLE)
        self.search_input.textChanged.connect(self.filter_products)
        self.search_input.returnPressed.connect(self.add_selected_product)

        main_layout.addWidget(self.search_input)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(14)

        products_frame = QFrame()
        products_frame.setStyleSheet("""
            background-color: white;
            border-radius: 18px;
        """)

        products_layout = QVBoxLayout()
        products_layout.setContentsMargins(18, 18, 18, 18)

        products_title = QLabel("Productos")
        products_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #1E293B;
        """)

        self.products_list = QListWidget()
        self.products_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
                font-size: 16px;
                color: #334155;
                outline: none;
            }

            QListWidget::item {
                padding: 14px;
                border-radius: 10px;
                margin-bottom: 4px;
            }

            QListWidget::item:hover {
                background-color: #F1F5F9;
            }

            QListWidget::item:selected {
                background-color: #DBEAFE;
                color: #1E293B;
                font-weight: bold;
            }
        """)

        self.products_list.itemDoubleClicked.connect(self.add_to_cart)

        products_layout.addWidget(products_title)
        products_layout.addWidget(self.products_list)

        products_frame.setLayout(products_layout)

        cart_frame = QFrame()
        cart_frame.setFixedWidth(340)
        cart_frame.setStyleSheet("""
            background-color: white;
            border-radius: 18px;
        """)

        cart_layout = QVBoxLayout()
        cart_layout.setContentsMargins(18, 18, 18, 18)

        cart_title = QLabel("Carrito")
        cart_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #1E293B;
        """)

        self.cart_list = QListWidget()
        self.cart_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
                font-size: 15px;
                color: #334155;
                outline: none;
            }

            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #E2E8F0;
            }

            QListWidget::item:hover {
                background-color: #F8FAFC;
            }

            QListWidget::item:selected {
                background-color: #DBEAFE;
                color: #1E293B;
                font-weight: bold;
                border-radius: 8px;
            }
        """)

        cart_layout.addWidget(cart_title)
        cart_layout.addWidget(self.cart_list)

        delete_button = QPushButton("Eliminar seleccionado")
        delete_button.setMinimumHeight(48)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #FF003D;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #D90429;
            }
        """)
        delete_button.clicked.connect(self.remove_selected)

        cart_layout.addWidget(delete_button)

        total_frame = QFrame()
        total_frame.setMinimumHeight(90)
        total_frame.setStyleSheet("""
            background-color: #F1F5F9;
            border-radius: 16px;
        """)

        total_layout = QVBoxLayout()

        total_label = QLabel("TOTAL")
        total_label.setStyleSheet("""
            font-size: 14px;
            color: #64748B;
        """)

        self.total_value = QLabel("$ 0")
        self.total_value.setStyleSheet(f"""
            font-size: 30px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
        """)
        self.total_value.setAlignment(Qt.AlignCenter)

        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_value)

        total_frame.setLayout(total_layout)
        cart_layout.addWidget(total_frame)

        charge_button = QPushButton("COBRAR")
        charge_button.setMinimumHeight(50)
        charge_button.setStyleSheet(BUTTON_STYLE)

        cart_layout.addWidget(charge_button)

        cart_frame.setLayout(cart_layout)

        content_layout.addWidget(products_frame, 3)
        content_layout.addWidget(cart_frame, 1)

        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)

    def load_products(self):

        self.products_list.clear()

        db = SessionLocal()

        self.products = db.query(Product).filter(
            Product.is_active == True
        ).all()

        db.close()

        for product in self.products:

            item = QListWidgetItem(
                f"{product.name}    $ {product.price}"
            )

            item.setData(Qt.UserRole, product)

            self.products_list.addItem(item)

        if self.products_list.count() > 0:
            self.products_list.setCurrentRow(0)

    def filter_products(self):

        text = self.search_input.text().lower()

        visible_items = []

        for i in range(self.products_list.count()):

            item = self.products_list.item(i)

            visible = text in item.text().lower()

            item.setHidden(not visible)

            if visible:
                visible_items.append(i)

        if visible_items:
            self.products_list.setCurrentRow(visible_items[0])

    def add_selected_product(self):

        current_item = self.products_list.currentItem()

        if current_item:
            self.add_to_cart(current_item)

    def add_to_cart(self, item):

        db = SessionLocal()

        cash_session = db.query(CashSession).filter(
            CashSession.is_open == True
        ).first()

        db.close()

        if not cash_session:

            QMessageBox.warning(
                self,
                "Caja cerrada",
                "Debe abrir una caja antes de vender"
            )

            return

        product = item.data(Qt.UserRole)
        product_id = product.id

        if product_id in self.cart:
            self.cart[product_id]["quantity"] += 1
        else:
            self.cart[product_id] = {
                "product": product,
                "quantity": 1
            }

        self.refresh_cart()

    def refresh_cart(self):

        self.cart_list.clear()

        for item_data in self.cart.values():

            product = item_data["product"]
            quantity = item_data["quantity"]
            subtotal = product.price * quantity

            self.cart_list.addItem(
                f"{product.name} x{quantity}    $ {subtotal}"
            )

        self.update_total()

    def remove_selected(self):

        current_row = self.cart_list.currentRow()

        if current_row < 0:
            return

        keys = list(self.cart.keys())
        product_id = keys[current_row]

        self.cart[product_id]["quantity"] -= 1

        if self.cart[product_id]["quantity"] <= 0:
            del self.cart[product_id]

        self.refresh_cart()

    def update_total(self):

        total = 0

        for item_data in self.cart.values():

            product = item_data["product"]
            quantity = item_data["quantity"]

            total += product.price * quantity

        self.total_value.setText(f"$ {total}")
