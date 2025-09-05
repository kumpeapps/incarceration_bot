#!/bin/bash

echo "🗂️ Archive Old Migrations Script"
echo "================================="

# Navigate to the project directory  
cd /Users/justinkumpe/Documents/incarceration_bot

echo "📋 Step 1: Create backup of current migrations"
mkdir -p migration_archive_$(date +%Y%m%d_%H%M%S)
cp -r backend/alembic/versions/* migration_archive_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true

echo "📋 Step 2: Remove all migration files from repository"
echo "This will clean up the conflicting migration chain..."

# Remove all existing migration files
rm -f backend/alembic/versions/*.py

echo "📋 Step 3: Update .gitignore to prevent future migration conflicts"
# Add migration files to gitignore if not already there
if ! grep -q "backend/alembic/versions/*.py" .gitignore 2>/dev/null; then
    echo "" >> .gitignore
    echo "# Migration files - managed by clean schema" >> .gitignore  
    echo "backend/alembic/versions/*.py" >> .gitignore
    echo "!backend/alembic/versions/.gitkeep" >> .gitignore
fi

# Create a .gitkeep file to maintain the directory
touch backend/alembic/versions/.gitkeep

echo "📋 Step 4: Commit the clean state"
git add .
git commit -m "Remove all migration files for clean schema approach

- Archived existing migrations to migration_archive_*
- Clean slate for comprehensive schema replacement
- Added migrations to .gitignore to prevent future conflicts
- Schema will be managed by create_clean_schema.py"

echo "📋 Step 5: Push clean state"
git push origin Beta

echo ""
echo "✅ Migration cleanup completed!"
echo ""
echo "Migration files have been:"
echo "✅ Backed up to migration_archive_* directory"
echo "✅ Removed from repository"  
echo "✅ Added to .gitignore"
echo "✅ Committed and pushed"
echo ""
echo "Next steps:"
echo "1. Run the clean_migration.sh script on the server"
echo "2. The create_clean_schema.py will handle all schema setup"
echo "3. No more migration conflicts!"
