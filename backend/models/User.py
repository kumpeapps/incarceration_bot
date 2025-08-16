"""User Model"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from database_connect import Base
from passlib.context import CryptContext
from passlib.hash import bcrypt, md5_crypt, phpass, argon2
import hashlib

pwd_context = CryptContext(schemes=["bcrypt", "argon2", "phpass"], deprecated="auto")


class User(Base):
    """
    User model for authentication and authorization.

    Attributes:
        id (int): Unique identifier for the user.
        username (str): Unique username.
        email (str): User email address.
        hashed_password (str): Bcrypt hashed password.
        is_active (bool): Whether the user account is active.
        created_at (datetime): When the user was created.
        updated_at (datetime): When the user was last updated.
    """

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="unique_username"),
        UniqueConstraint("email", name="unique_email"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    password_format = Column(String(20), nullable=False, default="bcrypt")
    api_key = Column(String(255), nullable=True, unique=True)
    amember_user_id = Column(Integer, nullable=True, unique=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user_groups = relationship("UserGroup", foreign_keys="UserGroup.user_id", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        return pwd_context.verify(password, self.hashed_password)
    
    def verify_password_with_format(self, password: str, password_format: str = "bcrypt") -> bool:
        """Verify a password against the stored hash with specific format."""
        if password_format == "bcrypt":
            return pwd_context.verify(password, self.hashed_password)
        elif password_format == "phpass":
            # aMember/WordPress phpass format
            try:
                return phpass.verify(password, self.hashed_password)
            except (ValueError, TypeError):
                return False
        elif password_format in ["argon2i", "argon2id", "argon2"]:
            # PHP password_hash() argon2 formats
            try:
                return argon2.verify(password, self.hashed_password)
            except (ValueError, TypeError):
                return False
        elif password_format == "md5":
            # Simple MD5 hash
            return hashlib.md5(password.encode()).hexdigest() == self.hashed_password
        elif password_format == "sha1":
            # Simple SHA1 hash
            return hashlib.sha1(password.encode()).hexdigest() == self.hashed_password
        elif password_format == "crypt":
            # Unix crypt format
            try:
                return md5_crypt.verify(password, self.hashed_password)
            except (ValueError, TypeError):
                return False
        else:
            # Default to bcrypt for unknown formats
            return pwd_context.verify(password, self.hashed_password)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    def to_dict(self) -> dict:
        """Convert the user to a dictionary (excluding password)."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "api_key": self.api_key,
            "amember_user_id": self.amember_user_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.get_last_login(),
            "groups": [ug.group.to_dict() for ug in self.user_groups if ug.group and ug.group.is_active],
            "role": self.role,
        }

    def get_last_login(self) -> str | None:
        """Get the most recent login time from sessions."""
        if not self.sessions:
            return None
        
        # Get the most recent session
        latest_session = max(self.sessions, key=lambda s: s.login_time)
        return latest_session.login_time.isoformat() if latest_session.login_time else None

    def has_group(self, group_name: str) -> bool:
        """Check if user belongs to a specific group."""
        return any(ug.group.name == group_name and ug.group.is_active 
                  for ug in self.user_groups if ug.group)

    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.has_group("admin")

    def get_groups(self) -> list:
        """Get list of active groups user belongs to."""
        return [ug.group.name for ug in self.user_groups 
                if ug.group and ug.group.is_active]

    @property
    def role(self) -> str:
        """Backward compatibility property that returns 'admin' if user is admin, else 'user'."""
        return "admin" if self.is_admin() else "user"
