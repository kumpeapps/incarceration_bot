"""Jail Model"""

from dataclasses import dataclass
from datetime import date
from loguru import logger
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
)
from database_connect import Base


@dataclass
class Jail(Base):  # type: ignore
    """Jail

    Attributes:
        id (Optional[int]): The unique identifier of the jail.
        jail_name (str): The name of the jail.
        state (str): The state where the jail is located.
        jail_id (str): The unique identifier for the jail.
        scrape_system (str): The system used for scraping data.
        active (bool): Whether the jail is active.
        created_date (date): The date the jail record was created.
        updated_date (date): The date the jail record was last updated.
        last_scrape_date (Optional[date]): The date the jail was last scraped.
    """

    __tablename__ = "jails"

    id = Column(
        "idjails", Integer, primary_key=True, autoincrement=True, nullable=False
    )
    jail_name = Column(String(255), nullable=False, unique=True)
    state = Column(String(2), nullable=False)
    jail_id = Column(String(255), nullable=False, unique=True)
    scrape_system = Column(String(255), nullable=False)
    active = Column(Boolean, nullable=False, default=False)
    created_date = Column(Date, nullable=False, default=date.today())
    updated_date = Column(Date, nullable=False, default=date.today())
    last_scrape_date = Column(Date, nullable=True)
    version = Column(String(10), nullable=True, default="1.0")

    inmates = relationship("Inmate", back_populates="jail")

    def to_dict(self) -> dict:
        """Converts the object to a dictionary"""
        return {
            "id": self.id,
            "jail_name": self.jail_name,
            "state": self.state,
            "jail_id": self.jail_id,
            "scrape_system": self.scrape_system,
            "active": self.active,
            "created_date": self.created_date.isoformat(),
            "updated_date": self.updated_date.isoformat(),
            "last_scrape_date": (
                self.last_scrape_date.isoformat() if self.last_scrape_date else None
            ),
        }

    def __str__(self) -> str:
        return str(self.jail_name)

    def __bool__(self) -> bool:
        return bool(self.active)

    def update_last_scrape_date(self):
        """Update the last scrape date"""
        logger.info(f"Updating last scrape date for {self.jail_name}")
        self.last_scrape_date = date.today()
