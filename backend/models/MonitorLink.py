"""Monitor Link Model for linking monitors that represent the same person"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    String,
    UniqueConstraint
)
from database_connect import Base


class MonitorLink(Base):
    """
    Model for linking monitors that represent the same person.
    
    This allows multiple monitor records (with different spellings/names)
    to be viewed as a single person's incarceration history.
    """

    __tablename__ = "monitor_links"
    __table_args__ = (
        UniqueConstraint("primary_monitor_id", "linked_monitor_id", name="unique_monitor_link"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    primary_monitor_id = Column(Integer, ForeignKey("monitors.idmonitors"), nullable=False)
    linked_monitor_id = Column(Integer, ForeignKey("monitors.idmonitors"), nullable=False)
    linked_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    link_reason = Column(String(500), nullable=True)  # Optional reason for the link
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "primary_monitor_id": self.primary_monitor_id,
            "linked_monitor_id": self.linked_monitor_id,
            "linked_by_user_id": self.linked_by_user_id,
            "link_reason": self.link_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
