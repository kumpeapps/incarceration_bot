import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base


mysql_server: str = os.getenv("MYSQL_SERVER", "")
mysql_username: str = os.getenv("MYSQL_USERNAME", "Apps_JailDatabase")
mysql_password: str = os.getenv("MYSQL_PASSWORD", "")
mysql_database: str = os.getenv("MYSQL_DATABASE", "Apps_JailDatabase")
mysql_port: str = os.getenv("MYSQL_PORT", "3306")
database_uri: str = os.getenv(
    "DATABASE_URI",
    f"mysql+pymysql://{mysql_username}:{mysql_password}@{mysql_server}:{mysql_port}/{mysql_database}",
)

Base = declarative_base()

def new_session() -> Session:
    """Create a new session"""
    db = create_engine(database_uri)
    Base.metadata.create_all(db)
    Session = sessionmaker(bind=db)
    return Session()
