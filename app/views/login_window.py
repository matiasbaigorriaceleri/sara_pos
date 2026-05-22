from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QLineEdit,
    QMessageBox,
)

from PySide6.QtCore import Qt

from app.assets.themes.theme import (
    PRIMARY_COLOR,
    BACKGROUND_COLOR,
    INPUT_STYLE,
    BUTTON_STYLE,
)

from app.database.database import SessionLocal
from app.models.user_model import User
from app.views.main_window import MainWindow


class LoginWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):

        self.setWindowTitle("SARA POS - Login")
        self.setFixedSize(760, 520)
        self.setStyleSheet(f"background-color: {BACKGROUND_COLOR};")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(70, 50, 70, 50)
        main_layout.setSpacing(22)
        main_layout.setAlignment(Qt.AlignCenter)

        title = QLabel("SARA POS")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            font-size: 58px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
        """)
        main_layout.addWidget(title)

        subtitle = QLabel("Sistema de ventas")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 22px;
            color: #64748B;
            margin-bottom: 25px;
        """)
        main_layout.addWidget(subtitle)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Usuario")
        self.username_input.setMinimumHeight(62)
        self.username_input.setStyleSheet(INPUT_STYLE)
        main_layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(62)
        self.password_input.setStyleSheet(INPUT_STYLE)
        self.password_input.returnPressed.connect(self.login)
        main_layout.addWidget(self.password_input)

        login_button = QPushButton("Ingresar")
        login_button.setMinimumHeight(65)
        login_button.setStyleSheet(BUTTON_STYLE)
        login_button.clicked.connect(self.login)
        main_layout.addWidget(login_button)

        self.setLayout(main_layout)

    def login(self):

        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        db = SessionLocal()
        try:
            user = db.query(User).filter(
                User.username == username,
                User.password == password,
                User.is_active == True
            ).first()
        finally:
            db.close()

        if not user:
            QMessageBox.warning(self, "Error", "Usuario o contraseña incorrectos")
            return

        self.main_window = MainWindow(user.username, user.role)
        self.main_window.show()
        self.close()