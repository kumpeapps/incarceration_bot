"""Inmate Model"""

from dataclasses import dataclass
from datetime import date
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Text,
)
from sqlalchemy.orm import relationship
from database_connect import Base


@dataclass
class Inmate(Base):  # type: ignore
    """Inmate Data

    Attributes:
        name (str): The name of the inmate.
        race (str): The race of the inmate.
        sex (str): The sex of the inmate.
        cell_block (str): The cell block where the inmate is held.
        arrest_date (str): The date of the inmate's arrest.
        held_for_agency (str): The agency for which the inmate is held.
        mugshot (str): BASE64 of the inmate's mugshot.
        dob (str): The date of birth of the inmate.
        hold_reasons (str): The reasons for holding the inmate.
        is_juvenile (bool): Whether the inmate is a juvenile.
        release_date (str): The date of the inmate's release.
    """

    __tablename__ = "inmates"
    __table_args__ = (
        UniqueConstraint(
            "jail_id",
            "arrest_date", 
            "name",
            "dob",
            "sex",
            "race",
            name="unique_inmate_optimized",
        ),
    )

    id = Column(
        "idinmates", Integer, primary_key=True, autoincrement=True, nullable=False
    )
    name = Column(String(255), nullable=False)
    race = Column(String(255), nullable=False, default="Unknown")
    sex = Column(String(255), nullable=False, default="Unknown")
    cell_block = Column(String(255), nullable=True)
    arrest_date = Column(Date, nullable=True)
    held_for_agency = Column(String(255), nullable=True)
    mugshot = Column(Text(65535), nullable=True)
    dob = Column(String(255), nullable=False, default="Unknown")
    hold_reasons = Column(String(1000), nullable=False, default="")  # Changed from Text to String with length
    is_juvenile = Column(Boolean, nullable=False, default=False)
    release_date = Column(String(255), nullable=False, default="")
    in_custody_date = Column(Date, nullable=False, default=date.today())
    last_seen = Column(DateTime, nullable=True)
    jail_id = Column(String(255), nullable=False)  # No FK constraint for partitioning compatibility
    hide_record = Column(Boolean, nullable=False, default=False)

    def __str__(self) -> str:
        return str(self.name)

    def to_dict(self) -> dict:
        """Converts the object to a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "race": self.race,
            "sex": self.sex,
            "cell_block": self.cell_block,
            "arrest_date": self.arrest_date.isoformat() if self.arrest_date else None,
            "held_for_agency": self.held_for_agency,
            "mugshot": self.mugshot,
            "dob": self.dob,
            "hold_reasons": self.hold_reasons,
            "is_juvenile": self.is_juvenile,
            "release_date": self.release_date,
            "in_custody_date": self.in_custody_date.isoformat() if self.in_custody_date else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "jail_id": self.jail_id,
            "hide_record": self.hide_record,
        }
