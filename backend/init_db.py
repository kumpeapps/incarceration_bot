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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        import subprocess
        
        # Set up Alembic configuration
        alembic_cfg = Config('/app/alembic.ini')
        
        logger.info("Running Alembic migrations...")
        
        # First, check if we have multiple heads
        try:
            heads_result = subprocess.run(['alembic', 'heads'], 
                                        capture_output=True, text=True, cwd='/app')
            if heads_result.returncode == 0:
                heads_output = heads_result.stdout.strip()
                head_lines = [line for line in heads_output.split('\n') if line.strip()]
                
                if len(head_lines) > 1:
                    logger.warning(f"Multiple Alembic heads detected ({len(head_lines)} heads)")
                    logger.info("Attempting to merge heads automatically...")
                    
                    # Try to merge heads
                    merge_result = subprocess.run([
                        'alembic', 'merge', '-m', 'auto-merge conflicting heads during startup', 'heads'
                    ], capture_output=True, text=True, cwd='/app')
                    
                    if merge_result.returncode == 0:
                        logger.info("✅ Heads merged successfully")
                        logger.info(f"Merge output: {merge_result.stdout}")
                    else:
                        logger.error(f"Failed to merge heads: {merge_result.stderr}")
                        logger.info("Attempting to use heads command as fallback...")
                        # Try upgrading to heads (all heads) instead of head
                        try:
                            command.upgrade(alembic_cfg, 'heads')
                            logger.info("Alembic migrations completed using 'heads' target")
                            return True
                        except Exception as heads_e:
                            logger.error(f"Failed to upgrade to heads: {heads_e}")
                            raise e
                else:
                    logger.info("Single head detected - proceeding normally")
        except Exception as check_e:
            logger.warning(f"Could not check heads: {check_e}, proceeding with normal upgrade")
        
        # Run migrations to head
        command.upgrade(alembic_cfg, 'head')
        
        logger.info("Alembic migrations completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Alembic migration failed: {e}")
        
        # Check if this is a multiple heads error
        error_str = str(e).lower()
        if 'multiple head revisions' in error_str:
            logger.error("Multiple head revisions detected - this needs to be resolved manually")
            logger.error("Container will continue startup but database may be inconsistent")
            logger.error("Please run: docker-compose exec backend_api alembic merge -m 'merge heads' heads")
            logger.error("Then run: docker-compose exec backend_api alembic upgrade head")
            # Don't fail startup completely - continue but log the issue
            return True
        
        # Fallback to manual migration if Alembic fails
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
