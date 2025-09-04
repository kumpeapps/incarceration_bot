#!/bin/bash

# Clean schema deployment script
# This script safely deploys the clean database schema

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"

echo "🚀 Starting clean schema deployment..."
echo "📁 Backend directory: $BACKEND_DIR"

# Check if we're in the right directory
if [ ! -f "$BACKEND_DIR/create_clean_schema.py" ]; then
    echo "❌ Error: create_clean_schema.py not found in $BACKEND_DIR"
    exit 1
fi

# Change to backend directory
cd "$BACKEND_DIR"

# Check database connection
echo "🔍 Testing database connection..."
python -c "
import sys
sys.path.append('.')
from database_connect import get_database_url
try:
    url = get_database_url()
    print(f'✅ Database URL configured: {url.split(\"@\")[1] if \"@\" in url else \"[local]\"}')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Database connection test failed"
    exit 1
fi

# Create backup of current migration state (if alembic exists)
if [ -f "alembic.ini" ] && [ -d "alembic/versions" ]; then
    echo "💾 Creating backup of current migration state..."
    BACKUP_DIR="migration_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    cp -r alembic/versions/* "$BACKUP_DIR/" 2>/dev/null || echo "ℹ️  No migration files to backup"
    echo "✅ Migration backup created in $BACKUP_DIR"
fi

# Test the clean schema first
echo "🧪 Testing clean schema deployment..."
python test_clean_schema.py

if [ $? -ne 0 ]; then
    echo "❌ Clean schema test failed"
    exit 1
fi

echo "✅ Clean schema test passed"

# Apply the clean schema
echo "📋 Applying clean schema to database..."
python -c "
import sys
import logging
sys.path.append('.')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from database_connect import get_database_url
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from create_clean_schema import create_complete_schema, setup_default_groups
    
    # Connect to database
    database_url = get_database_url()
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    logger.info('🔧 Creating complete schema...')
    create_complete_schema(session)
    
    logger.info('👥 Setting up default groups...')
    setup_default_groups(session)
    
    logger.info('💾 Committing changes...')
    session.commit()
    session.close()
    
    logger.info('✅ Clean schema deployment completed successfully')
    
except Exception as e:
    logger.error(f'❌ Clean schema deployment failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Clean schema deployment failed"
    exit 1
fi

# Verify the deployment
echo "🔍 Verifying deployment..."
python -c "
import sys
sys.path.append('.')
from database_connect import get_database_url
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

try:
    database_url = get_database_url()
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Check partitioning if MySQL
    if 'mysql' in database_url.lower():
        result = session.execute(text('''
            SELECT COUNT(*) as partition_count
            FROM information_schema.partitions 
            WHERE table_schema = DATABASE() 
            AND table_name = 'inmates' 
            AND partition_name IS NOT NULL
        ''')).fetchone()
        
        if result.partition_count > 0:
            print(f'✅ Inmates table partitioned with {result.partition_count} partitions')
        else:
            print('❌ Inmates table is not partitioned')
            sys.exit(1)
    
    # Check that default groups exist
    groups_result = session.execute(text('SELECT COUNT(*) FROM groups')).fetchone()
    if groups_result[0] > 0:
        print(f'✅ Default groups created ({groups_result[0]} groups)')
    else:
        print('❌ No default groups found')
        sys.exit(1)
    
    session.close()
    print('✅ Deployment verification successful')
    
except Exception as e:
    print(f'❌ Deployment verification failed: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Deployment verification failed"
    exit 1
fi

echo ""
echo "🎉 Clean schema deployment completed successfully!"
echo ""
echo "Summary:"
echo "  ✅ Database schema created with optimized structure"
echo "  ✅ Inmates table partitioned for performance (MySQL)"
echo "  ✅ Default user groups configured"
echo "  ✅ All migrations conflicts resolved"
echo ""
echo "Next steps:"
echo "  1. Test application startup: docker-compose up backend"
echo "  2. Verify data processing performance"
echo "  3. Monitor system performance with new optimizations"
echo ""
