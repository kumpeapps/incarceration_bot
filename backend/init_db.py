#!/usr/bin/env python3
"""
Database initialization and migration script.
Runs automatically on container startup to ensure database is up to date.
Uses proper Alembic for database-agnostic migrations.
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, '/app')

# Configure logging first
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import from the alembic utils package  
try:
    from alembic.utils import check_multiple_heads, merge_heads_safely
    alembic_utils_available = True
except ImportError as e:
    logger.warning("Could not import alembic utils: %s", e)
    alembic_utils_available = False

# Add environment variable to control auto-merge behavior
ALLOW_AUTO_MERGE = os.getenv('ALEMBIC_ALLOW_AUTO_MERGE', 'false').lower() == 'true'

def wait_for_database(max_retries=30, delay=2):
    """Wait for database to be available."""
    from database_connect import new_session
    from sqlalchemy.exc import OperationalError
    from sqlalchemy import text
    
    for attempt in range(max_retries):
        try:
            session = new_session()
            session.execute(text("SELECT 1"))
            session.close()
            logger.info("Database connection successful")
            return True
        except OperationalError as e:
            logger.warning(f"Database not ready (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Unexpected database error: {e}")
            time.sleep(delay)
    
    logger.error("Failed to connect to database after all retries")
    return False

def run_alembic_migrations():
    """Run Alembic migrations to update database schema."""
    try:
        from alembic.config import Config
        from alembic import command
        
        # Set up Alembic configuration
        alembic_cfg = Config('/app/alembic.ini')
        
        logger.info("Running Alembic migrations...")
        
        # Check for multiple heads using the shared utility
        if alembic_utils_available:
            has_multiple, heads = check_multiple_heads()
            if has_multiple:
                logger.warning("Multiple Alembic heads detected (%d heads)", len(heads))
                
                if ALLOW_AUTO_MERGE:
                    logger.info("Auto-merge is enabled, attempting to merge heads...")
                    if not merge_heads_safely(allow_auto_merge=True):
                        logger.error("Auto-merge failed, halting startup for safety")
                        return False
                else:
                    logger.error("Multiple heads detected but auto-merge is disabled")
                    logger.error("Set ALEMBIC_ALLOW_AUTO_MERGE=true to enable auto-merge")
                    logger.error("Or resolve manually:")
                    logger.error("  docker-compose exec backend_api alembic merge -m 'merge heads' heads")
                    logger.error("  docker-compose exec backend_api alembic upgrade head")
                    logger.error("Halting startup to prevent database inconsistencies")
                    return False
        
        # Run migrations to head
        command.upgrade(alembic_cfg, 'head')
        
        logger.info("Alembic migrations completed successfully")
        return True
        
    except Exception as e:
        logger.error("Alembic migration failed: %s", e)
        
        # Check if this is a multiple heads error
        error_str = str(e).lower()
        if 'multiple head revisions' in error_str:
            logger.error("Multiple head revisions detected in migration error")
            logger.error("Halting startup to prevent database inconsistencies")
            logger.error("Please resolve manually:")
            logger.error("  docker-compose exec backend_api alembic merge -m 'merge heads' heads")
            logger.error("  docker-compose exec backend_api alembic upgrade head")
            return False
        
        # For other errors, fall back to manual migration
        logger.info("Attempting manual migration as fallback...")
        return run_manual_migration_fallback()

def run_manual_migration_fallback():
    """Fallback manual migration if Alembic is not available."""
    from database_connect import new_session
    from sqlalchemy import text, inspect
    
    session = new_session()
    try:
        inspector = inspect(session.bind)
        
        # Check if inmates table exists
        tables = inspector.get_table_names()
        if 'inmates' not in tables:
            logger.error("Inmates table not found - database schema not properly initialized")
            return False
        
        columns = inspector.get_columns('inmates')
        column_names = [col['name'] for col in columns]
        
        # Check if last_seen column exists
        if 'last_seen' not in column_names:
            logger.info("Adding last_seen column to inmates table (manual fallback)")
            
            # Add the column using database-agnostic SQLAlchemy
            from sqlalchemy import Column, DateTime
            from sqlalchemy.schema import AddConstraint
            
            # Get the database dialect
            dialect = session.bind.dialect.name
            
            if dialect == 'mysql':
                session.execute(text('ALTER TABLE inmates ADD COLUMN last_seen DATETIME NULL'))
            elif dialect == 'postgresql':
                session.execute(text('ALTER TABLE inmates ADD COLUMN last_seen TIMESTAMP NULL'))
            elif dialect == 'sqlite':
                session.execute(text('ALTER TABLE inmates ADD COLUMN last_seen DATETIME NULL'))
            else:
                # Generic SQL for other databases
                session.execute(text('ALTER TABLE inmates ADD COLUMN last_seen TIMESTAMP NULL'))
            
            session.commit()
            logger.info("last_seen column added successfully")
            
            # Update existing records
            logger.info("Updating existing records with last_seen data...")
            result = session.execute(text('''
                UPDATE inmates 
                SET last_seen = in_custody_date 
                WHERE last_seen IS NULL 
                AND (release_date IS NULL OR release_date = '')
            '''))
            session.commit()
            logger.info(f"Updated {result.rowcount} records with last_seen data")
            
        else:
            logger.info("last_seen column already exists, skipping manual migration")
            
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"Manual migration failed: {e}")
        # Don't raise - continue with startup even if migration fails
        logger.info("Continuing with startup despite migration failure")
        return False
    finally:
        session.close()

def initialize_database():
    """Initialize database with all necessary tables and data."""
    try:
        from database_connect import Base, new_session
        # Import all models to ensure they're registered with Base
        from models.Inmate import Inmate
        from models.Jail import Jail
        from models.Monitor import Monitor
        
        logger.info("Initializing database schema...")
        
        session = new_session()
        # Create all tables using SQLAlchemy metadata
        logger.info(f"Creating tables: {[table.name for table in Base.metadata.tables.values()]}")
        Base.metadata.create_all(session.bind)
        session.close()
        logger.info("Database schema initialization completed")
        
        # Run Alembic migrations
        if not run_alembic_migrations():
            logger.warning("Alembic migrations failed, but continuing with startup")
        
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main initialization function."""
    logger.info("Starting database initialization...")
    
    # Wait for database to be available
    if not wait_for_database():
        logger.error("Database initialization failed - cannot connect to database")
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        logger.error("Database initialization failed")
        sys.exit(1)
    
    logger.info("Database initialization completed successfully")

if __name__ == "__main__":
    main()
