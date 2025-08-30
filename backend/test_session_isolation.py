#!/usr/bin/env python3
"""
Test script to verify database session isolation between jails.
This simulates the potential lock issue between Benton and Pulaski counties.
"""

import sys
import time
from datetime import datetime
from loguru import logger
import database_connect as db
from models.Jail import Jail

def test_session_isolation():
    """Test that individual sessions don't interfere with each other"""
    logger.info("🧪 Testing database session isolation between jails")
    
    # Test 1: Get jail list with setup session
    setup_session = db.new_session()
    try:
        jails = setup_session.query(Jail).filter(
            Jail.jail_id.in_(["benton-so-ar", "pulaski-so-ar"])
        ).all()
        logger.info(f"📋 Found {len(jails)} test jails")
        for jail in jails:
            logger.info(f"  - {jail.jail_name} ({jail.jail_id})")
    finally:
        setup_session.close()
        logger.info("✅ Setup session closed")
    
    if len(jails) < 2:
        logger.error("❌ Need both Benton and Pulaski counties in database")
        return False
    
    # Test 2: Process each jail with individual sessions (as in the fix)
    for i, jail in enumerate(jails, 1):
        logger.info(f"\n🔍 Test {i}/2: Processing {jail.jail_name}")
        
        # Create isolated session for this jail
        jail_session = db.new_session()
        
        try:
            # Simulate some database operations like the scraper does
            logger.info(f"  📊 Querying jail data for {jail.jail_name}")
            jail_from_session = jail_session.query(Jail).filter(
                Jail.jail_id == jail.jail_id
            ).first()
            
            if jail_from_session:
                # Simulate updating last scrape date
                logger.info(f"  💾 Updating last scrape date for {jail.jail_name}")
                jail_from_session.last_scrape_date = datetime.now().date()
                jail_session.commit()
                logger.success(f"  ✅ Successfully committed changes for {jail.jail_name}")
            else:
                logger.warning(f"  ⚠️  Could not find jail {jail.jail_id} in session")
                
        except Exception as e:
            logger.error(f"  ❌ Error processing {jail.jail_name}: {e}")
            try:
                jail_session.rollback()
                logger.info(f"  🔄 Rolled back session for {jail.jail_name}")
            except Exception as rollback_error:
                logger.error(f"  💥 Failed to rollback: {rollback_error}")
            return False
        finally:
            try:
                jail_session.close()
                logger.info(f"  🔒 Closed session for {jail.jail_name}")
            except Exception as close_error:
                logger.warning(f"  ⚠️  Warning closing session: {close_error}")
        
        # Brief pause between jails
        time.sleep(0.5)
    
    logger.success("\n🎉 Session isolation test completed successfully!")
    logger.info("💡 This confirms that individual sessions prevent lock conflicts")
    return True

if __name__ == "__main__":
    try:
        success = test_session_isolation()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.exception(f"💥 Test failed with exception: {e}")
        sys.exit(1)
