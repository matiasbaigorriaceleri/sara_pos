
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
)

from PySide6.QtGui import (
    QGuiApplication
)

from app.assets.themes.theme import (
    PRIMARY_COLOR,
    BACKGROUND_COLOR,
)

from app.views.pages.sales_page import SalesPage
from app.views.pages.sales_detail_page import SalesDetailPage
from app.views.pages.products_page import ProductsPage
from app.views.pages.cash_register_page import CashRegisterPage
from app.views.pages.dashboard_page import DashboardPage
from app.views.pages.settings_page import SettingsPage


class MainWindow(QMainWindow):

    def __init__(self, username, role):
        super().__init__()

        self.username = username
        self.role = role

        self.setWindowTitle("SARA POS")

        # =====================================
        # RESPONSIVE WINDOW
        # =====================================

        screen = QGuiApplication.primaryScreen()

        geometry = screen.availableGeometry()

        screen_width = geometry.width()
        screen_height = geometry.height()

        # =====================================
        # RESPONSIVE INTELIGENTE
        # =====================================

        width = int(screen_width * 0.78)
        height = int(screen_height * 0.82)

        # =====================================
        # LIMITES MAXIMOS
        # =====================================

        if width > 1450:
            width = 1450

        if height > 900:
            height = 900

        # =====================================
        # LIMITES MINIMOS
        # =====================================

        if width < 1100:
            width = 1100

        if height < 700:
            height = 700

        self.resize(width, height)

        # =====================================
        # CENTRAR VENTANA
        # =====================================

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.move(x, y)

        self.setup_ui()

    def setup_ui(self):

        central_widget = QWidget()

        central_widget.setStyleSheet(f"""
            background-color: {BACKGROUND_COLOR};
        """)

        self.setCentralWidget(
            central_widget
        )

        main_layout = QHBoxLayout()

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(0)

        central_widget.setLayout(
            main_layout
        )

        # =====================================
        # SIDEBAR
        # =====================================

        sidebar = QWidget()

        sidebar.setFixedWidth(210)

        sidebar.setStyleSheet("""
            background-color: #243B53;
        """)

        sidebar_layout = QVBoxLayout()

        sidebar_layout.setContentsMargins(
            15,
            22,
            15,
            20
        )

        sidebar_layout.setSpacing(10)

        # =====================================
        # LOGO
        # =====================================

        logo = QLabel(
            "SARA POS"
        )

        logo.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: white;
            margin-bottom: 25px;
        """)

        sidebar_layout.addWidget(
            logo
        )

        # =====================================
        # PAGES
        # =====================================

        self.pages = QStackedWidget()

        self.pages.setStyleSheet(f"""
            background-color: {BACKGROUND_COLOR};
        """)

        self.sales_page = SalesPage()

        self.sales_detail_page = (
            SalesDetailPage()
        )

        self.products_page = (
            ProductsPage()
        )

        self.cash_register_page = (
            CashRegisterPage(
                self.username
            )
        )

        self.dashboard_page = (
            DashboardPage()
        )

        self.settings_page = (
            SettingsPage()
        )

        self.pages.addWidget(
            self.sales_page
        )

        self.pages.addWidget(
            self.sales_detail_page
        )

        self.pages.addWidget(
            self.products_page
        )

        self.pages.addWidget(
            self.cash_register_page
        )

        self.pages.addWidget(
            self.dashboard_page
        )

        self.pages.addWidget(
            self.settings_page
        )

        # =====================================
        # MENU BUTTONS
        # =====================================

        sales_button = (
            self.create_menu_button(
                "Ventas"
            )
        )

        sales_button.clicked.connect(
            lambda: self.pages.setCurrentIndex(0)
        )

        sidebar_layout.addWidget(
            sales_button
        )

        detail_button = (
            self.create_menu_button(
                "Detalle Ventas"
            )
        )

        detail_button.clicked.connect(
            lambda: self.pages.setCurrentIndex(1)
        )

        sidebar_layout.addWidget(
            detail_button
        )

        products_button = (
            self.create_menu_button(
                "Productos"
            )
        )

        products_button.clicked.connect(
            lambda: self.pages.setCurrentIndex(2)
        )

        sidebar_layout.addWidget(
            products_button
        )

        cash_button = (
            self.create_menu_button(
                "Arqueo Caja"
            )
        )

        cash_button.clicked.connect(
            lambda: self.pages.setCurrentIndex(3)
        )

        sidebar_layout.addWidget(
            cash_button
        )

        dashboard_button = (
            self.create_menu_button(
                "Dashboard"
            )
        )

        dashboard_button.clicked.connect(
            lambda: self.pages.setCurrentIndex(4)
        )

        sidebar_layout.addWidget(
            dashboard_button
        )

        if self.role.upper() == "GOD":

            settings_button = (
                self.create_menu_button(
                    "Configuración"
                )
            )

            settings_button.clicked.connect(
                lambda: self.pages.setCurrentIndex(5)
            )

            sidebar_layout.addWidget(
                settings_button
            )

        sidebar_layout.addStretch()

        # =====================================
        # USER
        # =====================================

        user_label = QLabel(
            f"Usuario: {self.username}"
        )

        user_label.setStyleSheet("""
            color: #E5E7EB;
            font-size: 13px;
            margin-bottom: 6px;
        """)

        sidebar_layout.addWidget(
            user_label
        )

        # =====================================
        # LOGOUT
        # =====================================

        logout_button = QPushButton(
            "Cerrar sesión"
        )

        logout_button.setMinimumHeight(
            40
        )

        logout_button.setStyleSheet("""
            QPushButton {
                background-color: #3E5C76;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #4F76A1;
            }
        """)

        logout_button.clicked.connect(
            self.logout
        )

        sidebar_layout.addWidget(
            logout_button
        )

        sidebar.setLayout(
            sidebar_layout
        )

        # =====================================
        # MAIN
        # =====================================

        main_layout.addWidget(
            sidebar
        )

        main_layout.addWidget(
            self.pages
        )

        self.pages.setCurrentIndex(0)

    # =====================================
    # MENU BUTTON
    # =====================================

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

            QPushButton:hover {
                background-color: #3E5C76;
            }
        """)

        return button

    # =====================================
    # LOGOUT
    # =====================================

    def logout(self):

        from app.views.login_window import (
            LoginWindow
        )

        self.login_window = (
            LoginWindow()
        )

        self.login_window.show()

        self.close()
