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

    id = Column(Integer, primary_key=True, index=True)
    cash_session_id = Column(Integer)
    username = Column(String)
    products = Column(String)
    total = Column(Integer)
    payment_method = Column(String, default="cash")
    created_at = Column(DateTime, default=datetime.now)

    # Estado: "active" o "cancelled"
    status = Column(String, default="active")

    # Motivo de anulación (solo si status == "cancelled")
    cancel_reason = Column(String, default="")
    cancelled_by = Column(String, default="")
    cancelled_at = Column(DateTime, nullable=True)