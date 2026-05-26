import sys
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from app.database.database import (
    Base,
    engine,
    SessionLocal,
)

from app.models.user_model import User
from app.models.product_model import Product
from app.models.ticket_model import Ticket
from app.models.ticket_item_model import TicketItem
from app.models.cash_session_model import CashSession
from app.models.settings_model import Setting
from app.models.supplier_model import Supplier
from app.models.client_model import Client
from app.models.supplier_invoice_model import SupplierInvoice
from app.models.client_account_model import ClientAccount
from app.models.cash_movement_model import CashMovement

from app.views.login_window import LoginWindow

# ── Crear tablas ──────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Crear usuario admin por defecto ───────────────────
db = SessionLocal()

admin_user = db.query(User).filter(
    User.username == "admin"
).first()

if not admin_user:
    user = User(
        username="admin",
        password="123",
        role="ADMIN",
        is_active=True
    )
    db.add(user)
    db.commit()

db.close()

# ── Iniciar app ───────────────────────────────────────
app = QApplication(sys.argv)

# ── Ícono de la app ───────────────────────────────────
icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "assets", "sara_pos.png")
if os.path.exists(icon_path):
    app.setWindowIcon(QIcon(icon_path))

window = LoginWindow()
window.show()
sys.exit(app.exec())