import sys

from PySide6.QtWidgets import QApplication

from app.database.database import (
    Base,
    engine,
    SessionLocal,
)

from app.models.user_model import User
from app.models.product_model import Product

from app.views.login_window import LoginWindow


# =========================================================
# CREATE TABLES
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# CREATE ADMIN USER
# =========================================================

db = SessionLocal()

admin_user = db.query(User).filter(
    User.username == "admin"
).first()

if not admin_user:

    user = User(
        username="admin",
        password="admin",
        role="ADMIN",
        is_active=True
    )

    db.add(user)

    db.commit()

db.close()


# =========================================================
# START APP
# =========================================================

app = QApplication(sys.argv)

window = LoginWindow()

window.show()

sys.exit(app.exec())