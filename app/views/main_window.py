from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
    QMessageBox,
)

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from app.assets.themes.theme import PRIMARY_COLOR, BACKGROUND_COLOR
from datetime import date, timedelta


class MainWindow(QMainWindow):

    def __init__(self, username, role):
        super().__init__()

        self.username = username
        self.role = role
        self._pages_loaded = {}
        self._alerts_shown = False

        self.setWindowTitle("SARA POS")

        screen = QGuiApplication.primaryScreen()
        geometry = screen.availableGeometry()
        screen_width = geometry.width()
        screen_height = geometry.height()

        width = int(screen_width * 0.78)
        height = int(screen_height * 0.82)

        if width > 1450:
            width = 1450
        if height > 900:
            height = 900
        if width < 1100:
            width = 1100
        if height < 700:
            height = 700

        self.resize(width, height)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.move(x, y)

        self.setup_ui()

    def setup_ui(self):

        central_widget = QWidget()
        central_widget.setStyleSheet(f"background-color: {BACKGROUND_COLOR};")
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central_widget.setLayout(main_layout)

        sidebar = QWidget()
        sidebar.setFixedWidth(210)
        sidebar.setStyleSheet("background-color: #243B53;")

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(15, 22, 15, 20)
        sidebar_layout.setSpacing(6)

        logo = QLabel("SARA POS")
        logo.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: white;
            margin-bottom: 20px;
        """)
        sidebar_layout.addWidget(logo)

        self.pages = QStackedWidget()
        self.pages.setStyleSheet(f"background-color: {BACKGROUND_COLOR};")

        for i in range(8):
            placeholder = QWidget()
            self.pages.addWidget(placeholder)

        sales_btn = self.create_menu_button("Ventas")
        sales_btn.clicked.connect(lambda: self.navigate_to(0))
        sidebar_layout.addWidget(sales_btn)

        detail_btn = self.create_menu_button("Detalle Ventas")
        detail_btn.clicked.connect(lambda: self.navigate_to(1))
        sidebar_layout.addWidget(detail_btn)

        products_btn = self.create_menu_button("Productos")
        products_btn.clicked.connect(lambda: self.navigate_to(2))
        sidebar_layout.addWidget(products_btn)

        cash_btn = self.create_menu_button("Arqueo Caja")
        cash_btn.clicked.connect(lambda: self.navigate_to(3))
        sidebar_layout.addWidget(cash_btn)

        dashboard_btn = self.create_menu_button("Dashboard")
        dashboard_btn.clicked.connect(lambda: self.navigate_to(4))
        sidebar_layout.addWidget(dashboard_btn)

        suppliers_btn = self.create_menu_button("Proveedores")
        suppliers_btn.clicked.connect(lambda: self.navigate_to(5))
        sidebar_layout.addWidget(suppliers_btn)

        clients_btn = self.create_menu_button("Clientes")
        clients_btn.clicked.connect(lambda: self.navigate_to(6))
        sidebar_layout.addWidget(clients_btn)

        if self.role.upper() == "ADMIN":
            settings_btn = self.create_menu_button("Configuración")
            settings_btn.clicked.connect(lambda: self.navigate_to(7))
            sidebar_layout.addWidget(settings_btn)

        sidebar_layout.addStretch()

        user_label = QLabel(f"Usuario: {self.username}")
        user_label.setStyleSheet("color: #E5E7EB; font-size: 13px; margin-bottom: 6px;")
        sidebar_layout.addWidget(user_label)

        logout_button = QPushButton("Cerrar sesión")
        logout_button.setMinimumHeight(40)
        logout_button.setStyleSheet("""
            QPushButton {
                background-color: #3E5C76;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #4F76A1; }
        """)
        logout_button.clicked.connect(self.logout)
        sidebar_layout.addWidget(logout_button)

        sidebar.setLayout(sidebar_layout)
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.pages)

        self.navigate_to(0)

        # Mostrar alertas después de que la ventana termine de cargar
        QTimer.singleShot(800, self.check_payment_alerts)

    def check_payment_alerts(self):
        """Verifica facturas de proveedores que vencen hoy o mañana."""

        if self._alerts_shown:
            return

        self._alerts_shown = True

        from app.database.database import SessionLocal
        from app.models.supplier_invoice_model import SupplierInvoice
        from app.models.supplier_model import Supplier

        today = date.today()
        tomorrow = today + timedelta(days=1)

        db = SessionLocal()
        try:
            invoices = db.query(SupplierInvoice).filter(
                SupplierInvoice.is_paid == False
            ).all()

            suppliers = {s.id: s.name for s in db.query(Supplier).all()}
            alerts_today = []
            alerts_tomorrow = []

            for inv in invoices:
                if not inv.payment_date:
                    continue
                inv_date = inv.payment_date.date() if hasattr(inv.payment_date, 'date') else inv.payment_date
                supplier_name = suppliers.get(inv.supplier_id, "Proveedor desconocido")
                monto = f"$ {int(inv.amount or 0)}"

                if inv_date == today:
                    alerts_today.append(f"• {supplier_name} — {monto} — VENCE HOY")
                elif inv_date == tomorrow:
                    alerts_tomorrow.append(f"• {supplier_name} — {monto} — vence mañana")

        finally:
            db.close()

        all_alerts = alerts_today + alerts_tomorrow

        if all_alerts:
            msg = QMessageBox(self)
            msg.setWindowTitle("⚠️ Alertas de pago a proveedores")
            msg.setText(
                "Tenés facturas pendientes de pago:\n\n" +
                "\n".join(all_alerts)
            )
            msg.setStyleSheet("""
                QMessageBox { background-color: white; }
                QLabel {
                    color: #1E293B;
                    font-size: 14px;
                    min-width: 400px;
                }
                QPushButton {
                    background-color: #4A6A92; color: white; border: none;
                    border-radius: 10px; padding: 10px 20px; min-width: 80px;
                    min-height: 32px; font-size: 13px; font-weight: bold;
                }
                QPushButton:hover { background-color: #3D5A80; }
            """)
            msg.exec()

    def navigate_to(self, index):

        if index not in self._pages_loaded:
            page = self.load_page(index)
            if page:
                self.pages.removeWidget(self.pages.widget(index))
                self.pages.insertWidget(index, page)
                self._pages_loaded[index] = page
        else:
            page = self._pages_loaded[index]
            if hasattr(page, 'load_products'):
                page.load_products()
            elif hasattr(page, 'load_sales'):
                page.load_sales()
            elif hasattr(page, 'load_data'):
                page.load_data()
            elif hasattr(page, 'load_suppliers'):
                page.load_suppliers()
            elif hasattr(page, 'load_clients'):
                page.load_clients()

        self.pages.setCurrentIndex(index)

    def load_page(self, index):

        if index == 0:
            from app.views.pages.sales_page import SalesPage
            return SalesPage()
        elif index == 1:
            from app.views.pages.sales_detail_page import SalesDetailPage
            return SalesDetailPage()
        elif index == 2:
            from app.views.pages.products_page import ProductsPage
            return ProductsPage()
        elif index == 3:
            from app.views.pages.cash_register_page import CashRegisterPage
            return CashRegisterPage(self.username)
        elif index == 4:
            from app.views.pages.dashboard_page import DashboardPage
            return DashboardPage()
        elif index == 5:
            from app.views.pages.suppliers_page import SuppliersPage
            return SuppliersPage()
        elif index == 6:
            from app.views.pages.clients_page import ClientsPage
            return ClientsPage()
        elif index == 7:
            from app.views.pages.settings_page import SettingsPage
            return SettingsPage()

        return None

    def create_menu_button(self, text):

        button = QPushButton(text)
        button.setMinimumHeight(40)
        button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
                text-align: left;
                padding-left: 16px;
            }
            QPushButton:hover { background-color: #3E5C76; }
        """)
        return button

    def logout(self):
        from app.views.login_window import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()