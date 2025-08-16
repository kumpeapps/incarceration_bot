#!/bin/bash
# Quick verification script for remote server

echo "Checking if api_key column exists in users table..."

docker-compose exec backend python -c "
import sys
sys.path.append('/app')
from database_connect import get_db
from sqlalchemy import inspect, text

try:
    db = next(get_db())
    inspector = inspect(db.bind)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    print('Users table columns:')
    for col in sorted(columns):
        print(f'  - {col}')
    
    if 'api_key' in columns:
        print('\n✅ api_key column EXISTS')
    else:
        print('\n❌ api_key column MISSING')
        
    if 'amember_user_id' in columns:
        print('✅ amember_user_id column EXISTS')
    else:
        print('❌ amember_user_id column MISSING')
        
    if 'password_format' in columns:
        print('✅ password_format column EXISTS')
    else:
        print('❌ password_format column MISSING')
        
except Exception as e:
    print(f'Error checking columns: {e}')
finally:
    db.close()
"
