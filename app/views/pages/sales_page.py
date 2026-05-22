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
    QFrame,
    QDialog,
    QCompleter,
)

from PySide6.QtCore import Qt, QStringListModel

from app.database.database import SessionLocal
from app.models.product_model import Product
from app.models.cash_session_model import CashSession
from app.models.ticket_model import Ticket
from app.models.ticket_item_model import TicketItem
from app.models.client_model import Client
from app.views.pages.payment_dialog import PaymentDialog
from app.views.pages.transfer_dialog import TransferDialog
from app.views.pages.budget_dialog import BudgetDialog
from app.printers.ticket_printer import print_ticket


class SalesPage(QWidget):

    def __init__(self):
        super().__init__()
        self.selected_cart_index = None
        self.cart = []
        self.current_client = None  # None = Consumidor Final
        self.current_discount = 0.0
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
        main_layout.setSpacing(10)

        title = QLabel("Punto de Venta")
        title.setObjectName("title")
        main_layout.addWidget(title)

        # ── Buscador de productos ─────────────────────
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar producto por nombre o barcode...")
        self.search_input.returnPressed.connect(self.add_product_by_barcode)
        main_layout.addWidget(self.search_input)

        # ── Selector de cliente ───────────────────────
        client_row = QHBoxLayout()
        client_row.setSpacing(10)

        self.client_input = QLineEdit()
        self.client_input.setPlaceholderText("Cliente (dejar vacío = Consumidor Final)")
        self.client_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #B8C4D0;
                border-radius: 15px;
                padding: 12px 16px;
                font-size: 15px;
                color: #1E293B;
            }
            QLineEdit:focus { border: 2px solid #4A6A92; }
        """)
        self.client_input.textChanged.connect(self.on_client_input_changed)
        self.client_input.returnPressed.connect(self.search_client)

        btn_search_client = QPushButton("Buscar cliente")
        btn_search_client.setFixedHeight(48)
        btn_search_client.setStyleSheet("""
            QPushButton {
                background-color: #4A6A92;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover { background-color: #3D5A80; }
        """)
        btn_search_client.clicked.connect(self.search_client)

        btn_clear_client = QPushButton("Consumidor Final")
        btn_clear_client.setFixedHeight(48)
        btn_clear_client.setStyleSheet("""
            QPushButton {
                background-color: #64748B;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        btn_clear_client.clicked.connect(self.clear_client)

        self.client_info_label = QLabel("Cliente: Consumidor Final")
        self.client_info_label.setStyleSheet("""
            font-size: 14px;
            color: #64748B;
            font-weight: bold;
            background: transparent;
            border: none;
        """)

        client_row.addWidget(self.client_input, 3)
        client_row.addWidget(btn_search_client)
        client_row.addWidget(btn_clear_client)
        client_row.addWidget(self.client_info_label, 2)
        main_layout.addLayout(client_row)

        content_layout = QHBoxLayout()

        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)

        lbl_products = QLabel("Productos")
        lbl_products.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E293B;")
        left_layout.addWidget(lbl_products)

        self.products_list = QListWidget()
        self.products_list.itemDoubleClicked.connect(self.add_product_to_cart)
        left_layout.addWidget(self.products_list)

        right_frame = QFrame()
        right_frame.setFixedWidth(420)
        right_layout = QVBoxLayout(right_frame)

        lbl_cart = QLabel("Carrito")
        lbl_cart.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E293B;")
        right_layout.addWidget(lbl_cart)

        self.cart_list = QListWidget()
        self.cart_list.itemClicked.connect(self.select_cart_item)
        right_layout.addWidget(self.cart_list)

        self.delete_button = QPushButton("Eliminar seleccionado")
        self.delete_button.setStyleSheet("""
            QPushButton { background-color: #FF003D; }
            QPushButton:hover { background-color: #D9043A; }
        """)
        self.delete_button.clicked.connect(self.remove_selected_item)
        right_layout.addWidget(self.delete_button)

        total_frame = QFrame()
        total_layout = QVBoxLayout(total_frame)
        total_layout.setSpacing(2)

        total_label = QLabel("TOTAL")
        total_label.setStyleSheet("font-size: 14px; color: #64748B;")

        self.total_value = QLabel("$ 0")
        self.total_value.setAlignment(Qt.AlignCenter)
        self.total_value.setStyleSheet("font-size: 28px; font-weight: bold; color: #4A6A92;")

        self.discount_label = QLabel("")
        self.discount_label.setAlignment(Qt.AlignCenter)
        self.discount_label.setStyleSheet("font-size: 13px; color: #22C55E; font-weight: bold; background: transparent; border: none;")

        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_value)
        total_layout.addWidget(self.discount_label)
        right_layout.addWidget(total_frame)

        self.charge_button = QPushButton("COBRAR")
        self.charge_button.setStyleSheet("""
            QPushButton { background-color: #4A6A92; }
            QPushButton:hover { background-color: #3D5A80; }
        """)
        self.charge_button.clicked.connect(self.charge_sale)
        right_layout.addWidget(self.charge_button)

        content_layout.addWidget(left_frame, 3)
        content_layout.addWidget(right_frame, 1)
        main_layout.addLayout(content_layout)

    def on_client_input_changed(self, text):
        if not text.strip():
            self.clear_client()

    def search_client(self):

        query = self.client_input.text().strip().upper()
        if not query:
            self.clear_client()
            return

        db = SessionLocal()
        try:
            client = db.query(Client).filter(
                (Client.name == query) |
                (Client.account_number == query),
                Client.is_active == True
            ).first()

            if not client:
                # Buscar parcial
                client = db.query(Client).filter(
                    Client.name.contains(query),
                    Client.is_active == True
                ).first()

            if not client:
                self.show_message("Error", f"Cliente '{query}' no encontrado")
                return

            self.current_client = client.name
            self.current_discount = client.discount or 0.0
            self.client_input.setText(client.name)

            if self.current_discount > 0:
                self.client_info_label.setText(
                    f"✓ {client.name}  |  {int(self.current_discount)}% descuento"
                )
                self.client_info_label.setStyleSheet(
                    "font-size: 14px; color: #22C55E; font-weight: bold; background: transparent; border: none;"
                )
            else:
                self.client_info_label.setText(f"✓ {client.name}  |  Sin descuento")
                self.client_info_label.setStyleSheet(
                    "font-size: 14px; color: #4A6A92; font-weight: bold; background: transparent; border: none;"
                )

            self.refresh_cart()

        finally:
            db.close()

    def clear_client(self):
        self.current_client = None
        self.current_discount = 0.0
        self.client_input.clear()
        self.client_info_label.setText("Cliente: Consumidor Final")
        self.client_info_label.setStyleSheet(
            "font-size: 14px; color: #64748B; font-weight: bold; background: transparent; border: none;"
        )
        self.refresh_cart()

    def show_message(self, title, message):

        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStyleSheet("""
            QMessageBox { background-color: white; }
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
            QPushButton:hover { background-color: #3D5A80; }
        """)
        msg.exec()

    def load_products(self):

        self.products_list.clear()
        db = SessionLocal()

        try:
            products = db.query(Product).filter(Product.is_active == True).all()
            for product in products:
                item_text = f"{product.name}   $ {int(product.price)}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, product)
                self.products_list.addItem(item)
        finally:
            db.close()

    def add_product_to_cart(self, item):

        product = item.data(Qt.UserRole)
        db = SessionLocal()

        try:
            db_product = db.query(Product).filter(Product.id == product.id).first()

            if not db_product or db_product.stock <= 0:
                self.show_message("Sin stock", f"{product.name} no tiene stock disponible")
                return

            for cart_item in self.cart:
                if cart_item["id"] == product.id:
                    if cart_item["quantity"] >= db_product.stock:
                        self.show_message("Sin stock", f"{product.name} solo tiene {int(db_product.stock)} unidades disponibles")
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
            # Buscar por barcode o por nombre
            product = db.query(Product).filter(
                Product.barcode == barcode,
                Product.is_active == True
            ).first()

            if not product:
                product = db.query(Product).filter(
                    Product.name.contains(barcode.upper()),
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
                        self.show_message("Sin stock", f"{product.name} solo tiene {int(product.stock)} unidades disponibles")
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
        subtotal_bruto = 0

        for item in self.cart:
            subtotal = item["price"] * item["quantity"]
            subtotal_bruto += subtotal
            text = f"{item['name']} x{item['quantity']}   $ {int(subtotal)}"
            list_item = QListWidgetItem(text)
            self.cart_list.addItem(list_item)

        if self.current_discount > 0:
            descuento_monto = subtotal_bruto * (self.current_discount / 100)
            total_final = subtotal_bruto - descuento_monto
            self.total_value.setText(f"$ {int(total_final)}")
            self.discount_label.setText(
                f"Descuento {int(self.current_discount)}%: -$ {int(descuento_monto)}"
            )
        else:
            self.total_value.setText(f"$ {int(subtotal_bruto)}")
            self.discount_label.setText("")

    def get_total(self):
        subtotal = sum(item["price"] * item["quantity"] for item in self.cart)
        if self.current_discount > 0:
            return subtotal * (1 - self.current_discount / 100)
        return subtotal

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

    def register_sale(self, total, payment_method):

        db = SessionLocal()

        try:
            cash_session = db.query(CashSession).filter(CashSession.is_open == True).first()

            if not cash_session:
                self.show_message("Error", "No hay caja abierta")
                return None

            ticket = Ticket(
                total=total,
                username=cash_session.username,
                cash_session_id=cash_session.id,
                payment_method=payment_method
            )

            db.add(ticket)
            db.flush()

            cart_snapshot = list(self.cart)

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

                product = db.query(Product).filter(Product.id == item["id"]).first()
                if product:
                    product.stock -= item["quantity"]

            db.commit()
            return ticket.id, cart_snapshot

        except Exception as e:
            db.rollback()
            self.show_message("Error", f"Error al registrar venta: {str(e)}")
            return None

        finally:
            db.close()

    def charge_sale(self):

        if not self.cart:
            self.show_message("Error", "Debe agregar productos")
            return

        db = SessionLocal()

        try:
            cash_session = db.query(CashSession).filter(CashSession.is_open == True).first()

            if not cash_session:
                self.show_message("Error", "Debe abrir una caja antes de vender")
                return

            for item in self.cart:
                product = db.query(Product).filter(Product.id == item["id"]).first()
                if not product:
                    self.show_message("Error", f"Producto {item['name']} no encontrado")
                    return
                if product.stock < item["quantity"]:
                    self.show_message("Stock insuficiente", f"{product.name} tiene solo {int(product.stock)} unidades disponibles")
                    return

        finally:
            db.close()

        total = self.get_total()

        # ── Bucle de pago ─────────────────────────────
        while True:

            dialog = PaymentDialog(total, parent=self)
            result = dialog.exec()

            if result != QDialog.Accepted:
                return

            payment_method = dialog.selected_method

            if payment_method == "cash":
                reg = self.register_sale(total, payment_method)
                if reg is None:
                    return
                ticket_id, cart_snapshot = reg
                success, msg = print_ticket(ticket_id, cart_snapshot, total, payment_method)
                if not success:
                    self.show_message("Aviso", f"Venta registrada pero {msg}")
                else:
                    self.show_message("Venta exitosa", f"Venta N° {ticket_id:05d} registrada\nTotal: $ {int(total)}")
                break

            elif payment_method in ("transfer", "qr"):
                transfer_dialog = TransferDialog(
                    total=total,
                    ticket_id=None,
                    cart=list(self.cart),
                    payment_method=payment_method,
                    parent=self,
                    on_confirm=lambda: self.register_sale(total, payment_method)
                )
                transfer_dialog.exec()

                if transfer_dialog.sale_confirmed:
                    break
                else:
                    continue

            elif payment_method == "budget":
                budget_dialog = BudgetDialog(
                    total=total,
                    ticket_id=None,
                    cart=list(self.cart),
                    parent=self,
                    on_confirm=lambda email: self._confirm_budget(total, email)
                )
                result = budget_dialog.exec()

                if result == QDialog.Accepted:
                    break
                else:
                    continue

        self.cart.clear()
        self.clear_client()
        self.refresh_cart()
        self.load_products()

    def _confirm_budget(self, total, email):
        result = self.register_sale(total, "budget")
        if result is None:
            return None
        ticket_id, cart_snapshot = result
        return ticket_id, cart_snapshot, email