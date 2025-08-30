#!/bin/bash
# Local development runner with SQLite database

# Set environment variables for local SQLite development
export DB_TYPE="sqlite"
export DB_NAME="incarceration_bot_dev"
export LOG_LEVEL="DEBUG"
export RUN_SCHEDULE="now"  # Run immediately for testing

echo "🚀 Starting Incarceration Bot in LOCAL DEVELOPMENT MODE"
echo "📁 Database: SQLite (${DB_NAME}.db)"
echo "📊 Log Level: ${LOG_LEVEL}"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "💡 Tip: Activate your venv first: source venv/bin/activate"
    echo ""
fi

# Run the application
python3 main.py "$@"

# Capture exit code
exit_code=$?

if [[ $exit_code -eq 0 ]]; then
    echo ""
    echo "✅ Application completed successfully"
else
    echo ""
    echo "❌ Application failed with exit code: $exit_code"
fi

exit $exit_code
