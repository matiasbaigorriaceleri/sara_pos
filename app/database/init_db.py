from sqlalchemy.orm import Session

from app.database.database import engine, SessionLocal, Base
from app.models.user_model import User


def init_database():
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    admin_user = db.query(User).filter(
        User.username == "admin"
    ).first()

    if not admin_user:
        new_admin = User(
            username="admin",
            password="1234",
            role="admin",
            is_active=True
        )

        db.add(new_admin)
        db.commit()

        print("Usuario admin creado correctamente")

    else:
        print("El usuario admin ya existe")

    db.close()

if __name__ == "__main__":
    init_database()