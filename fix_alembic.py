#!/usr/bin/env python3
"""
Clear alembic version table to fix migration conflicts
"""
import mysql.connector
import sys

def clear_alembic_version():
    try:
        # Connect to database
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='incarceration_db',
            user='root',
            password='rootpassword'
        )
        
        cursor = connection.cursor()
        
        # Check current versions
        cursor.execute("SELECT * FROM alembic_version")
        versions = cursor.fetchall()
        print(f"Current alembic versions: {versions}")
        
        # Clear the table
        cursor.execute("DELETE FROM alembic_version")
        print("Cleared alembic_version table")
        
        # Insert the latest valid revision
        cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('005_monitor_inmate_links')")
        print("Set version to '005_monitor_inmate_links'")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("✅ Successfully updated alembic version")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    clear_alembic_version()
