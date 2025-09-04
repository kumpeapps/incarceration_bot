#!/usr/bin/env python3
"""
Clean Database Schema Initialization
This script replaces all migrations with a single comprehensive schema setup.
Designed for clean installations and resolving migration conflicts.
"""

import sys
import os
import logging
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, '/app')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_clean_schema():
    """Create complete database schema from scratch."""
    from database_connect import get_database_uri, new_session
    from sqlalchemy import text, inspect, create_engine
    
    logger.info("🗄️  Creating clean database schema...")
    
    # Create engine and session
    database_uri = get_database_uri()
    engine = create_engine(database_uri)
    session = new_session()
    
    try:
        # Check if we're dealing with a clean database
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if existing_tables:
            logger.info(f"Found existing tables: {existing_tables}")
        else:
            logger.info("Clean database detected - creating full schema")
        
        # Create all tables with complete schema
        create_complete_schema(session)
        
        # Set up default groups
        initialize_groups(session)
        
        session.commit()
        logger.info("✅ Clean schema creation completed successfully")
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Schema creation failed: {e}")
        raise
    finally:
        session.close()

def create_partitioned_inmates_table(session):
    """Create the inmates table with partitioning for MySQL."""
    from sqlalchemy import text
    
    logger.info("🔧 Creating partitioned inmates table for MySQL...")
    
    # First check if table exists
    check_table_sql = """
    SELECT COUNT(*) as count 
    FROM information_schema.tables 
    WHERE table_schema = DATABASE() AND table_name = 'inmates'
    """
    
    result = session.execute(text(check_table_sql)).fetchone()
    table_exists = result.count > 0
    
    if table_exists:
        # Check if it's already partitioned
        check_partition_sql = """
        SELECT COUNT(*) as count 
        FROM information_schema.partitions 
        WHERE table_schema = DATABASE() 
        AND table_name = 'inmates' 
        AND partition_name IS NOT NULL
        """
        
        partition_result = session.execute(text(check_partition_sql)).fetchone()
        is_partitioned = partition_result.count > 0
        
        if is_partitioned:
            logger.info("ℹ️  Inmates table already exists and is partitioned")
            return
        else:
            logger.info("⚠️  Inmates table exists but is NOT partitioned - recreating with partitions...")
            # Drop and recreate with partitioning
            session.execute(text("DROP TABLE inmates"))
            logger.info("🗑️  Dropped existing non-partitioned inmates table")
    
    logger.info("🏗️  Creating new partitioned inmates table...")
    
    # Create partitioned inmates table
    inmates_partitioned_sql = """
    CREATE TABLE inmates (
        idinmates INT NOT NULL AUTO_INCREMENT,
        name VARCHAR(255) NOT NULL,
        race VARCHAR(255) NOT NULL DEFAULT 'Unknown',
        sex VARCHAR(255) NOT NULL DEFAULT 'Unknown',
        cell_block VARCHAR(255) NULL,
        arrest_date DATE NULL,
        held_for_agency VARCHAR(255) NULL,
        mugshot TEXT NULL,
        dob VARCHAR(255) NOT NULL DEFAULT 'Unknown',
        hold_reasons VARCHAR(1000) NOT NULL DEFAULT '',
        is_juvenile BOOLEAN NOT NULL DEFAULT 0,
        release_date VARCHAR(255) NOT NULL DEFAULT '',
        in_custody_date DATE NOT NULL,
        last_seen DATETIME NULL,
        jail_id VARCHAR(255) NOT NULL,
        hide_record BOOLEAN NOT NULL DEFAULT 0,
        PRIMARY KEY (idinmates, jail_id),
        UNIQUE KEY unique_inmate_optimized (jail_id, arrest_date, name, dob, sex, race),
        KEY idx_jail_id (jail_id),
        KEY idx_last_seen (last_seen),
        KEY idx_jail_last_seen (jail_id, last_seen),
        KEY idx_arrest_date (arrest_date),
        KEY idx_name (name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    PARTITION BY KEY(jail_id)
    PARTITIONS 16
    """
    
    try:
        logger.info("📋 Executing CREATE TABLE with partitioning...")
        session.execute(text(inmates_partitioned_sql))
        logger.info("✅ Partitioned inmates table created successfully")
        
        # Verify partitioning
        verify_sql = """
        SELECT COUNT(*) as partition_count 
        FROM information_schema.partitions 
        WHERE table_schema = DATABASE() 
        AND table_name = 'inmates' 
        AND partition_name IS NOT NULL
        """
        
        verify_result = session.execute(text(verify_sql)).fetchone()
        partition_count = verify_result.partition_count
        logger.info(f"🎯 Verified: inmates table has {partition_count} partitions")
        
        if partition_count == 16:
            logger.info("🎉 SUCCESS: Inmates table properly partitioned with 16 hash partitions!")
            
            # List all partitions for confirmation
            list_partitions_sql = """
            SELECT 
                partition_name,
                partition_ordinal_position,
                table_rows
            FROM information_schema.partitions 
            WHERE table_schema = DATABASE() 
            AND table_name = 'inmates' 
            AND partition_name IS NOT NULL
            ORDER BY partition_ordinal_position
            """
            
            partitions = session.execute(text(list_partitions_sql)).fetchall()
            logger.info("📊 Partition details:")
            for partition in partitions:
                logger.info(f"   - {partition.partition_name}: position {partition.partition_ordinal_position}, rows: {partition.table_rows}")
                
        else:
            logger.error(f"❌ PARTITIONING FAILED: Expected 16 partitions, got {partition_count}")
        
    except Exception as e:
        logger.error(f"❌ Failed to create partitioned inmates table: {e}")
        logger.error(f"SQL attempted: {inmates_partitioned_sql[:200]}...")
        
        # Check if it's a partitioning-related error
        error_msg = str(e).lower()
        if any(phrase in error_msg for phrase in ['partition', 'not allowed', '1564']):
            logger.warning("🔄 Partitioning not supported by this MySQL configuration - creating regular table...")
            
            # Fallback to regular inmates table without partitioning
            inmates_regular_sql = """
            CREATE TABLE IF NOT EXISTS inmates (
                idinmates INT NOT NULL AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL,
                race VARCHAR(255) NOT NULL DEFAULT 'Unknown',
                sex VARCHAR(255) NOT NULL DEFAULT 'Unknown',
                cell_block VARCHAR(255) NULL,
                arrest_date DATE NULL,
                held_for_agency VARCHAR(255) NULL,
                mugshot TEXT NULL,
                dob VARCHAR(255) NOT NULL DEFAULT 'Unknown',
                hold_reasons VARCHAR(1000) NOT NULL DEFAULT '',
                is_juvenile BOOLEAN NOT NULL DEFAULT 0,
                release_date VARCHAR(255) NOT NULL DEFAULT '',
                in_custody_date DATE NOT NULL,
                last_seen DATETIME NULL,
                jail_id VARCHAR(255) NOT NULL,
                hide_record BOOLEAN NOT NULL DEFAULT 0,
                PRIMARY KEY (idinmates),
                UNIQUE KEY unique_inmate_optimized (jail_id, arrest_date, name, dob, sex, race),
                KEY idx_jail_id (jail_id),
                KEY idx_last_seen (last_seen),
                KEY idx_jail_last_seen (jail_id, last_seen),
                KEY idx_arrest_date (arrest_date),
                KEY idx_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            try:
                session.execute(text(inmates_regular_sql))
                logger.info("✅ Regular inmates table created successfully (without partitioning)")
                logger.info("ℹ️  Performance will still be good due to optimized indexes")
            except Exception as fallback_error:
                logger.error(f"❌ Even fallback table creation failed: {fallback_error}")
                raise
        else:
            # Re-raise non-partitioning errors
            raise


def create_complete_schema(session):
    """Create all tables with the complete, final schema."""
    from sqlalchemy import text
    
    logger.info("🚀 Creating complete database schema...")
    
    # Get database dialect for SQL variations
    dialect = session.bind.dialect.name
    logger.info(f"🔍 Database dialect detected: {dialect}")
    
    # Define SQL for each table based on our models
    schema_sql = get_schema_sql(dialect)
    
    # Create tables in dependency order:
    # 1. First create tables that don't depend on inmates
    # 2. Then create inmates table (with partitioning if MySQL)
    # 3. Finally create tables that depend on inmates
    
    # Phase 1: Independent tables (no foreign keys to inmates)
    independent_tables = ['users', 'groups', 'user_groups', 'jails', 'monitors', 'monitor_links', 'sessions']
    
    for table_name in independent_tables:
        if table_name in schema_sql:
            logger.info(f"📋 Creating table: {table_name}")
            try:
                session.execute(text(schema_sql[table_name]))
                logger.info(f"✅ Table {table_name} created successfully")
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    logger.info(f"ℹ️  Table {table_name} already exists, skipping")
                else:
                    logger.error(f"❌ Failed to create table {table_name}: {e}")
                    raise
    
    # Phase 2: Create inmates table (with partitioning if MySQL)
    if dialect == 'mysql':
        logger.info("🗂️  MySQL detected - setting up table partitioning...")
        create_partitioned_inmates_table(session)
    else:
        logger.info(f"ℹ️  Database dialect '{dialect}' does not support partitioning - creating regular inmates table")
        # For non-MySQL databases, create inmates table normally
        inmates_sql = f'''
            CREATE TABLE IF NOT EXISTS inmates (
                idinmates INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                name VARCHAR(255) NOT NULL,
                race VARCHAR(255) NOT NULL DEFAULT 'Unknown',
                sex VARCHAR(255) NOT NULL DEFAULT 'Unknown',
                cell_block VARCHAR(255) NULL,
                arrest_date DATE NULL,
                held_for_agency VARCHAR(255) NULL,
                mugshot TEXT NULL,
                dob VARCHAR(255) NOT NULL DEFAULT 'Unknown',
                hold_reasons VARCHAR(1000) NOT NULL DEFAULT '',
                is_juvenile INTEGER NOT NULL DEFAULT 0,
                release_date VARCHAR(255) NOT NULL DEFAULT '',
                in_custody_date DATE NOT NULL,
                last_seen DATETIME NULL,
                jail_id VARCHAR(255) NOT NULL,
                hide_record INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (jail_id) REFERENCES jails(jail_id),
                UNIQUE (jail_id, arrest_date, name, dob, sex, race)
            )
        '''
        
        try:
            session.execute(text(inmates_sql))
            logger.info("✅ Standard inmates table created for non-MySQL database")
        except Exception as e:
            if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                logger.info("ℹ️  Inmates table already exists")
            else:
                logger.error(f"❌ Failed to create inmates table: {e}")
                raise
    
    # Phase 3: Create tables that depend on inmates
    dependent_tables = ['monitor_inmate_links']
    
    for table_name in dependent_tables:
        if table_name in schema_sql:
            logger.info(f"📋 Creating table: {table_name}")
            try:
                session.execute(text(schema_sql[table_name]))
                logger.info(f"✅ Table {table_name} created successfully")
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    logger.info(f"ℹ️  Table {table_name} already exists, skipping")
                else:
                    logger.error(f"❌ Failed to create table {table_name}: {e}")
                    raise
    
    logger.info("🎉 Complete schema creation finished!")

def get_schema_sql(dialect):
    """Get complete schema SQL for all tables."""
    
    # Common SQL patterns
    if dialect == 'mysql':
        auto_increment = 'AUTO_INCREMENT'
        datetime_type = 'DATETIME'
        text_type = 'TEXT'
        boolean_type = 'BOOLEAN'
        timestamp_default = 'CURRENT_TIMESTAMP'
        timestamp_update = 'ON UPDATE CURRENT_TIMESTAMP'
    elif dialect == 'postgresql':
        auto_increment = 'SERIAL'
        datetime_type = 'TIMESTAMP'
        text_type = 'TEXT'
        boolean_type = 'BOOLEAN'
        timestamp_default = 'CURRENT_TIMESTAMP'
        timestamp_update = ''  # PostgreSQL handles this differently
    else:  # SQLite
        auto_increment = 'AUTOINCREMENT'
        datetime_type = 'DATETIME'
        text_type = 'TEXT'
        boolean_type = 'INTEGER'  # SQLite doesn't have native boolean
        timestamp_default = 'CURRENT_TIMESTAMP'
        timestamp_update = ''
    
    return {
        'users': f'''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY {auto_increment} NOT NULL,
                username VARCHAR(50) NOT NULL,
                email VARCHAR(255) NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                password_format VARCHAR(20) NOT NULL DEFAULT 'bcrypt',
                api_key VARCHAR(255) NULL,
                amember_user_id INTEGER NULL,
                is_active {boolean_type} NOT NULL DEFAULT 1,
                created_at {datetime_type} NOT NULL DEFAULT {timestamp_default},
                updated_at {datetime_type} NOT NULL DEFAULT {timestamp_default} {timestamp_update},
                UNIQUE KEY unique_username (username),
                UNIQUE KEY unique_email (email),
                UNIQUE KEY uk_users_api_key (api_key),
                UNIQUE KEY uk_users_amember_user_id (amember_user_id)
            )
        ''',
        
        'groups': f'''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY {auto_increment} NOT NULL,
                name VARCHAR(50) NOT NULL,
                display_name VARCHAR(100) NOT NULL,
                description VARCHAR(255) NULL,
                is_active {boolean_type} NOT NULL DEFAULT 1,
                created_at {datetime_type} NOT NULL DEFAULT {timestamp_default},
                updated_at {datetime_type} NOT NULL DEFAULT {timestamp_default} {timestamp_update},
                UNIQUE KEY unique_group_name (name)
            )
        ''',
        
        'user_groups': f'''
            CREATE TABLE IF NOT EXISTS user_groups (
                id INTEGER PRIMARY KEY {auto_increment} NOT NULL,
                user_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                created_at {datetime_type} NOT NULL DEFAULT {timestamp_default},
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
                UNIQUE KEY unique_user_group (user_id, group_id)
            )
        ''',
        
        'jails': f'''
            CREATE TABLE IF NOT EXISTS jails (
                idjails INTEGER PRIMARY KEY {auto_increment} NOT NULL,
                jail_name VARCHAR(255) NOT NULL,
                state VARCHAR(2) NOT NULL,
                jail_id VARCHAR(255) NOT NULL,
                scrape_system VARCHAR(255) NOT NULL,
                active {boolean_type} NOT NULL DEFAULT 0,
                created_date DATE NOT NULL,
                updated_date DATE NOT NULL,
                last_scrape_date DATE NULL,
                last_successful_scrape {datetime_type} NULL,
                UNIQUE KEY unique_jail_name (jail_name),
                UNIQUE KEY unique_jail_id (jail_id)
            )
        ''',
        
        # inmates table handled separately for partitioning
        
        'monitors': f'''
            CREATE TABLE IF NOT EXISTS monitors (
                idmonitors INTEGER PRIMARY KEY {auto_increment} NOT NULL,
                name VARCHAR(255) NOT NULL,
                race VARCHAR(255) NULL,
                sex VARCHAR(255) NULL,
                dob VARCHAR(255) NULL,
                last_seen_incarcerated {datetime_type} NULL,
                last_check {datetime_type} NULL,
                release_date VARCHAR(255) NULL,
                jail VARCHAR(255) NULL,
                user_id INTEGER NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''',
        
        'monitor_inmate_links': f'''
            CREATE TABLE IF NOT EXISTS monitor_inmate_links (
                id INTEGER PRIMARY KEY {auto_increment} NOT NULL,
                monitor_id INTEGER NOT NULL,
                inmate_id INTEGER NOT NULL,
                linked_by_user_id INTEGER NOT NULL,
                is_excluded {boolean_type} NOT NULL DEFAULT 0,
                link_reason VARCHAR(500) NULL,
                created_at {datetime_type} NOT NULL DEFAULT {timestamp_default},
                updated_at {datetime_type} NOT NULL DEFAULT {timestamp_default} {timestamp_update},
                FOREIGN KEY (monitor_id) REFERENCES monitors(idmonitors),
                FOREIGN KEY (linked_by_user_id) REFERENCES users(id),
                UNIQUE KEY unique_monitor_inmate_link (monitor_id, inmate_id)
            )
        ''',
        
        'monitor_links': f'''
            CREATE TABLE IF NOT EXISTS monitor_links (
                id INTEGER PRIMARY KEY {auto_increment} NOT NULL,
                monitor_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at {datetime_type} NOT NULL DEFAULT {timestamp_default},
                FOREIGN KEY (monitor_id) REFERENCES monitors(idmonitors),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE KEY unique_monitor_user_link (monitor_id, user_id)
            )
        ''',
        
        'sessions': f'''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY {auto_increment} NOT NULL,
                user_id INTEGER NOT NULL,
                session_token VARCHAR(255) NOT NULL,
                login_time {datetime_type} NOT NULL,
                logout_time {datetime_type} NULL,
                ip_address VARCHAR(45) NULL,
                user_agent {text_type} NULL,
                is_active {boolean_type} NOT NULL,
                created_at {datetime_type} NOT NULL,
                updated_at {datetime_type} NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE KEY unique_session_token (session_token)
            )
        '''
    }

def create_indexes(session):
    """Create all performance indexes."""
    from sqlalchemy import text
    logger.info("Creating performance indexes...")
    
    indexes = [
        # Inmates table indexes for performance
        "CREATE INDEX IF NOT EXISTS idx_inmates_last_seen ON inmates (last_seen)",
        "CREATE INDEX IF NOT EXISTS idx_inmates_jail_last_seen ON inmates (jail_id, last_seen)",
        "CREATE INDEX IF NOT EXISTS idx_inmates_jail_id ON inmates (jail_id)",
        "CREATE INDEX IF NOT EXISTS idx_inmates_name ON inmates (name)",
        "CREATE INDEX IF NOT EXISTS idx_inmates_arrest_date ON inmates (arrest_date)",
        
        # Monitors table indexes
        "CREATE INDEX IF NOT EXISTS idx_monitors_last_seen_incarcerated ON monitors (last_seen_incarcerated)",
        "CREATE INDEX IF NOT EXISTS idx_monitors_jail_last_seen_release ON monitors (jail, last_seen_incarcerated, release_date)",
        "CREATE INDEX IF NOT EXISTS idx_monitors_user_id ON monitors (user_id)",
        
        # Sessions table indexes
        "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_sessions_is_active ON sessions (is_active)",
        "CREATE INDEX IF NOT EXISTS idx_sessions_login_time ON sessions (login_time)",
        
        # User groups indexes
        "CREATE INDEX IF NOT EXISTS idx_user_groups_user_id ON user_groups (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_groups_group_id ON user_groups (group_id)",
    ]
    
    for index_sql in indexes:
        try:
            session.execute(text(index_sql))
            logger.info(f"✅ Index created: {index_sql.split('idx_')[1].split(' ')[0]}")
        except Exception as e:
            if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                logger.info(f"ℹ️  Index already exists, skipping")
            else:
                logger.warning(f"⚠️  Could not create index: {e}")

def apply_table_partitioning(session):
    """Apply table partitioning for performance optimization."""
    from sqlalchemy import text
    logger.info("Applying table partitioning for performance...")
    
    # Get database dialect
    dialect = session.bind.dialect.name
    
    if dialect != 'mysql':
        logger.info("ℹ️  Table partitioning only supported for MySQL, skipping")
        return
    
    try:
        # Check if inmates table is already partitioned
        result = session.execute(text("""
            SELECT COUNT(*) FROM information_schema.PARTITIONS 
            WHERE TABLE_NAME = 'inmates' 
            AND TABLE_SCHEMA = DATABASE()
            AND PARTITION_NAME IS NOT NULL
        """))
        
        partition_count = result.scalar()
        
        if partition_count > 0:
            logger.info(f"✅ Inmates table already partitioned ({partition_count} partitions)")
            return
        
        logger.info("🔧 Applying hash partitioning to inmates table by jail_id...")
        
        # Apply partitioning to existing table
        # Note: This requires a table rebuild, so we need to be careful with large datasets
        session.execute(text("""
            ALTER TABLE inmates PARTITION BY HASH(CRC32(jail_id)) PARTITIONS 16
        """))
        
        logger.info("✅ Successfully applied hash partitioning (16 partitions) to inmates table")
        
        # Verify partitioning was applied
        result = session.execute(text("""
            SELECT COUNT(*) FROM information_schema.PARTITIONS 
            WHERE TABLE_NAME = 'inmates' 
            AND TABLE_SCHEMA = DATABASE()
            AND PARTITION_NAME IS NOT NULL
        """))
        
        new_partition_count = result.scalar()
        logger.info(f"✅ Verified: inmates table now has {new_partition_count} partitions")
        
    except Exception as e:
        if 'already partitioned' in str(e).lower():
            logger.info("ℹ️  Inmates table already partitioned, skipping")
        else:
            logger.warning(f"⚠️  Could not apply table partitioning: {e}")
            logger.info("ℹ️  Continuing without partitioning - table will still function normally")

def initialize_groups(session):
    """Initialize all required groups."""
    logger.info("Initializing required groups...")
    
    groups_data = [
        ('admin', 'Administrators', 'Full system access and user management'),
        ('user', 'Regular Users', 'Standard user access to monitor functionality'),
        ('moderator', 'Moderators', 'Enhanced access for content moderation'),
        ('api', 'API Users', 'Users who can request and use API keys'),
        ('guest', 'Guests', 'Limited access for guest users'),
        ('banned', 'Banned Users', 'No access to the system'),
        ('locked', 'Locked Users', 'User account has been locked')
    ]
    
    from sqlalchemy import text
    current_time = datetime.now()
    
    for name, display_name, description in groups_data:
        # Check if group exists
        existing = session.execute(
            text("SELECT COUNT(*) FROM groups WHERE name = :name"),
            {"name": name}
        ).scalar()
        
        if existing == 0:
            # Insert new group
            session.execute(text("""
                INSERT INTO groups (name, display_name, description, is_active, created_at, updated_at)
                VALUES (:name, :display_name, :description, 1, :created_at, :updated_at)
            """), {
                "name": name,
                "display_name": display_name,
                "description": description,
                "created_at": current_time,
                "updated_at": current_time
            })
            logger.info(f"✅ Created group: {name}")
        else:
            logger.info(f"ℹ️  Group already exists: {name}")

def initialize_alembic_version(session):
    """Set up Alembic version table with final state."""
    logger.info("Initializing Alembic version state...")
    
    from sqlalchemy import text
    
    # Create alembic_version table if it doesn't exist
    try:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL,
                PRIMARY KEY (version_num)
            )
        """))
        
        # Check if there's already a version
        existing = session.execute(text("SELECT COUNT(*) FROM alembic_version")).scalar()
        
        if existing == 0:
            # Set to a final "clean_schema" version
            session.execute(text("""
                INSERT INTO alembic_version (version_num) VALUES ('clean_schema_v1')
            """))
            logger.info("✅ Set Alembic version to 'clean_schema_v1'")
        else:
            # Update existing version to clean state
            session.execute(text("""
                UPDATE alembic_version SET version_num = 'clean_schema_v1'
            """))
            logger.info("✅ Updated Alembic version to 'clean_schema_v1'")
            
    except Exception as e:
        logger.warning(f"⚠️  Could not initialize Alembic version: {e}")

if __name__ == "__main__":
    try:
        success = create_clean_schema()
        if success:
            logger.info("🎉 Clean schema initialization completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Schema initialization failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Fatal error during schema initialization: {e}")
        sys.exit(1)
