
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
)

from PySide6.QtCore import Qt

from app.assets.themes.theme import PRIMARY_COLOR


class CartItemWidget(QWidget):

    def __init__(
        self,
        product_name,
        quantity,
        subtotal
    ):
        super().__init__()

        layout = QHBoxLayout()

        layout.setContentsMargins(10, 8, 10, 8)

        # PRODUCT NAME

        product_label = QLabel(product_name)

        product_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 500;
        """)

        # QUANTITY

        quantity_label = QLabel(f"x{quantity}")

        quantity_label.setAlignment(Qt.AlignCenter)

        quantity_label.setFixedWidth(50)

        quantity_label.setStyleSheet(f"""
            font-size: 15px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
        """)

        # SUBTOTAL

        subtotal_label = QLabel(f"$ {subtotal}")

        subtotal_label.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )

        subtotal_label.setFixedWidth(100)

        subtotal_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
        """)

        # ADD TO LAYOUT

        layout.addWidget(product_label)

        layout.addStretch()

        layout.addWidget(quantity_label)

        layout.addWidget(subtotal_label)

        self.setLayout(layout)
