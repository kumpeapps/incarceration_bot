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
    """Create a new session with optimized settings for concurrent processing"""
    # Add connection pooling and isolation settings to prevent lock conflicts
    if db_type == 'mysql':
        # MySQL-specific optimizations for concurrent processing
        engine_kwargs = {
            'pool_size': 10,  # Larger pool for concurrent operations
            'max_overflow': 20,  # Additional connections when needed
            'pool_timeout': 30,  # Timeout waiting for connection
            'pool_recycle': 3600,  # Recycle connections every hour
            'isolation_level': 'READ_COMMITTED',  # Reduce lock contention
            'echo': False,  # Set to True for debugging SQL queries
            'connect_args': {
                'connect_timeout': 10,  # Connection timeout
                'read_timeout': 30,     # Read timeout
                'write_timeout': 30,    # Write timeout
                'autocommit': False,    # Explicit transaction control
                'charset': 'utf8mb4'    # Full UTF-8 support
            }
        }
    else:
        # Default settings for other databases
        engine_kwargs = {
            'pool_size': 5,
            'max_overflow': 10,
            'pool_timeout': 30,
            'pool_recycle': 3600
        }
    
    db = create_engine(database_uri, **engine_kwargs)
    Base.metadata.create_all(db)
    Session = sessionmaker(
        bind=db, 
        expire_on_commit=False,  # Don't expire objects after commit
        autoflush=True,          # Auto-flush before queries
        autocommit=False         # Explicit transaction control
    )
    return Session()
