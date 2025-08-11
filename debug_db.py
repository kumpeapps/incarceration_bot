#!/usr/bin/env python3

import os
import sys
from sqlalchemy import create_engine, text

# Database connection settings
mysql_server = "172.16.21.10"
mysql_username = "jail_test"
mysql_password = "LetmeN2it"
mysql_database = "jail_test"
mysql_port = "3306"

database_uri = f"mysql+pymysql://{mysql_username}:{mysql_password}@{mysql_server}:{mysql_port}/{mysql_database}"

print(f"Connecting to: {database_uri}")

try:
    engine = create_engine(database_uri)
    connection = engine.connect()
    print("✓ Database connection successful")
    
    # Test basic query
    result = connection.execute(text("SELECT COUNT(*) as count FROM inmates WHERE name = 'Waylon Kumpe'"))
    row = result.fetchone()
    print(f"✓ Found {row.count} records for Waylon Kumpe")
    
    # Test the enhancement query
    enhancement_query = text("""
        SELECT COUNT(*) as total_records,
               MIN(in_custody_date) as first_booking,
               MAX(in_custody_date) as latest_booking,
               GROUP_CONCAT(DISTINCT in_custody_date ORDER BY in_custody_date) as all_custody_dates,
               GROUP_CONCAT(DISTINCT release_date) as all_releases
        FROM inmates 
        WHERE name = :name AND dob = :dob AND jail_id = :jail_id
    """)
    
    enhancement_result = connection.execute(enhancement_query, {
        'name': 'Waylon Kumpe',
        'dob': '1995-01-23',
        'jail_id': 'aiken-so-sc'
    })
    enhancement_data = enhancement_result.fetchone()
    
    if enhancement_data:
        print("✓ Enhancement query executed successfully")
        print(f"  Total records: {enhancement_data.total_records}")
        print(f"  First booking: {enhancement_data.first_booking}")
        print(f"  Latest booking: {enhancement_data.latest_booking}")
        print(f"  All custody dates: {enhancement_data.all_custody_dates}")
        print(f"  All releases: {enhancement_data.all_releases}")
        
        # Determine actual status
        has_release = enhancement_data.all_releases and enhancement_data.all_releases.strip()
        actual_status = 'released' if has_release else 'in_custody'
        print(f"  Actual status: {actual_status}")
    else:
        print("✗ Enhancement query returned no data")
    
    connection.close()
    
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
