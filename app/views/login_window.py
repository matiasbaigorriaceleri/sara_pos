
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
)

from PySide6.QtCore import Qt

from app.views.dashboard_window import DashboardWindow

from app.database.database import SessionLocal
from app.models.user_model import User

from app.assets.themes.theme import (
    WINDOW_STYLE,
    INPUT_STYLE,
    BUTTON_STYLE,
    PRIMARY_COLOR,
)


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SARA POS - Login")
        self.setFixedSize(400, 300)

        self.setStyleSheet(WINDOW_STYLE)

        layout = QVBoxLayout()

        title = QLabel("SARA POS")
        title.setAlignment(Qt.AlignCenter)

        title.setStyleSheet(f"""
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 20px;
            color: {PRIMARY_COLOR};
        """)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Usuario")
        self.username_input.setStyleSheet(INPUT_STYLE)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(INPUT_STYLE)

        login_button = QPushButton("Ingresar")
        login_button.setStyleSheet(BUTTON_STYLE)

        login_button.clicked.connect(self.login)

        self.username_input.returnPressed.connect(
            self.password_input.setFocus
        )

        self.password_input.returnPressed.connect(
            self.login
        )

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_button)
        layout.addStretch()

        self.setLayout(layout)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        db = SessionLocal()

        user = db.query(User).filter(
            User.username == username,
            User.password == password,
            User.is_active == True
        ).first()

        db.close()

        if user:
            self.dashboard = DashboardWindow(user)
            self.dashboard.show()

            self.close()

        else:
            QMessageBox.warning(
                self,
                "Error",
                "Usuario o contraseña incorrectos"
            )
