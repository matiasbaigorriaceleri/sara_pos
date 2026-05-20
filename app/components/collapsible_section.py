from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QToolButton,
    QSizePolicy,
)

from PySide6.QtCore import (
    Qt,
)

from app.assets.themes.theme import (
    PRIMARY_COLOR
)


class CollapsibleSection(QWidget):

    def __init__(
        self,
        title,
        content_widget
    ):
        super().__init__()

        self.content_widget = content_widget

        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(0)

        # =====================================
        # HEADER BUTTON
        # =====================================

        self.toggle_button = QToolButton()

        self.toggle_button.setText(title)

        self.toggle_button.setCheckable(True)

        self.toggle_button.setChecked(True)

        self.toggle_button.setToolButtonStyle(
            Qt.ToolButtonTextBesideIcon
        )

        self.toggle_button.setArrowType(
            Qt.DownArrow
        )

        self.toggle_button.clicked.connect(
            self.toggle
        )

        self.toggle_button.setStyleSheet(f"""
            QToolButton {{
                background-color: white;
                border: none;
                padding: 18px;
                text-align: left;
                font-size: 20px;
                font-weight: bold;
                color: {PRIMARY_COLOR};
                border-top-left-radius: 18px;
                border-top-right-radius: 18px;
            }}

            QToolButton:hover {{
                background-color: #F8FAFC;
            }}
        """)

        main_layout.addWidget(
            self.toggle_button
        )

        # =====================================
        # CONTENT
        # =====================================

        self.content_widget.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        self.content_widget.setStyleSheet("""
            background-color: white;
            border-bottom-left-radius: 18px;
            border-bottom-right-radius: 18px;
        """)

        main_layout.addWidget(
            self.content_widget
        )

        self.setLayout(main_layout)

    # =====================================
    # TOGGLE
    # =====================================

    def toggle(self):

        checked = (
            self.toggle_button.isChecked()
        )

        if checked:

            self.toggle_button.setArrowType(
                Qt.DownArrow
            )

            self.content_widget.show()

        else:

            self.toggle_button.setArrowType(
                Qt.RightArrow
            )

            self.content_widget.hide()
