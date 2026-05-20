from sqlalchemy import (
    Column,
    Integer,
    Float,
    ForeignKey
)

from app.database.database import (
    Base
)


class TicketItem(Base):

    __tablename__ = "ticket_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    ticket_id = Column(
        Integer,
        ForeignKey("tickets.id")
    )

    product_id = Column(
        Integer
    )

    quantity = Column(
        Float,
        default=0
    )

    price = Column(
        Float,
        default=0
    )

    subtotal = Column(
        Float,
        default=0
    )