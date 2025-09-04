#!/usr/bin/env python3
"""
Test script for clean schema deployment
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from create_clean_schema import create_complete_schema, setup_default_groups
from database_connect import get_database_url

def test_schema_deployment():
    """Test the complete schema deployment process."""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        # Get database URL
        database_url = get_database_url()
        logger.info(f"Connecting to database...")
        
        # Create engine and session
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Test schema creation
        logger.info("Testing schema creation...")
        create_complete_schema(session)
        
        # Test default groups setup
        logger.info("Testing default groups setup...")
        setup_default_groups(session)
        
        # Verify partitioning (MySQL only)
        if 'mysql' in database_url.lower():
            logger.info("Verifying table partitioning...")
            
            # Check if inmates table exists and is partitioned
            partition_check = """
            SELECT 
                table_name,
                COUNT(*) as partition_count
            FROM information_schema.partitions 
            WHERE table_schema = DATABASE() 
            AND table_name = 'inmates' 
            AND partition_name IS NOT NULL
            GROUP BY table_name
            """
            
            result = session.execute(text(partition_check)).fetchone()
            if result and result.partition_count > 0:
                logger.info(f"✅ Inmates table has {result.partition_count} partitions")
            else:
                logger.warning("❌ Inmates table is not partitioned")
                
            # List all partitions for verification
            list_partitions = """
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
            
            partitions = session.execute(text(list_partitions)).fetchall()
            if partitions:
                logger.info("Partition details:")
                for partition in partitions:
                    logger.info(f"  - {partition.partition_name}: position {partition.partition_ordinal_position}, rows: {partition.table_rows}")
            
        # Verify all tables were created
        logger.info("Verifying table creation...")
        show_tables = "SHOW TABLES" if 'mysql' in database_url.lower() else "SELECT name FROM sqlite_master WHERE type='table'"
        
        tables = session.execute(text(show_tables)).fetchall()
        table_names = [table[0] for table in tables]
        
        expected_tables = ['users', 'groups', 'user_groups', 'jails', 'inmates', 'monitors', 'monitor_inmate_links', 'monitor_links', 'sessions']
        
        logger.info("Created tables:")
        for table in table_names:
            status = "✅" if table in expected_tables else "ℹ️"
            logger.info(f"  {status} {table}")
            
        missing_tables = [table for table in expected_tables if table not in table_names]
        if missing_tables:
            logger.warning(f"Missing tables: {missing_tables}")
        else:
            logger.info("✅ All expected tables created successfully")
            
        # Commit and close
        session.commit()
        session.close()
        
        logger.info("✅ Schema deployment test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema deployment test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_schema_deployment()
    sys.exit(0 if success else 1)
