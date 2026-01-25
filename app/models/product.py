"""
Order model for storing order information.
"""

from typing import ClassVar

from sqlalchemy import Column, Integer, Numeric, String

from .base import Base


class Product(Base):
    """
    Product model representing a product in the system.

    Attributes:
        id: Unique identifier for the product
        name: Name of the product
        department: Department associated with the product
        price: Price of the product
        weight: Weight of the product
        created_at: Timestamp when the product was created
        updated_at: Timestamp when the product was last updated
    """

    __tablename__ = "products"
    __table_args__ = {"schema": "temp"}

    id: ClassVar[Column] = Column(Integer, primary_key=True, autoincrement=True)
    name: ClassVar[Column] = Column(String(255), nullable=False, index=True)
    department: ClassVar[Column] = Column(String(255), nullable=False, index=True)
    price: ClassVar[Column] = Column(Numeric(10, 2), nullable=False)
    weight: ClassVar[Column] = Column(Numeric(10, 2), nullable=False)

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, name='{self.name}', department='{self.department}')>"

    def to_dict(self) -> dict:
        """Convert order object to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "department": self.department,
            "price": float(self.price) if self.price else None,
            "weight": float(self.weight) if self.weight else None,
        }

    def to_summary_dict(self) -> dict:
        """Convert product object to summary dictionary (for list views)."""
        return {
            "id": self.id,
            "name": self.name,
            "department": self.department,
            "price": float(self.price) if self.price else None,
        }
