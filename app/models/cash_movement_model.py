from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from app.database.database import Base


class CashMovement(Base):

    __tablename__ = "cash_movements"

    id = Column(Integer, primary_key=True, index=True)
    cash_session_id = Column(Integer, ForeignKey("cash_sessions.id"), nullable=True)
    type = Column(String, nullable=False)  # ingreso / egreso
    concept = Column(String, nullable=True)
    amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)