"""Session Model for tracking user login activity"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Text
)
from sqlalchemy.orm import relationship
from database_connect import Base


class Session(Base):
    """
    Session model for tracking user login activity.

    Attributes:
        id (int): Unique identifier for the session.
        user_id (int): Foreign key to the user.
        session_token (str): JWT token or session identifier.
        login_time (datetime): When the session was created/user logged in.
        logout_time (datetime): When the session ended/user logged out.
        ip_address (str): IP address of the user's login.
        user_agent (str): Browser/client user agent string.
        is_active (bool): Whether the session is still active.
        created_at (datetime): When the session record was created.
        updated_at (datetime): When the session record was last updated.
    """

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), nullable=False, unique=True)
    login_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    logout_time = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 can be up to 45 chars
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="sessions")

    def to_dict(self) -> dict:
        """Convert the session to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_token": self.session_token,
            "login_time": self.login_time.isoformat() if self.login_time else None,
            "logout_time": self.logout_time.isoformat() if self.logout_time else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def end_session(self):
        """Mark the session as ended."""
        self.is_active = False
        self.logout_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
