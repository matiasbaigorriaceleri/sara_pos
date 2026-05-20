from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLineEdit,
    QMessageBox,
    QFrame
)

from PySide6.QtCore import Qt

from app.database.database import SessionLocal
from app.models.product_model import Product
from app.models.cash_session_model import CashSession
from app.models.ticket_model import Ticket
from app.models.ticket_item_model import TicketItem


class SalesPage(QWidget):

    def __init__(self):
        super().__init__()

        self.selected_cart_index = None
        self.cart = []

        self.init_ui()
        self.load_products()

    def init_ui(self):

        self.setStyleSheet("""

            QWidget {
                background-color: #F4F5F7;
                color: #1E293B;
                font-family: Arial;
            }

            QLabel#title {
                font-size: 28px;
                font-weight: bold;
                color: #4A6A92;
            }

            QFrame {
                background-color: white;
                border-radius: 20px;
            }

            QListWidget {
                border: none;
                background: transparent;
                font-size: 18px;
                padding: 10px;
            }

            QListWidget::item {
                padding: 18px;
                border-radius: 10px;
                margin-bottom: 10px;
            }

            QListWidget::item:selected {
                background-color: #D8E6F5;
                color: #1E293B;
            }

            QLineEdit {
                background-color: white;
                border: 2px solid #B8C4D0;
                border-radius: 15px;
                padding: 14px;
                font-size: 18px;
                color: #1E293B;
            }

            QPushButton {
                border: none;
                border-radius: 15px;
                padding: 16px;
                font-size: 18px;
                font-weight: bold;
                color: white;
            }

        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel("Punto de Venta")
        title.setObjectName("title")
        main_layout.addWidget(title)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar producto...")
        self.search_input.returnPressed.connect(self.add_product_by_barcode)
        main_layout.addWidget(self.search_input)

        content_layout = QHBoxLayout()

        # ── Panel izquierdo: productos ──────────────────
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)

        lbl_products = QLabel("Productos")
        lbl_products.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1E293B;
        """)
        left_layout.addWidget(lbl_products)

        self.products_list = QListWidget()
        self.products_list.itemDoubleClicked.connect(self.add_product_to_cart)
        left_layout.addWidget(self.products_list)

        # ── Panel derecho: carrito ──────────────────────
        right_frame = QFrame()
        right_frame.setFixedWidth(420)
        right_layout = QVBoxLayout(right_frame)

        lbl_cart = QLabel("Carrito")
        lbl_cart.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1E293B;
        """)
        right_layout.addWidget(lbl_cart)

        self.cart_list = QListWidget()
        self.cart_list.itemClicked.connect(self.select_cart_item)
        right_layout.addWidget(self.cart_list)

        self.delete_button = QPushButton("Eliminar seleccionado")
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #FF003D;
            }
            QPushButton:hover {
                background-color: #D9043A;
            }
        """)
        self.delete_button.clicked.connect(self.remove_selected_item)
        right_layout.addWidget(self.delete_button)

        total_frame = QFrame()
        total_layout = QVBoxLayout(total_frame)

        total_label = QLabel("TOTAL")
        total_label.setStyleSheet("font-size: 14px; color: #64748B;")

        self.total_value = QLabel("$ 0")
        self.total_value.setAlignment(Qt.AlignCenter)
        self.total_value.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #4A6A92;
        """)

        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_value)
        right_layout.addWidget(total_frame)

        self.charge_button = QPushButton("COBRAR")
        self.charge_button.setStyleSheet("""
            QPushButton {
                background-color: #4A6A92;
            }
            QPushButton:hover {
                background-color: #3D5A80;
            }
        """)
        self.charge_button.clicked.connect(self.charge_sale)
        right_layout.addWidget(self.charge_button)

        content_layout.addWidget(left_frame, 3)
        content_layout.addWidget(right_frame, 1)
        main_layout.addLayout(content_layout)

    def show_message(self, title, message):

        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QLabel {
                color: #1E293B;
                font-size: 16px;
                font-weight: bold;
                min-width: 320px;
            }
            QPushButton {
                background-color: #4A6A92;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                min-width: 90px;
                min-height: 35px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3D5A80;
            }
        """)
        msg.exec()

    def load_products(self):

        self.products_list.clear()

        db = SessionLocal()

        try:
            products = db.query(Product).filter(
                Product.is_active == True
            ).all()

            for product in products:
                item_text = f"{product.name}   $ {int(product.price)}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, product)
                self.products_list.addItem(item)

        finally:
            db.close()

    def add_product_to_cart(self, item):

        product = item.data(Qt.UserRole)

        # Validar stock disponible
        db = SessionLocal()
        try:
            db_product = db.query(Product).filter(
                Product.id == product.id
            ).first()

            if not db_product or db_product.stock <= 0:
                self.show_message("Sin stock", f"{product.name} no tiene stock disponible")
                return

            # Verificar si ya está en el carrito
            for cart_item in self.cart:
                if cart_item["id"] == product.id:
                    if cart_item["quantity"] >= db_product.stock:
                        self.show_message(
                            "Sin stock",
                            f"{product.name} solo tiene {int(db_product.stock)} unidades disponibles"
                        )
                        return
                    cart_item["quantity"] += 1
                    self.refresh_cart()
                    return

            self.cart.append({
                "id": product.id,
                "name": product.name,
                "price": float(product.price),
                "quantity": 1
            })

            self.refresh_cart()

        finally:
            db.close()

    def add_product_by_barcode(self):

        barcode = self.search_input.text().strip()

        if not barcode:
            return

        db = SessionLocal()

        try:
            product = db.query(Product).filter(
                Product.barcode == barcode,
                Product.is_active == True
            ).first()

            if not product:
                self.show_message("Error", "Producto no encontrado")
                return

            if product.stock <= 0:
                self.show_message("Sin stock", f"{product.name} no tiene stock disponible")
                self.search_input.clear()
                return

            for cart_item in self.cart:
                if cart_item["id"] == product.id:
                    if cart_item["quantity"] >= product.stock:
                        self.show_message(
                            "Sin stock",
                            f"{product.name} solo tiene {int(product.stock)} unidades disponibles"
                        )
                        self.search_input.clear()
                        return
                    cart_item["quantity"] += 1
                    self.refresh_cart()
                    self.search_input.clear()
                    return

            self.cart.append({
                "id": product.id,
                "name": product.name,
                "price": float(product.price),
                "quantity": 1
            })

            self.refresh_cart()
            self.search_input.clear()

        finally:
            db.close()

    def refresh_cart(self):

        self.cart_list.clear()

        total = 0

        for item in self.cart:
            subtotal = item["price"] * item["quantity"]
            total += subtotal
            text = f"{item['name']} x{item['quantity']}   $ {int(subtotal)}"
            list_item = QListWidgetItem(text)
            self.cart_list.addItem(list_item)

        self.total_value.setText(f"$ {int(total)}")

    def select_cart_item(self, item):

        self.selected_cart_index = self.cart_list.row(item)

    def remove_selected_item(self):

        if self.selected_cart_index is None:
            return

        item = self.cart[self.selected_cart_index]

        if item["quantity"] > 1:
            item["quantity"] -= 1
        else:
            self.cart.pop(self.selected_cart_index)

        self.selected_cart_index = None
        self.refresh_cart()

    def charge_sale(self):

        if not self.cart:
            self.show_message("Error", "Debe agregar productos")
            return

        db = SessionLocal()

        try:

            # Validar caja abierta
            cash_session = db.query(CashSession).filter(
                CashSession.is_open == True
            ).first()

            if not cash_session:
                self.show_message("Error", "Debe abrir una caja antes de vender")
                return

            # Validar stock antes de cobrar
            for item in self.cart:
                product = db.query(Product).filter(
                    Product.id == item["id"]
                ).first()
                if not product:
                    self.show_message("Error", f"Producto {item['name']} no encontrado")
                    return
                if product.stock < item["quantity"]:
                    self.show_message(
                        "Stock insuficiente",
                        f"{product.name} tiene solo {int(product.stock)} unidades disponibles"
                    )
                    return

            # Calcular total
            total = sum(
                item["price"] * item["quantity"]
                for item in self.cart
            )

            # Crear ticket
            ticket = Ticket(
                total=total,
                username=cash_session.username,
                cash_session_id=cash_session.id
            )

            db.add(ticket)
            db.flush()

            # Crear items y descontar stock
            for item in self.cart:

                subtotal = item["price"] * item["quantity"]

                ticket_item = TicketItem(
                    ticket_id=ticket.id,
                    product_id=item["id"],
                    quantity=item["quantity"],
                    price=item["price"],
                    subtotal=subtotal
                )

                db.add(ticket_item)

                # Descontar stock
                product = db.query(Product).filter(
                    Product.id == item["id"]
                ).first()

                product.stock -= item["quantity"]

            db.commit()

            self.show_message(
                "Venta exitosa",
                f"Venta registrada correctamente\nTotal: $ {int(total)}"
            )

            self.cart.clear()
            self.refresh_cart()
            self.load_products()

        except Exception as e:
            db.rollback()
            self.show_message("Error", f"Error al registrar venta: {str(e)}")

        finally:
            db.close()