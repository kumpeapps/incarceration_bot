#!/usr/bin/env python3
"""
Check database structure and create missing tables
"""
import sys
import os
sys.path.insert(0, '/app')

from database_connect import new_session
from sqlalchemy import inspect, text

def check_database_structure():
    session = new_session()
    try:
        inspector = inspect(session.bind)
        
        # Check what tables exist
        tables = inspector.get_table_names()
        print(f"Existing tables: {tables}")
        
        # Check monitors table structure if it exists
        if 'monitors' in tables:
            monitors_columns = inspector.get_columns('monitors')
            print(f"Monitors table columns: {[col['name'] for col in monitors_columns]}")
        
        # Check if users table exists
        if 'users' not in tables:
            print("Users table does not exist, creating it...")
            session.execute(text("""
                CREATE TABLE users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """))
            session.commit()
            print("Users table created successfully")
        else:
            print("Users table already exists")
            
        # Check inmates table primary key
        if 'inmates' in tables:
            inmates_columns = inspector.get_columns('inmates')
            print(f"Inmates table columns: {[col['name'] for col in inmates_columns]}")
            
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    check_database_structure()
