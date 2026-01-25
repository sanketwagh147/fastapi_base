"""
Image model for storing image metadata.
"""

from sqlalchemy import Column, Integer, String

from .base import Base, TimestampMixin


class Image(Base, TimestampMixin):
    """
    Image model representing an image in the system.

    Attributes:
        id: Unique identifier for the image
        path: Filename/path of the image
        caption: Description or caption for the image
        created_at: Timestamp when the image was added
        updated_at: Timestamp when the image was last updated
    """

    __tablename__ = "images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String(500), nullable=False, unique=True, index=True)
    caption = Column(String(1000), nullable=True)

    def __repr__(self):
        return f"<Image(id={self.id}, path='{self.path}')>"

    def to_dict(self):
        """Convert image object to dictionary."""
        return {
            "id": self.id,
            "path": self.path,
            "caption": self.caption,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
