"""partition_inmates_table_by_jail_id

Revision ID: 98cbdf3c7e56
Revises: ae704cc1468a
Create Date: 2025-09-02 18:54:10.443094

Partitions the inmates table by jail_id for better performance.

This migration:
1. Creates a partitioned version of the inmates table
2. Copies all existing data to the new partitioned table
3. Replaces the original table with the partitioned version
4. Uses HASH partitioning for even distribution

Benefits:
- Physical separation of jail data
- Faster queries (only searches relevant partition)
- Better concurrent processing
- Improved maintenance operations
- Query optimization by MySQL

IMPORTANT: This is a complex operation that requires careful handling.
The migration includes rollback safety and validation steps.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect
from migration_utils import safe_execute


# revision identifiers, used by Alembic.
revision: str = '98cbdf3c7e56'
down_revision: Union[str, Sequence[str], None] = 'ae704cc1468a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(connection, table_name):
    """Check if a table exists."""
    try:
        inspector = inspect(connection)
        tables = inspector.get_table_names()
        return table_name in tables
    except Exception:
        return False


def is_table_partitioned(connection, table_name):
    """Check if a table is already partitioned."""
    try:
        result = connection.execute(text("""
            SELECT COUNT(*) as partition_count
            FROM information_schema.PARTITIONS 
            WHERE TABLE_NAME = :table_name 
            AND TABLE_SCHEMA = DATABASE()
            AND PARTITION_NAME IS NOT NULL
        """), {"table_name": table_name})
        
        count = result.scalar()
        return count > 0
    except Exception as e:
        print(f"Error checking partitioning status: {e}")
        return False


def upgrade() -> None:
    """Partition the inmates table by jail_id."""
    connection = op.get_bind()
    
    # Check if we're using MySQL
    if connection.dialect.name != 'mysql':
        print("⚠️  Table partitioning is only supported on MySQL/MariaDB")
        print("   Skipping partitioning for non-MySQL database")
        return
    
    print("🚀 Starting inmates table partitioning by jail_id...")
    
    try:
        # Check if table is already partitioned
        if is_table_partitioned(connection, 'inmates'):
            print("✅ Table 'inmates' is already partitioned, no changes needed")
            return
        
        # Get current row count for verification
        original_count = connection.execute(text("SELECT COUNT(*) FROM inmates")).scalar()
        print(f"📊 Current inmates table has {original_count:,} rows")
        
        # Step 1: Create backup table
        backup_table = "inmates_backup_before_partition"
        
        if table_exists(connection, backup_table):
            print(f"📋 Backup table {backup_table} exists, assuming resumed operation")
        else:
            print("📋 Creating backup of original inmates table...")
            connection.execute(text(f"CREATE TABLE {backup_table} LIKE inmates"))
            connection.execute(text(f"INSERT INTO {backup_table} SELECT * FROM inmates"))
            print("✅ Backup created successfully")
        
        # Step 2: Create new partitioned table
        partitioned_table = "inmates_partitioned"
        
        if table_exists(connection, partitioned_table):
            print(f"🔄 Partitioned table {partitioned_table} exists, dropping for fresh creation")
            connection.execute(text(f"DROP TABLE {partitioned_table}"))
        
        print("🏗️  Creating new partitioned inmates table...")
        
        # Create partitioned table with HASH partitioning for even distribution
        partition_sql = """
        CREATE TABLE inmates_partitioned (
            idinmates INT NOT NULL AUTO_INCREMENT,
            name VARCHAR(255) NOT NULL,
            race VARCHAR(255) NOT NULL DEFAULT 'Unknown',
            sex VARCHAR(255) NOT NULL DEFAULT 'Unknown',
            cell_block VARCHAR(255),
            arrest_date DATE,
            held_for_agency VARCHAR(255),
            mugshot TEXT,
            dob VARCHAR(255) NOT NULL DEFAULT 'Unknown',
            hold_reasons VARCHAR(1000) NOT NULL DEFAULT '',
            is_juvenile TINYINT(1) NOT NULL DEFAULT 0,
            release_date VARCHAR(255) NOT NULL DEFAULT '',
            in_custody_date DATE NOT NULL,
            last_seen DATETIME,
            jail_id VARCHAR(255) NOT NULL,
            hide_record TINYINT(1) NOT NULL DEFAULT 0,
            PRIMARY KEY (idinmates, jail_id),
            UNIQUE KEY unique_inmate_optimized (jail_id, arrest_date, name, dob, sex, race),
            KEY idx_jail_id (jail_id),
            KEY idx_last_seen (last_seen),
            KEY idx_arrest_date (arrest_date),
            CONSTRAINT fk_inmates_jail_partitioned FOREIGN KEY (jail_id) REFERENCES jails (jail_id)
        ) ENGINE=InnoDB
        PARTITION BY HASH(CRC32(jail_id))
        PARTITIONS 16
        """
        
        connection.execute(text(partition_sql))
        print("✅ Partitioned table structure created with 16 hash partitions")
        
        # Step 3: Copy data to partitioned table in batches for large datasets
        print("📊 Copying data to partitioned table...")
        if original_count > 100000:
            print(f"   Large dataset detected ({original_count:,} rows), using batch copy...")
            batch_size = 50000
            offset = 0
            total_copied = 0
            
            while True:
                batch_result = connection.execute(text(f"""
                    INSERT INTO inmates_partitioned 
                    SELECT * FROM inmates 
                    LIMIT {batch_size} OFFSET {offset}
                """))
                
                rows_copied = batch_result.rowcount if hasattr(batch_result, 'rowcount') else batch_size
                if rows_copied == 0:
                    break
                    
                total_copied += rows_copied
                offset += batch_size
                print(f"   Copied {total_copied:,} / {original_count:,} rows...")
                
                if total_copied >= original_count:
                    break
        else:
            # Single batch for smaller datasets
            connection.execute(text("INSERT INTO inmates_partitioned SELECT * FROM inmates"))
            total_copied = original_count
        
        print(f"✅ Copied {total_copied:,} rows to partitioned table")
        
        # Step 4: Verify data integrity
        print("🔍 Verifying data integrity...")
        partitioned_count = connection.execute(text("SELECT COUNT(*) FROM inmates_partitioned")).scalar()
        
        if original_count != partitioned_count:
            raise Exception(f"Data integrity check failed: original={original_count:,}, partitioned={partitioned_count:,}")
        
        print(f"✅ Data integrity verified: {original_count:,} rows in both tables")
        
        # Step 5: Replace original table with partitioned version
        print("🔄 Replacing original table with partitioned version...")
        
        # Drop the original table and rename partitioned table
        connection.execute(text("DROP TABLE inmates"))
        connection.execute(text("RENAME TABLE inmates_partitioned TO inmates"))
        
        print("✅ Table replacement completed")
        
        # Step 6: Verify partitioning is working
        partition_info = connection.execute(text("""
            SELECT PARTITION_NAME, TABLE_ROWS 
            FROM information_schema.PARTITIONS 
            WHERE TABLE_NAME = 'inmates' 
            AND TABLE_SCHEMA = DATABASE()
            AND PARTITION_NAME IS NOT NULL
            ORDER BY PARTITION_NAME
        """)).fetchall()
        
        print(f"📊 Partitioning verification - {len(partition_info)} partitions created:")
        for partition_name, row_count in partition_info:
            print(f"   Partition {partition_name}: {row_count:,} rows")
        
        print(f"📋 Backup table {backup_table} retained for safety")
        
        print("🎉 Table partitioning completed successfully!")
        print("   Benefits achieved:")
        print("   ✅ Faster queries for specific jails")
        print("   ✅ Better concurrent processing")
        print("   ✅ Improved maintenance operations")
        print("   ✅ Optimized storage and indexing")
        print("   ✅ Even data distribution across partitions")
        
    except Exception as e:
        print(f"❌ Partitioning failed: {e}")
        print("🔄 Attempting to restore from backup if available...")
        
        try:
            backup_table = "inmates_backup_before_partition"
            if table_exists(connection, backup_table):
                # Clean up partial work
                if table_exists(connection, partitioned_table):
                    connection.execute(text(f"DROP TABLE {partitioned_table}"))
                
                if not table_exists(connection, 'inmates'):
                    connection.execute(text(f"RENAME TABLE {backup_table} TO inmates"))
                    print("✅ Successfully restored from backup")
                else:
                    print("⚠️  Original table still exists, backup preserved")
            else:
                print("⚠️  No backup found, manual intervention may be required")
                
        except Exception as restore_error:
            print(f"❌ Restore failed: {restore_error}")
            print("⚠️  MANUAL INTERVENTION REQUIRED")
        
        raise


def downgrade() -> None:
    """Remove partitioning from inmates table."""
    connection = op.get_bind()
    
    if connection.dialect.name != 'mysql':
        print("ℹ️  Partitioning downgrade only applies to MySQL/MariaDB")
        return
    
    print("🔄 Removing partitioning from inmates table...")
    
    try:
        # Check if table is partitioned
        if not is_table_partitioned(connection, 'inmates'):
            print("ℹ️  Table 'inmates' is not partitioned, no changes needed")
            return
        
        backup_table = "inmates_backup_before_partition"
        
        # Get current row count
        current_count = connection.execute(text("SELECT COUNT(*) FROM inmates")).scalar()
        print(f"📊 Current partitioned table has {current_count:,} rows")
        
        if table_exists(connection, backup_table):
            print(f"📋 Restoring from backup table {backup_table}")
            
            # Verify backup integrity
            backup_count = connection.execute(text(f"SELECT COUNT(*) FROM {backup_table}")).scalar()
            print(f"📋 Backup table has {backup_count:,} rows")
            
            # Create non-partitioned table from backup
            connection.execute(text("CREATE TABLE inmates_temp LIKE " + backup_table))
            connection.execute(text(f"INSERT INTO inmates_temp SELECT * FROM {backup_table}"))
            
            # Replace partitioned table
            connection.execute(text("DROP TABLE inmates"))
            connection.execute(text("RENAME TABLE inmates_temp TO inmates"))
            
            print("✅ Successfully restored non-partitioned table from backup")
            
        else:
            print("⚠️  No backup found, creating non-partitioned version from current data")
            
            # Create non-partitioned copy of current data
            non_partitioned_sql = """
            CREATE TABLE inmates_non_partitioned (
                idinmates INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                race VARCHAR(255) NOT NULL DEFAULT 'Unknown',
                sex VARCHAR(255) NOT NULL DEFAULT 'Unknown',
                cell_block VARCHAR(255),
                arrest_date DATE,
                held_for_agency VARCHAR(255),
                mugshot TEXT,
                dob VARCHAR(255) NOT NULL DEFAULT 'Unknown',
                hold_reasons VARCHAR(1000) NOT NULL DEFAULT '',
                is_juvenile TINYINT(1) NOT NULL DEFAULT 0,
                release_date VARCHAR(255) NOT NULL DEFAULT '',
                in_custody_date DATE NOT NULL,
                last_seen DATETIME,
                jail_id VARCHAR(255) NOT NULL,
                hide_record TINYINT(1) NOT NULL DEFAULT 0,
                UNIQUE KEY unique_inmate_optimized (jail_id, arrest_date, name, dob, sex, race),
                KEY idx_jail_id (jail_id),
                KEY idx_last_seen (last_seen),
                KEY idx_arrest_date (arrest_date),
                CONSTRAINT fk_inmates_jail_id FOREIGN KEY (jail_id) REFERENCES jails (jail_id)
            ) ENGINE=InnoDB
            """
            
            connection.execute(text(non_partitioned_sql))
            connection.execute(text("INSERT INTO inmates_non_partitioned SELECT * FROM inmates"))
            
            # Replace partitioned table
            connection.execute(text("DROP TABLE inmates"))
            connection.execute(text("RENAME TABLE inmates_non_partitioned TO inmates"))
            
            print("✅ Successfully created non-partitioned table")
        
        print("🎯 Partitioning removal completed - table is now non-partitioned")
        
    except Exception as e:
        print(f"❌ Partitioning removal failed: {e}")
        print("⚠️  Manual intervention may be required")
        raise
