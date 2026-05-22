from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from datetime import datetime
from app.database.database import Base


class SupplierInvoice(Base):

    __tablename__ = "supplier_invoices"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    invoice_number = Column(String, nullable=True)
    entry_date = Column(DateTime, default=datetime.now)
    payment_date = Column(DateTime, nullable=True)
    amount = Column(Float, default=0.0)
    is_paid = Column(Boolean, default=False)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)