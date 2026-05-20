from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
)

from datetime import datetime

from app.database.database import Base


class Product(Base):

    __tablename__ = "products"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    product_code = Column(
        String,
        unique=True
    )

    name = Column(String)

    detail = Column(String)

    barcode = Column(
        String,
        unique=True
    )

    stock = Column(
        Integer,
        default=0
    )

    minimum_stock = Column(
        Integer,
        default=0
    )

    price = Column(
        Integer,
        default=0
    )

    cost_price = Column(
        Integer,
        default=0
    )

    category = Column(String)

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime,
        default=datetime.now
    )

    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now
    )