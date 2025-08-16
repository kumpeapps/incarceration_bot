#!/bin/bash
# Comprehensive Migration Diagnostic and Fix Script
# This script will diagnose and fix migration issues

echo "🔍 MIGRATION DIAGNOSTIC AND FIX SCRIPT"
echo "======================================"

# Function to run commands in backend container
run_in_backend() {
    docker-compose exec backend_api "$@"
}

echo "📊 Step 1: Check container status"
echo "--------------------------------"
docker-compose ps backend_api

echo ""
echo "📊 Step 2: Check current Alembic head"
echo "------------------------------------"
run_in_backend alembic heads

echo ""
echo "📊 Step 3: Check current database revision"
echo "-----------------------------------------"
run_in_backend alembic current

echo ""
echo "📊 Step 4: Check migration history"
echo "---------------------------------"
run_in_backend alembic history --verbose

echo ""
echo "📊 Step 5: Check if api_key column exists"
echo "----------------------------------------"
run_in_backend python -c "
import sys
sys.path.append('/app')
from database_connect import get_db
from sqlalchemy import inspect

try:
    db = next(get_db())
    inspector = inspect(db.bind)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    print('📋 Users table columns:')
    for col in sorted(columns):
        print(f'   ✓ {col}')
    
    print()
    if 'api_key' in columns:
        print('✅ api_key column EXISTS')
    else:
        print('❌ api_key column MISSING')
        
    if 'amember_user_id' in columns:
        print('✅ amember_user_id column EXISTS')
    else:
        print('❌ amember_user_id column MISSING')
        
    if 'password_format' in columns:
        print('✅ password_format column EXISTS')
    else:
        print('❌ password_format column MISSING')
        
except Exception as e:
    print(f'❌ Error checking columns: {e}')
finally:
    db.close()
"

echo ""
echo "🔧 Step 6: Fix migrations if needed"
echo "----------------------------------"

echo "Option 1: Run upgrade to head"
if run_in_backend alembic upgrade head; then
    echo "✅ Migration upgrade successful"
else
    echo "❌ Migration upgrade failed, trying alternative approaches..."
    
    echo ""
    echo "Option 2: Stamp current and upgrade"
    run_in_backend alembic stamp head
    run_in_backend alembic upgrade head
    
    if [ $? -eq 0 ]; then
        echo "✅ Stamp and upgrade successful"
    else
        echo "❌ Stamp and upgrade failed, trying manual schema update..."
        
        echo ""
        echo "Option 3: Manual schema update via init_db.py"
        run_in_backend python /app/init_db.py
        
        if [ $? -eq 0 ]; then
            echo "✅ Manual schema update successful"
        else
            echo "❌ All automatic fixes failed"
            echo "📋 Manual intervention required:"
            echo "   1. Check container logs: docker-compose logs backend_api"
            echo "   2. Connect to database manually and verify schema"
            echo "   3. Run individual migrations manually if needed"
        fi
    fi
fi

echo ""
echo "📊 Step 7: Verify fix - Check columns again"
echo "------------------------------------------"
run_in_backend python -c "
import sys
sys.path.append('/app')
from database_connect import get_db
from sqlalchemy import inspect

try:
    db = next(get_db())
    inspector = inspect(db.bind)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    print('📋 FINAL STATE - Users table columns:')
    for col in sorted(columns):
        print(f'   ✓ {col}')
    
    print()
    missing_columns = []
    
    if 'api_key' not in columns:
        missing_columns.append('api_key')
    if 'amember_user_id' not in columns:
        missing_columns.append('amember_user_id') 
    if 'password_format' not in columns:
        missing_columns.append('password_format')
    
    if missing_columns:
        print(f'❌ STILL MISSING: {', '.join(missing_columns)}')
        print('🔧 MANUAL FIX REQUIRED')
    else:
        print('✅ ALL REQUIRED COLUMNS PRESENT')
        print('🎉 MIGRATION FIX SUCCESSFUL')
        
except Exception as e:
    print(f'❌ Error in final verification: {e}')
finally:
    db.close()
"

echo ""
echo "🏁 DIAGNOSTIC COMPLETE"
echo "====================="
echo "If all columns are present, your aMember plugin should now work!"
echo "If columns are still missing, manual database intervention is required."
