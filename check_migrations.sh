#!/bin/bash

echo "🔍 Checking migration state and fixing conflicting heads..."

# Navigate to the backend directory
cd /Users/justinkumpe/Documents/incarceration_bot/backend

# Try to use Python to run alembic commands instead
echo "📋 Current migration history:"
python -m alembic history --verbose | head -20

echo ""
echo "📋 Current heads:"
python -m alembic heads

echo ""
echo "📋 Current revision:"
python -m alembic current

echo ""
echo "🔧 Attempting to merge any remaining heads..."
python -m alembic merge -m "Merge remaining conflicting heads" heads

echo ""
echo "📋 Updated heads after merge:"
python -m alembic heads

echo ""
echo "✅ Migration state check complete"
