#!/bin/bash

# Monitor MariaDB Binlog Growth
# Run this script to track binlog file sizes before and after optimization

echo "=== MariaDB Binlog Monitoring ==="
echo "Timestamp: $(date)"
echo ""

# Function to get binlog size in MB
get_binlog_size() {
    docker-compose exec -T backend_api mysql -e "
        SELECT 
            Log_name,
            ROUND(File_size/1024/1024, 2) as Size_MB
        FROM information_schema.BINARY_LOG_FILES 
        ORDER BY Log_name DESC 
        LIMIT 5;
    " 2>/dev/null | grep -v "File_size" || echo "Error: Could not connect to database"
}

# Function to check recent SQL operations
check_recent_operations() {
    echo "Recent UPDATE operations on inmates table:"
    docker-compose exec -T backend_api mysql -e "
        SELECT 
            COUNT(*) as update_count,
            'inmates table updates in last hour' as description
        FROM information_schema.PROCESSLIST 
        WHERE COMMAND = 'Query' 
        AND INFO LIKE '%UPDATE inmates%'
        AND TIME < 3600;
    " 2>/dev/null || echo "Could not check recent operations"
}

# Main monitoring
echo "📊 Current Binlog Files (Latest 5):"
echo "Log Name                    Size (MB)"
echo "----------------------------------------"
get_binlog_size

echo ""
echo "🔍 Performance Check:"
check_recent_operations

echo ""
echo "💡 Tips:"
echo "- Watch for Size_MB growth rate"
echo "- Before optimization: Files grew rapidly (GB/hour)"
echo "- After optimization: Much slower growth" 
echo "- Run this script periodically to monitor improvement"
echo ""
echo "🚀 Optimization Status:"
docker-compose exec -T backend_api python -c "
import sys
sys.path.append('/app')
try:
    from helpers.db_optimization_config import DatabaseOptimizationConfig
    config = DatabaseOptimizationConfig.get_config_summary()
    if config['conditional_timestamps_enabled']:
        print('✅ Conditional timestamp updates: ENABLED')
    else:
        print('❌ Conditional timestamp updates: DISABLED')
    print(f'⚙️  Last seen threshold: {config[\"last_seen_threshold_hours\"]} hours')
except Exception as e:
    print('⚠️  Could not check optimization config')
" 2>/dev/null

echo ""
echo "=== End Monitoring ==="
