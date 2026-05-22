from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from datetime import datetime
from app.database.database import Base


class ClientAccount(Base):

    __tablename__ = "client_accounts"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    account_number = Column(String, nullable=True)
    detail = Column(String, nullable=True)
    delivery_date = Column(DateTime, nullable=True)
    payment_date = Column(DateTime, nullable=True)
    amount = Column(Float, default=0.0)
    is_paid = Column(Boolean, default=False)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)