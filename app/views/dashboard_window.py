from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
    QMessageBox,
)

from app.assets.themes.theme import (
    SIDEBAR_STYLE,
)

from app.views.pages.sales_page import SalesPage

from app.views.pages.sales_detail_page import (
    SalesDetailPage
)

from app.views.pages.products_page import (
    ProductsPage
)

from app.views.pages.cash_register_page import (
    CashRegisterPage
)

from app.views.pages.dashboard_page import (
    DashboardPage
)

from app.views.pages.settings_page import (
    SettingsPage
)


class DashboardWindow(QWidget):

    def __init__(
        self,
        username="admin",
        role="admin"
    ):
        super().__init__()

        self.username = username

        self.role = role

        self.setWindowTitle("SARA POS")

        self.showMaximized()

        # =====================================
        # MAIN LAYOUT
        # =====================================

        main_layout = QHBoxLayout()

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(0)

        # =====================================
        # SIDEBAR
        # =====================================

        sidebar = QWidget()

        sidebar.setFixedWidth(260)

        sidebar.setStyleSheet(
            SIDEBAR_STYLE
        )

        sidebar_layout = QVBoxLayout()

        sidebar_layout.setContentsMargins(
            20,
            30,
            20,
            30
        )

        sidebar_layout.setSpacing(15)

        # =====================================
        # LOGO
        # =====================================

        logo = QLabel("SARA POS")

        logo.setStyleSheet("""
            font-size: 34px;
            font-weight: bold;
            color: white;
            margin-bottom: 30px;
        """)

        sidebar_layout.addWidget(logo)

        # =====================================
        # BUTTONS
        # =====================================

        self.sales_button = QPushButton(
            "Ventas"
        )

        self.sales_detail_button = QPushButton(
            "Detalle Ventas"
        )

        self.products_button = QPushButton(
            "Productos"
        )

        self.cash_button = QPushButton(
            "Arqueo Caja"
        )

        self.dashboard_button = QPushButton(
            "Dashboard"
        )

        self.settings_button = QPushButton(
            "Configuración"
        )

        buttons = [
            self.sales_button,
            self.sales_detail_button,
            self.products_button,
            self.cash_button,
            self.dashboard_button,
            self.settings_button,
        ]

        for button in buttons:

            button.setMinimumHeight(55)

            button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    border: none;
                    text-align: left;
                    padding-left: 20px;
                    font-size: 17px;
                    border-radius: 12px;
                }

                QPushButton:hover {
                    background-color: rgba(255,255,255,0.08);
                }
            """)

            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch()

        # =====================================
        # USER LABEL
        # =====================================

        user_label = QLabel(
            f"Usuario: {self.username}"
        )

        user_label.setStyleSheet("""
            color: rgba(255,255,255,0.7);
            font-size: 14px;
            margin-bottom: 10px;
        """)

        sidebar_layout.addWidget(user_label)

        # =====================================
        # LOGOUT BUTTON
        # =====================================

        logout_button = QPushButton(
            "Cerrar sesión"
        )

        logout_button.setMinimumHeight(45)

        logout_button.setStyleSheet("""
            QPushButton {
                background-color:
                    rgba(255,255,255,0.08);

                color: white;

                border: none;

                border-radius: 12px;

                font-size: 15px;

                font-weight: bold;
            }

            QPushButton:hover {
                background-color:
                    rgba(255,255,255,0.15);
            }
        """)

        logout_button.clicked.connect(
            self.logout
        )

        sidebar_layout.addWidget(
            logout_button
        )

        sidebar.setLayout(sidebar_layout)

        # =====================================
        # STACK
        # =====================================

        self.stack = QStackedWidget()

        self.sales_page = SalesPage()

        self.sales_detail_page = (
            SalesDetailPage()
        )

        self.products_page = ProductsPage()

        self.cash_register_page = (
            CashRegisterPage(self.username)
        )

        self.dashboard_page = DashboardPage()

        self.settings_page = SettingsPage()

        self.stack.addWidget(
            self.sales_page
        )

        self.stack.addWidget(
            self.sales_detail_page
        )

        self.stack.addWidget(
            self.products_page
        )

        self.stack.addWidget(
            self.cash_register_page
        )

        self.stack.addWidget(
            self.dashboard_page
        )

        self.stack.addWidget(
            self.settings_page
        )

        # =====================================
        # BUTTON ACTIONS
        # =====================================

        self.sales_button.clicked.connect(
            self.open_sales_page
        )

        self.sales_detail_button.clicked.connect(
            lambda:
            self.stack.setCurrentIndex(1)
        )

        self.products_button.clicked.connect(
            lambda:
            self.stack.setCurrentIndex(2)
        )

        self.cash_button.clicked.connect(
            lambda:
            self.stack.setCurrentIndex(3)
        )

        self.dashboard_button.clicked.connect(
            self.open_dashboard
        )

        self.settings_button.clicked.connect(
            self.open_settings
        )

        # =====================================
        # ADD MAIN
        # =====================================

        main_layout.addWidget(sidebar)

        main_layout.addWidget(self.stack)

        self.setLayout(main_layout)

    # =====================================
    # OPEN SALES
    # =====================================

    def open_sales_page(self):

        self.sales_page.load_products()

        self.sales_page.refresh_products_list()

        self.stack.setCurrentIndex(0)

    # =====================================
    # OPEN DASHBOARD
    # =====================================

    def open_dashboard(self):

        self.stack.removeWidget(
            self.dashboard_page
        )

        self.dashboard_page.deleteLater()

        self.dashboard_page = DashboardPage()

        self.stack.insertWidget(
            4,
            self.dashboard_page
        )

        self.stack.setCurrentIndex(4)

    # =====================================
    # OPEN SETTINGS
    # =====================================

    def open_settings(self):

        if self.role != "god":

            QMessageBox.warning(
                self,
                "Acceso denegado",
                "Solo GOD puede ingresar"
            )

            return

        self.stack.setCurrentIndex(5)

    # =====================================
    # LOGOUT
    # =====================================

    def logout(self):

        from app.views.login_window import (
            LoginWindow
        )

        self.login = LoginWindow()

        self.login.show()

        self.close()
