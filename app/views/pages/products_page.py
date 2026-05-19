
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
)

from app.assets.themes.theme import PRIMARY_COLOR


class ProductsPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        title = QLabel("Productos")

        title.setStyleSheet(f"""
            font-size: 34px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
        """)

        layout.addWidget(title)
        layout.addStretch()

        self.setLayout(layout)
