from app.database.database import (
    engine,
    SessionLocal,
    Base,
)

from app.models.user_model import User

from app.models.ticket_model import Ticket

from app.models.product_model import Product

from app.models.cash_session_model import (
    CashSession
)

from app.models.settings_model import (
    Setting
)


Base.metadata.create_all(bind=engine)

db = SessionLocal()

# =====================================
# ADMIN
# =====================================

admin_exists = db.query(User).filter(
    User.username == "admin"
).first()

if not admin_exists:

    admin_user = User(
        username="admin",
        password="1234",
        role="admin",
        is_active=True
    )

    db.add(admin_user)

# =====================================
# GOD
# =====================================

god_exists = db.query(User).filter(
    User.username == "GOD"
).first()

if not god_exists:

    god_user = User(
        username="GOD",
        password="Joacco2020!!",
        role="god",
        is_active=True
    )

    db.add(god_user)

# =====================================
# DEFAULT SETTINGS
# =====================================

default_settings = {

    # BUSINESS
    "business_name": "SARA POS",
    "business_cuit": "",
    "business_address": "",
    "business_phone": "",
    "ticket_footer": "Gracias por su compra",

    # PRINTER
    "printer_name": "",
    "printer_size": "80mm",

    # PAYMENT
    "mp_alias": "",
    "payment_qr_path": "",

    # SMTP
    "smtp_host": "",
    "smtp_port": "587",
    "smtp_email": "",
    "smtp_password": "",
    "smtp_tls": "true",
    "smtp_sender_name": "SARA POS",
}

for key, value in default_settings.items():

    existing = db.query(Setting).filter(
        Setting.key == key
    ).first()

    if not existing:

        setting = Setting(
            key=key,
            value=value
        )

        db.add(setting)

db.commit()

db.close()

print("Base de datos inicializada correctamente")