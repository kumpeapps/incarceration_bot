"""Group Model"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from database_connect import Base


class Group(Base):
    """
    Group model for role-based access control.

    Attributes:
        id (int): Unique identifier for the group.
        name (str): Group name (e.g., 'admin', 'user', 'moderator').
        display_name (str): Human-readable display name.
        description (str): Description of the group's purpose.
        is_active (bool): Whether the group is active.
        created_at (datetime): When the group was created.
        updated_at (datetime): When the group was last updated.
    """

    __tablename__ = "groups"
    __table_args__ = (
        UniqueConstraint("name", name="unique_group_name"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(50), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to user groups
    user_groups = relationship("UserGroup", back_populates="group", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """Convert the group to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
