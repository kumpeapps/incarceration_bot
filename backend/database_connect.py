import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

# Database-agnostic configuration
db_host: str = os.getenv('DB_HOST', 'db')
db_port: str = os.getenv('DB_PORT', '3306')
db_user: str = os.getenv('DB_USER', 'user')
db_password: str = os.getenv('DB_PASSWORD', 'password')
db_name: str = os.getenv('DB_NAME', 'incarceration_db')
db_type: str = os.getenv('DB_TYPE', 'mysql')

# Legacy MySQL environment variables for backwards compatibility
mysql_server: str = os.getenv("MYSQL_SERVER", db_host)
mysql_username: str = os.getenv("MYSQL_USERNAME", db_user)
mysql_password: str = os.getenv("MYSQL_PASSWORD", db_password)
mysql_database: str = os.getenv("MYSQL_DATABASE", db_name)
mysql_port: str = os.getenv("MYSQL_PORT", db_port)

# Construct database URI based on database type
def get_database_uri() -> str:
    """Get database-agnostic connection URI."""
    if db_type == 'mysql':
        return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    elif db_type == 'postgresql':
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    elif db_type == 'sqlite':
        return f"sqlite:///{db_name}.db"
    else:
        # Default to MySQL for backwards compatibility with legacy config
        return f"mysql+pymysql://{mysql_username}:{mysql_password}@{mysql_server}:{mysql_port}/{mysql_database}"

database_uri: str = os.getenv("DATABASE_URI", get_database_uri())

Base = declarative_base()

def new_session() -> Session:
    """Create a new session"""
    db = create_engine(database_uri)
    Base.metadata.create_all(db)
    Session = sessionmaker(bind=db)
    return Session()
