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
except ImportError:
    # Fallback to old location for backward compatibility
    try:
        import sys
        import os
        alembic_dir = os.path.join(os.path.dirname(__file__), 'alembic')
        if alembic_dir not in sys.path:
            sys.path.append(alembic_dir)
        from migration_utils import check_multiple_heads, merge_heads_safely
        alembic_utils_available = True
        logger.info("Using legacy migration_utils import")
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

def ensure_critical_schema_updates():
    """Ensure critical schema updates are applied (idempotent)."""
    from database_connect import new_session
    from sqlalchemy import text, inspect, Column, String, Integer
    from sqlalchemy.schema import CreateTable
    from sqlalchemy.exc import OperationalError
    
    session = new_session()
    try:
        logger.info("Ensuring critical schema updates are applied...")
        
        inspector = inspect(session.bind)
        
        # Ensure users table exists
        tables = inspector.get_table_names()
        if 'users' not in tables:
            logger.warning("Users table does not exist - will be created by migrations")
            return True
        
        # Check and add api_key column if missing
        columns = inspector.get_columns('users')
        column_names = [col['name'] for col in columns]
        
        updates_applied = False
        
        if 'api_key' not in column_names:
            logger.info("Adding api_key column to users table")
            try:
                # Use SQLAlchemy DDL operations for database agnosticism
                from sqlalchemy import DDL
                ddl = DDL("ALTER TABLE users ADD COLUMN api_key %(api_key_type)s NULL")
                
                # Get database-specific type for VARCHAR(255)
                dialect_name = session.bind.dialect.name
                if dialect_name == 'mysql':
                    api_key_type = 'VARCHAR(255)'
                elif dialect_name == 'postgresql':
                    api_key_type = 'VARCHAR(255)'
                elif dialect_name == 'sqlite':
                    api_key_type = 'TEXT'
                else:
                    api_key_type = 'VARCHAR(255)'
                
                session.execute(ddl, {'api_key_type': api_key_type})
                
                # Add unique constraint separately for better compatibility
                try:
                    constraint_ddl = DDL("ALTER TABLE users ADD CONSTRAINT uk_users_api_key UNIQUE (api_key)")
                    session.execute(constraint_ddl)
                except OperationalError as e:
                    if 'duplicate key' not in str(e).lower() and 'already exists' not in str(e).lower():
                        logger.warning(f"Could not add unique constraint to api_key: {e}")
                
                updates_applied = True
            except OperationalError as e:
                if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                    logger.info("✅ api_key column already exists (caught during creation)")
                else:
                    raise
        else:
            logger.info("✅ api_key column already exists in users table")
        
        if 'amember_user_id' not in column_names:
            logger.info("Adding amember_user_id column to users table")
            try:
                # Use SQLAlchemy DDL operations for database agnosticism
                from sqlalchemy import DDL
                ddl = DDL("ALTER TABLE users ADD COLUMN amember_user_id %(amember_id_type)s NULL")
                
                # Get database-specific type for INT
                dialect_name = session.bind.dialect.name
                if dialect_name == 'mysql':
                    amember_id_type = 'INT'
                elif dialect_name == 'postgresql':
                    amember_id_type = 'INTEGER'
                elif dialect_name == 'sqlite':
                    amember_id_type = 'INTEGER'
                else:
                    amember_id_type = 'INTEGER'
                
                session.execute(ddl, {'amember_id_type': amember_id_type})
                
                # Add unique constraint separately for better compatibility
                try:
                    constraint_ddl = DDL("ALTER TABLE users ADD CONSTRAINT uk_users_amember_user_id UNIQUE (amember_user_id)")
                    session.execute(constraint_ddl)
                except OperationalError as e:
                    if 'duplicate key' not in str(e).lower() and 'already exists' not in str(e).lower():
                        logger.warning(f"Could not add unique constraint to amember_user_id: {e}")
                
                updates_applied = True
            except OperationalError as e:
                if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                    logger.info("✅ amember_user_id column already exists (caught during creation)")
                else:
                    raise
        else:
            logger.info("✅ amember_user_id column already exists in users table")
        
        if 'password_format' not in column_names:
            logger.info("Adding password_format column to users table")
            try:
                # Use SQLAlchemy DDL operations for database agnosticism
                from sqlalchemy import DDL
                ddl = DDL("ALTER TABLE users ADD COLUMN password_format %(password_format_type)s NOT NULL DEFAULT 'bcrypt'")
                
                # Get database-specific type for VARCHAR(20)
                dialect_name = session.bind.dialect.name
                if dialect_name == 'mysql':
                    password_format_type = 'VARCHAR(20)'
                elif dialect_name == 'postgresql':
                    password_format_type = 'VARCHAR(20)'
                elif dialect_name == 'sqlite':
                    password_format_type = 'VARCHAR(20)'
                else:
                    password_format_type = 'VARCHAR(20)'
                
                session.execute(ddl, {'password_format_type': password_format_type})
                updates_applied = True
            except OperationalError as e:
                if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                    logger.info("✅ password_format column already exists (caught during creation)")
                else:
                    raise
        else:
            logger.info("✅ password_format column already exists in users table")
        
        if updates_applied:
            session.commit()
            logger.info("✅ Critical schema updates applied successfully")
        else:
            logger.info("✅ All critical schema updates already present")
        
        # Fix alembic version if it's broken
        try:
            result = session.execute(text("SELECT version_num FROM alembic_version")).fetchone()
            if result and result[0] == '6049d5bb7db9':
                logger.info("Fixing broken alembic version")
                session.execute(text("UPDATE alembic_version SET version_num = 'a9f5f7465f50'"))
                session.commit()
                logger.info("✅ Fixed alembic version")
        except Exception as e:
            logger.debug(f"Alembic version check failed (expected if table doesn't exist): {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to ensure critical schema updates: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def run_alembic_migrations():
    """Run Alembic migrations to update database schema."""
    try:
        # First, ensure critical schema updates are applied safely
        if not ensure_critical_schema_updates():
            logger.error("Critical schema updates failed")
            return False
            
        # Ensure monitors table schema is up to date
        if not ensure_monitors_schema():
            logger.warning("Monitors schema update failed, but continuing...")
            
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
        
        # Check if this is a broken revision error
        if "can't locate revision identified by" in error_str:
            logger.warning("Broken revision detected, attempting to fix...")
            try:
                from alembic.config import Config
                from alembic import command
                
                alembic_cfg = Config('/app/alembic.ini')
                # Stamp to head to fix broken revision
                command.stamp(alembic_cfg, 'head')
                logger.info("Fixed broken revision, trying upgrade again...")
                command.upgrade(alembic_cfg, 'head')
                logger.info("Alembic migrations completed successfully after revision fix")
                return True
            except Exception as fix_error:
                logger.error(f"Failed to fix broken revision: {fix_error}")
                return run_manual_migration_fallback()
        
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

def ensure_monitors_schema():
    """Ensure monitors table has all required columns from SQLAlchemy model."""
    logger.info("Ensuring monitors table schema is up to date...")
    
    from database_connect import new_session
    from sqlalchemy import text, inspect
    from sqlalchemy.exc import OperationalError
    
    session = new_session()
    try:
        inspector = inspect(session.bind)
        
        # Check if monitors table exists
        tables = inspector.get_table_names()
        if 'monitors' not in tables:
            logger.info("Monitors table not found - will be created by schema initialization")
            return True
        
        columns = inspector.get_columns('monitors')
        column_names = [col['name'] for col in columns]
        logger.info(f"Current monitors table columns: {column_names}")
        
        # Define required columns that should exist
        dialect = session.bind.dialect.name
        required_columns = {
            'arrest_date': 'DATE NULL',
            'arrest_reason': 'VARCHAR(255) NULL',
            'arresting_agency': 'VARCHAR(255) NULL',
            'mugshot': 'TEXT NULL',
            'enable_notifications': 'INTEGER NOT NULL DEFAULT 1',
            'notify_method': 'VARCHAR(255) NULL',
            'notify_address': 'VARCHAR(255) NOT NULL DEFAULT \'\'',
        }
        
        # Adjust column definitions for different databases
        if dialect == 'postgresql':
            required_columns['mugshot'] = 'TEXT NULL'
            required_columns['notify_method'] = 'VARCHAR(255) DEFAULT \'pushover\''
        elif dialect == 'sqlite':
            required_columns['arrest_date'] = 'DATE'
            
        missing_columns = []
        for col_name, col_def in required_columns.items():
            if col_name not in column_names:
                missing_columns.append((col_name, col_def))
        
        if not missing_columns:
            logger.info("✅ All required monitors table columns already exist")
            return True
        
        logger.info(f"Adding {len(missing_columns)} missing columns to monitors table...")
        
        # Add missing columns
        for col_name, col_def in missing_columns:
            try:
                logger.info(f"Adding column: {col_name}")
                sql = f"ALTER TABLE monitors ADD COLUMN {col_name} {col_def}"
                session.execute(text(sql))
                session.commit()
                logger.info(f"✅ Added {col_name} column successfully")
            except Exception as e:
                error_msg = str(e).lower()
                if 'duplicate' in error_msg or 'already exists' in error_msg:
                    logger.info(f"✅ {col_name} column already exists")
                else:
                    logger.warning(f"⚠️ Could not add {col_name} column: {e}")
                    # Continue with other columns
        
        # Try to add unique constraint if it doesn't exist
        try:
            if dialect != 'sqlite':  # SQLite doesn't support adding constraints easily
                session.execute(text("ALTER TABLE monitors ADD CONSTRAINT unique_monitor UNIQUE (name, notify_address)"))
                session.commit()
                logger.info("✅ Added unique constraint to monitors table")
        except Exception as e:
            error_msg = str(e).lower()
            if 'duplicate' in error_msg or 'already exists' in error_msg:
                logger.info("✅ Unique constraint already exists")
            else:
                logger.info(f"ℹ️ Could not add unique constraint: {e}")
                # This is not critical, continue
        
        logger.info("✅ Monitors table schema update completed")
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"Monitors schema update failed: {e}")
        return False
    finally:
        session.close()

def initialize_groups():
    """Initialize required groups in the database."""
    logger.info("Starting initialize_groups function...")
    from database_connect import new_session
    from sqlalchemy import text, inspect
    
    session = new_session()
    try:
        logger.info("Connected to database, checking for groups table...")
        # Check if groups table exists using SQLAlchemy inspector
        inspector = inspect(session.bind)
        tables = inspector.get_table_names()
        logger.info(f"Available tables: {tables}")
        
        if 'groups' not in tables:
            logger.info("Groups table doesn't exist, skipping group initialization")
            return
        
        logger.info("Groups table exists, ensuring all required groups are present...")
        
        # Define all required groups
        groups_data = [
            ('admin', 'Administrators', 'Full system access and user management'),
            ('user', 'Regular Users', 'Standard user access to monitor functionality'),
            ('moderator', 'Moderators', 'Enhanced access for content moderation'),
            ('api', 'API Users', 'Users who can request and use API keys'),
            ('guest', 'Guests', 'Limited access for guest users'),
            ('banned', 'Banned Users', 'No access to the system'),
            ('locked', 'Locked Users', 'User account has been locked')
        ]
        
        from datetime import datetime
        current_time = datetime.now()
        groups_added = 0
        
        for name, display_name, description in groups_data:
            # Check if this specific group already exists
            existing = session.execute(
                text("SELECT COUNT(*) FROM groups WHERE name = :name"),
                {'name': name}
            ).scalar()
            
            if existing == 0:
                logger.info(f"Creating missing group: {name}")
                insert_sql = """
                    INSERT INTO groups (name, display_name, description, is_active, created_at, updated_at)
                    VALUES (:name, :display_name, :description, 1, :created_at, :updated_at)
                """
                session.execute(text(insert_sql), {
                    'name': name,
                    'display_name': display_name,
                    'description': description,
                    'created_at': current_time,
                    'updated_at': current_time
                })
                groups_added += 1
            else:
                logger.info(f"Group already exists: {name}")
        
        if groups_added > 0:
            session.commit()
            logger.info(f"Added {groups_added} new groups to database")
        else:
            logger.info("All required groups already exist")
        
        # Verify all groups are present
        result = session.execute(text("SELECT name, display_name FROM groups ORDER BY name"))
        groups = result.fetchall()
        
        logger.info("Current groups in database:")
        for group in groups:
            logger.info(f"  - {group[0]}: {group[1]}")
            
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to initialize groups: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Don't raise - continue with startup even if group initialization fails
        logger.warning("Continuing with startup despite group initialization failure")
    finally:
        session.close()
        logger.info("initialize_groups function completed")

def initialize_database():
    """Initialize database with all necessary tables and data."""
    try:
        from database_connect import Base, database_uri
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        # Import all models to ensure they're registered with Base
        from models.Inmate import Inmate
        from models.Jail import Jail
        from models.Monitor import Monitor
        from models.Group import Group
        from models.UserGroup import UserGroup
        
        logger.info("Initializing database schema...")
        
        # Create database engine and session manually to avoid table creation conflicts
        engine = create_engine(database_uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Use clean schema approach instead of Base.metadata.create_all()
        # This handles partitioning and optimizations properly
        try:
            from create_clean_schema import create_complete_schema, initialize_groups
            logger.info("Using clean schema approach for database initialization...")
            
            # Create complete optimized schema with partitioning
            create_complete_schema(session)
            
            # Set up default groups
            initialize_groups(session)
            
            session.commit()
            logger.info("✅ Clean schema initialization completed successfully")
            
        except ImportError as import_error:
            # Only fall back if the clean schema module is genuinely missing
            logger.error(f"Clean schema module not available: {import_error}")
            logger.warning("Falling back to traditional table creation")
            logger.info(f"Creating tables: {[table.name for table in Base.metadata.tables.values()]}")
            # Use checkfirst=True to avoid "table already exists" errors
            Base.metadata.create_all(session.bind, checkfirst=True)
            
        except Exception as schema_error:
            # Check if it's a database connection error
            error_msg = str(schema_error).lower()
            if any(phrase in error_msg for phrase in ['can\'t connect', 'connection', 'timeout', 'host']):
                logger.error(f"Database connection error during clean schema: {schema_error}")
                raise  # Re-raise connection errors - don't fall back
            
            # Check if it's just table existence errors (safe to ignore)
            elif any(phrase in error_msg for phrase in ['already exists', 'duplicate', 'table exists']):
                logger.info("Tables already exist - clean schema completed")
                # Still set up groups if possible
                try:
                    initialize_groups(session)
                    session.commit()
                    logger.info("✅ Groups initialization completed")
                except Exception as group_error:
                    logger.warning(f"Group initialization failed: {group_error}")
            
            else:
                # For other errors, log and fall back carefully
                logger.error(f"Clean schema initialization error: {schema_error}")
                logger.warning("Falling back to traditional table creation")
                logger.info(f"Creating tables: {[table.name for table in Base.metadata.tables.values()]}")
                # Use checkfirst=True to avoid "table already exists" errors  
                Base.metadata.create_all(session.bind, checkfirst=True)
            
        session.close()
        logger.info("Database schema initialization completed")
        
        # Run Alembic migrations (only if not using clean schema)
        # Skip migrations when using clean schema to avoid conflicts
        try:
            from create_clean_schema import create_complete_schema
            logger.info("Clean schema detected - skipping Alembic migrations to avoid conflicts")
        except ImportError:
            logger.info("Running Alembic migrations...")
            if not run_alembic_migrations():
                logger.warning("Alembic migrations failed, but continuing with startup")
        
        # Ensure required groups exist (only if not already done by clean schema)
        try:
            from create_clean_schema import initialize_groups
            logger.info("Groups already initialized by clean schema")
        except ImportError:
            logger.info("About to initialize groups...")
            initialize_groups()
            logger.info("Group initialization completed")
        
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
