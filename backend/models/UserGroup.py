"""UserGroup Model for Many-to-Many relationship between Users and Groups"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from database_connect import Base


class UserGroup(Base):
    """
    UserGroup model for many-to-many relationship between users and groups.

    Attributes:
        id (int): Unique identifier for the user-group relationship.
        user_id (int): Foreign key to the user.
        group_id (int): Foreign key to the group.
        assigned_by (int): User ID who assigned this group relationship.
        created_at (datetime): When the relationship was created.
        updated_at (datetime): When the relationship was last updated.
    """

    __tablename__ = "user_groups"
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="unique_user_group"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="user_groups")
    group = relationship("Group", back_populates="user_groups")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])

    def to_dict(self) -> dict:
        """Convert the user-group relationship to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "group_id": self.group_id,
            "assigned_by": self.assigned_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "group": self.group.to_dict() if self.group else None,
        }
