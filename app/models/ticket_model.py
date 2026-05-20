from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
)

from datetime import datetime

from app.database.database import Base


class Ticket(Base):

    __tablename__ = "tickets"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    cash_session_id = Column(
        Integer
    )

    username = Column(
        String
    )

    products = Column(
        String
    )

    total = Column(
        Integer
    )

    created_at = Column(
        DateTime,
        default=datetime.now
    )
