"""Models package initialization - imports all models to ensure they're registered with SQLAlchemy"""

# Import all models to ensure they're registered with SQLAlchemy
from models.User import User
from models.Group import Group
from models.UserGroup import UserGroup
from models.Inmate import Inmate
from models.Jail import Jail
from models.Monitor import Monitor
from models.MonitorInmateLink import MonitorInmateLink
from models.MonitorLink import MonitorLink

# Make all models available when importing from models
__all__ = [
    'User',
    'Group', 
    'UserGroup',
    'Inmate',
    'Jail',
    'Monitor',
    'MonitorInmateLink',
    'MonitorLink'
]
