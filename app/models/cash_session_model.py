
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
)

from datetime import datetime

from app.database.database import Base


class CashSession(Base):

    __tablename__ = "cash_sessions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(String)

    opening_amount = Column(
        Integer,
        default=0
    )

    closing_amount = Column(
        Integer,
        default=0
    )

    expected_amount = Column(
        Integer,
        default=0
    )

    difference = Column(
        Integer,
        default=0
    )

    opened_at = Column(
        DateTime,
        default=datetime.now
    )

    closed_at = Column(DateTime)

    is_open = Column(
        Boolean,
        default=True
    )
