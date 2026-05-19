
from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QStackedWidget,
)

from PySide6.QtCore import Qt

from app.assets.themes.theme import (
    BACKGROUND_COLOR,
    SIDEBAR_COLOR,
    PRIMARY_COLOR,
    TEXT_LIGHT,
    TEXT_DARK,
)

from app.views.pages.dashboard_page import DashboardPage
from app.views.pages.sales_page import SalesPage
from app.views.pages.products_page import ProductsPage


class DashboardWindow(QWidget):
    def __init__(self, user):
        super().__init__()

        self.user = user

        self.setWindowTitle("SARA POS")
        self.resize(1400, 800)

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_DARK};
                font-size: 14px;
                font-family: Arial;
            }}
        """)

        self.active_button = None

        # =====================================
        # MAIN LAYOUT
        # =====================================

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # =====================================
        # SIDEBAR
        # =====================================

        sidebar = QFrame()
        sidebar.setFixedWidth(240)

        sidebar.setStyleSheet(f"""
            background-color: {SIDEBAR_COLOR};
        """)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(20, 25, 20, 25)
        sidebar_layout.setSpacing(10)

        # =====================================
        # LOGO
        # =====================================

        logo = QLabel("SARA POS")

        logo.setAlignment(Qt.AlignCenter)

        logo.setStyleSheet(f"""
            color: {TEXT_LIGHT};
            font-size: 30px;
            font-weight: bold;
            margin-bottom: 30px;
        """)

        sidebar_layout.addWidget(logo)

        # =====================================
        # STACKED PAGES
        # =====================================

        self.pages = QStackedWidget()

        self.dashboard_page = DashboardPage()
        self.sales_page = SalesPage()
        self.products_page = ProductsPage()

        self.pages.addWidget(self.dashboard_page)
        self.pages.addWidget(self.sales_page)
        self.pages.addWidget(self.products_page)

        # =====================================
        # BUTTONS
        # =====================================

        self.dashboard_btn = QPushButton("Dashboard")
        self.sales_btn = QPushButton("Ventas")
        self.products_btn = QPushButton("Productos")

        self.menu_buttons = [
            self.dashboard_btn,
            self.sales_btn,
            self.products_btn,
        ]

        for button in self.menu_buttons:

            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(45)

            self.set_button_default_style(button)

            sidebar_layout.addWidget(button)

        # =====================================
        # BUTTON EVENTS
        # =====================================

        self.dashboard_btn.clicked.connect(
            lambda: self.change_page(
                self.dashboard_page,
                self.dashboard_btn
            )
        )

        self.sales_btn.clicked.connect(
            lambda: self.change_page(
                self.sales_page,
                self.sales_btn
            )
        )

        self.products_btn.clicked.connect(
            lambda: self.change_page(
                self.products_page,
                self.products_btn
            )
        )

        # DEFAULT ACTIVE BUTTON

        self.change_page(
            self.dashboard_page,
            self.dashboard_btn
        )

        sidebar_layout.addStretch()

        # =====================================
        # USER CARD
        # =====================================

        user_card = QFrame()

        user_card.setStyleSheet("""
            background-color: rgba(255,255,255,0.08);
            border-radius: 14px;
        """)

        user_layout = QVBoxLayout()

        username = QLabel(self.user.username)
        username.setStyleSheet("""
            color: white;
            font-size: 15px;
            font-weight: bold;
        """)

        role = QLabel(self.user.role)
        role.setStyleSheet("""
            color: rgba(255,255,255,0.7);
            font-size: 13px;
        """)

        user_layout.addWidget(username)
        user_layout.addWidget(role)

        user_card.setLayout(user_layout)

        sidebar_layout.addWidget(user_card)

        sidebar.setLayout(sidebar_layout)

        # =====================================
        # CONTENT AREA
        # =====================================

        content = QFrame()

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(30, 30, 30, 30)

        content_layout.addWidget(self.pages)

        content.setLayout(content_layout)

        # =====================================
        # ADD TO MAIN LAYOUT
        # =====================================

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)

        self.setLayout(main_layout)

    # =====================================
    # BUTTON STYLES
    # =====================================

    def set_button_default_style(self, button):

        button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT_LIGHT};
                border: none;
                border-radius: 12px;
                padding-left: 15px;
                text-align: left;
                font-size: 15px;
            }}

            QPushButton:hover {{
                background-color: rgba(255,255,255,0.08);
            }}
        """)

    def set_button_active_style(self, button):

        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY_COLOR};
                color: white;
                border: none;
                border-radius: 12px;
                padding-left: 15px;
                text-align: left;
                font-size: 15px;
                font-weight: bold;
            }}
        """)

    # =====================================
    # CHANGE PAGE
    # =====================================

    def change_page(self, page, button):

        self.pages.setCurrentWidget(page)

        for btn in self.menu_buttons:
            self.set_button_default_style(btn)

        self.set_button_active_style(button)
