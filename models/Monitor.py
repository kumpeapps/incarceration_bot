"""Monitor Model"""

import os
import json
import requests # type: ignore
from loguru import logger
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Date,
    TIMESTAMP
)
from database_connect import Base
from models.Inmate import Inmate


class Monitor(Base):
    """
    Monitor model representing an individual who is to be monitored for arrest.

    Attributes:
        id (int): Unique identifier for the monitor.
        name (str): Name of the individual.
        arrest_date (str): Date of arrest.
        release_date (str): Date of release.
        arrest_reason (str): Reason for the arrest.
        arresting_agency (str): Agency that made the arrest.
        jail (str): Jail where the individual is held.
        mugshot (bytes): Mugshot of the individual.
        notify_method (str): Method of notification (e.g., pushover).
        notify_address (str): Address/Key for notification.
    """

    __tablename__ = "monitors"
    __table_args__ = (
        UniqueConstraint("name", "notify_address", name="unique_monitor"),
    )

    id = Column(
        "idmonitors", Integer, primary_key=True, autoincrement=True, nullable=False
    )
    name = Column(String(255), nullable=False)
    arrest_date = Column(Date, nullable=True)
    release_date = Column(String(255), nullable=True)
    arrest_reason = Column(String(255), nullable=True)
    arresting_agency = Column(String(255), nullable=True)
    jail = Column(String(255), nullable=True)
    mugshot = Column(Text(65535), nullable=True)
    enable_notifications = Column(Integer, nullable=False, default=1)
    notify_method = Column(String(255), nullable=True, default="pushover")
    notify_address = Column(String(255), nullable=False, default="")
    last_seen_incarcerated = Column(TIMESTAMP, nullable=True, default=None)

    def to_dict(self) -> dict:
        """Converts the object to a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "arrest_date": self.arrest_date,
            "release_date": self.release_date,
            "arrest_reason": self.arrest_reason,
            "arresting_agency": self.arresting_agency,
            "jail": self.jail,
            "mugshot": self.mugshot,
            "enable_notifications": self.enable_notifications,
            "notify_method": self.notify_method,
            "notify_address": self.notify_address,
            "last_seen_incarcerated": self.last_seen_incarcerated,
        }

    def send_message(self, inmate: Inmate, released: bool = False):
        """Send a message to the monitor"""

        def send_pushover(self):
            """Send a message via Pushover"""
            logger.info(f"Sending Pushover notification.")
            user_key = self.notify_address
            pushover_api_key = os.getenv("PUSHOVER_API_KEY", "")
            pushover_sound = os.getenv("PUSHOVER_SOUND", "default")
            pushover_priority = os.getenv("PUSHOVER_PRIORITY", "1")
            title = (
                f"{inmate.name} has been released"
                if released
                else f"{inmate.name} has been arrested"
            )
            message = (
                f"{inmate.name} has been released" if released else f"{inmate.name} has been arrested by {inmate.held_for_agency} for {inmate.hold_reasons}"

            )
            if pushover_api_key == "":
                raise ValueError("Pushover API Key not set")
            try:
                _ = requests.post(
                    url="https://api.pushover.net/1/messages.json",
                    headers={
                        "Content-Type": "application/json; charset=utf-8",
                    },
                    data=json.dumps(
                        {
                            "sound": pushover_sound,
                            "message": message,
                            "title": title,
                            "priority": pushover_priority,
                            "token": pushover_api_key,
                            "user": user_key,
                            "attachment_base64": inmate.mugshot,
                            "attachment_type": "image/jpeg",
                        }
                    ),
                    timeout=10,
                )
            except requests.exceptions.RequestException as e:
                logger.exception(f"Error sending Pushover notification: {e}")

        def send_email(self):
            """Send a message via email"""
            raise NotImplementedError("Email not implemented")

        def send_sms(self):
            """Send a message via SMS"""
            raise NotImplementedError("SMS not implemented")

        if self.enable_notifications:
            if self.notify_method == "pushover":
                send_pushover(self)
            elif self.notify_method == "email":
                send_email(self)
            elif self.notify_method == "sms":
                send_sms(self)
            else:
                raise ValueError("Invalid notification method")
        else:
            print(f"Notifications disabled for {self.name}")

    def send_pushover(self, user_key: str, title: str, message: str):
        """Send a message via Pushover"""
        raise NotImplementedError("Pushover not implemented")

    def send_email(self, email: str, title: str, message: str):
        """Send a message via email"""
        raise NotImplementedError("Email not implemented")

    def send_sms(self, phone_number: str, message: str):
        """Send a message via SMS"""
        raise NotImplementedError("SMS not implemented")
