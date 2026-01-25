"""
Event model for storing event information.
"""

from typing import ClassVar

from sqlalchemy import Column, Date, Integer, String, Text, Time

from .base import Base, TimestampMixin


class Event(Base, TimestampMixin):
    """
    Event model representing an event in the system.

    Attributes:
        id: Unique identifier for the event
        title: Title of the event
        description: Detailed description of the event
        date: Date when the event takes place
        time: Time when the event starts
        location: Physical location of the event
        image: Filename/path of the event image
        created_at: Timestamp when the event was created
        updated_at: Timestamp when the event was last updated
    """

    __tablename__ = "events"
    __table_args__ = {"schema": "temp"}

    id: ClassVar[Column] = Column(Integer, primary_key=True, autoincrement=True)
    title: ClassVar[Column] = Column(String(255), nullable=False, index=True)
    description: ClassVar[Column] = Column(Text, nullable=False)
    date: ClassVar[Column] = Column(Date, nullable=False, index=True)
    time: ClassVar[Column] = Column(Time, nullable=False)
    location: ClassVar[Column] = Column(String(500), nullable=False, index=True)
    image: ClassVar[Column] = Column(String(255), nullable=False)

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, title='{self.title}', date={self.date})>"

    def to_dict(self) -> dict:
        """Convert event object to dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "date": self.date.isoformat() if self.date else None,
            "time": self.time.isoformat() if self.time else None,
            "location": self.location,
            "image": self.image,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_summary_dict(self) -> dict:
        """Convert event object to summary dictionary (for list views)."""
        return {
            "id": str(self.id),
            "title": self.title,
            "image": self.image,
            "date": self.date.isoformat() if self.date else None,
            "location": self.location,
        }
