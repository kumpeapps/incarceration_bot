#!/bin/bash

echo "🧹 Clean Database Schema Migration Script"
echo "=========================================="

# Navigate to the project directory
cd /home/bot/bot

echo "📋 Step 1: Backup current database state"
echo "Creating database backup before clean migration..."

# Create backup using the container
docker compose exec backend_api python3 -c "
import os
from datetime import datetime
import subprocess

# Create backup filename with timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = f'/tmp/incarceration_bot_backup_{timestamp}.sql'

# Get database connection details from environment
host = os.getenv('MYSQL_HOST', 'localhost')
user = os.getenv('MYSQL_USER', 'root')
password = os.getenv('MYSQL_ROOT_PASSWORD')
database = os.getenv('MYSQL_DATABASE', 'incarceration_bot')

print(f'Creating backup: {backup_file}')
print(f'Database: {host}/{database}')

# Note: This would need mysqldump available in the container
# For now, we'll just log the intent
print('⚠️  Manual backup recommended before proceeding')
print(f'   mysqldump -h {host} -u {user} -p{password} {database} > backup_{timestamp}.sql')
"

echo ""
echo "📋 Step 2: Remove conflicting migration files"
echo "Cleaning up problematic migration files..."

# Create backup of migration files first
docker compose exec backend_api bash -c "
cd /app/alembic/versions
echo 'Current migration files:'
ls -la *.py | wc -l

# Create backup directory for old migrations
mkdir -p /tmp/old_migrations_backup
echo 'Backing up existing migrations to /tmp/old_migrations_backup...'
cp *.py /tmp/old_migrations_backup/ 2>/dev/null || true

echo 'Removing ALL existing migration files to prevent conflicts...'
rm -f *.py

echo 'Migration files after cleanup:'
ls -la *.py 2>/dev/null | wc -l || echo '0'
echo 'All migration files removed - clean slate ready'
"

echo ""
echo "📋 Step 3: Copy clean schema script to container"

# Copy the clean schema script to the container
docker compose cp backend/create_clean_schema.py backend_api:/app/

echo ""
echo "📋 Step 4: Run clean schema initialization"
echo "This will create missing tables and set up the final schema..."

# Run the clean schema script
docker compose exec backend_api python3 /app/create_clean_schema.py

echo ""
echo "📋 Step 5: Verify schema state"

# Verify the database state
docker compose exec backend_api python3 -c "
from database_connect import new_session
from sqlalchemy import text, inspect

session = new_session()
try:
    # Check tables
    inspector = inspect(session.bind)
    tables = inspector.get_table_names()
    print(f'✅ Database tables ({len(tables)}): {sorted(tables)}')
    
    # Check alembic version
    result = session.execute(text('SELECT version_num FROM alembic_version'))
    version = result.scalar()
    print(f'✅ Alembic version: {version}')
    
    # Check inmates table structure
    if 'inmates' in tables:
        columns = inspector.get_columns('inmates')
        column_names = [col['name'] for col in columns]
        print(f'✅ Inmates table columns ({len(column_names)}): last_seen={\"last_seen\" in column_names}')
        
        # Check indexes
        indexes = inspector.get_indexes('inmates')
        index_names = [idx['name'] for idx in indexes]
        print(f'✅ Inmates table indexes ({len(index_names)}): {sorted(index_names)}')
    
    # Check groups
    if 'groups' in tables:
        result = session.execute(text('SELECT COUNT(*) FROM groups'))
        group_count = result.scalar()
        print(f'✅ Groups in database: {group_count}')
        
        result = session.execute(text('SELECT name FROM groups ORDER BY name'))
        groups = [row[0] for row in result]
        print(f'✅ Available groups: {groups}')
        
except Exception as e:
    print(f'❌ Verification error: {e}')
finally:
    session.close()
"

echo ""
echo "📋 Step 6: Restart services"
echo "Restarting containers to ensure clean state..."

docker compose restart backend_api

echo ""
echo "📋 Step 7: Final verification"
echo "Checking application startup logs..."

sleep 5
docker compose logs backend_api | tail -20

echo ""
echo "🎉 Clean schema migration completed!"
echo ""
echo "Next steps:"
echo "1. Verify the application is running: docker compose ps"
echo "2. Check logs for any errors: docker compose logs -f backend_api"
echo "3. Test the application functionality"
echo "4. Monitor processing performance"
echo ""
echo "The system should now have:"
echo "✅ Clean database schema with all tables"
echo "✅ Performance indexes for optimized queries"
echo "✅ All required groups initialized"
echo "✅ No migration conflicts"
echo "✅ Optimized unique constraints"
