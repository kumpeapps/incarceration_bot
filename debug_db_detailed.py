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
    
    # Get details for inmate ID 249
    result = connection.execute(text("SELECT * FROM inmates WHERE idinmates = 249"))
    row = result.fetchone()
    
    if row:
        print(f"✓ Found inmate with ID 249:")
        print(f"  Name: '{row.name}'")
        print(f"  DOB: '{row.dob}'")
        print(f"  Jail ID: '{row.jail_id}'")
        print(f"  In custody date: {row.in_custody_date}")
        print(f"  Release date: '{row.release_date}'")
        
        # Now search for all records with this exact name and details
        all_records_query = text("""
            SELECT idinmates, name, dob, jail_id, in_custody_date, release_date
            FROM inmates 
            WHERE name = :name AND dob = :dob AND jail_id = :jail_id
            ORDER BY in_custody_date
        """)
        
        all_records_result = connection.execute(all_records_query, {
            'name': row.name,
            'dob': row.dob,
            'jail_id': row.jail_id
        })
        all_records = all_records_result.fetchall()
        
        print(f"\n✓ Found {len(all_records)} total records for this person:")
        for record in all_records:
            print(f"  ID: {record.idinmates}, In custody: {record.in_custody_date}, Release: '{record.release_date}'")
            
        # Test the enhancement query with exact values
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
            'name': row.name,
            'dob': row.dob,
            'jail_id': row.jail_id
        })
        enhancement_data = enhancement_result.fetchone()
        
        if enhancement_data:
            print(f"\n✓ Enhancement query results:")
            print(f"  Total records: {enhancement_data.total_records}")
            print(f"  First booking: {enhancement_data.first_booking}")
            print(f"  Latest booking: {enhancement_data.latest_booking}")
            print(f"  All custody dates: {enhancement_data.all_custody_dates}")
            print(f"  All releases: '{enhancement_data.all_releases}'")
            
            # Determine actual status
            has_release = enhancement_data.all_releases and enhancement_data.all_releases.strip()
            actual_status = 'released' if has_release else 'in_custody'
            print(f"  Actual status: {actual_status}")
        else:
            print("✗ Enhancement query returned no data")
    else:
        print("✗ No inmate found with ID 249")
    
    connection.close()
    
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
