"""Monitor Inmate Link Model for manually associating monitors with specific inmate records"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    String,
    Boolean,
    UniqueConstraint
)
from database_connect import Base


class MonitorInmateLink(Base):
    """
    Model for manually linking monitors to specific inmate records.
    
    This allows users to manually associate or disassociate inmate records
    with monitors, handling false positives and missed matches.
    """

    __tablename__ = "monitor_inmate_links"
    __table_args__ = (
        UniqueConstraint("monitor_id", "inmate_id", name="unique_monitor_inmate_link"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    monitor_id = Column(Integer, ForeignKey("monitors.idmonitors"), nullable=False)
    inmate_id = Column(Integer, ForeignKey("inmates.idinmates"), nullable=False)
    linked_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_excluded = Column(Boolean, nullable=False, default=False)  # True = exclude this record, False = include this record
    link_reason = Column(String(500), nullable=True)  # Reason for inclusion/exclusion
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "monitor_id": self.monitor_id,
            "inmate_id": self.inmate_id,
            "linked_by_user_id": self.linked_by_user_id,
            "is_excluded": self.is_excluded,
            "link_reason": self.link_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
