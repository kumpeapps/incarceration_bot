"""
Database Optimization Configuration

This module provides configuration options for database optimizations
to reduce MariaDB binlog bloat and improve performance.
"""

import os
from typing import Dict, Any


class DatabaseOptimizationConfig:
    """Configuration for database optimization features."""
    
    # Enable optimized batch processing (recommended: True)
    ENABLE_BATCH_PROCESSING = os.getenv("DB_ENABLE_BATCH_PROCESSING", "True").lower() == "true"
    
    # Batch size for inmate processing (recommended: 100-500)
    INMATE_BATCH_SIZE = int(os.getenv("DB_INMATE_BATCH_SIZE", "100"))
    
    # Batch size for monitor updates (recommended: 50-100)
    MONITOR_BATCH_SIZE = int(os.getenv("DB_MONITOR_BATCH_SIZE", "50"))
    
    # Hours between last_seen updates (recommended: 1-6 hours)
    LAST_SEEN_UPDATE_THRESHOLD_HOURS = int(os.getenv("DB_LAST_SEEN_THRESHOLD_HOURS", "1"))
    
    # Enable conditional timestamp updates (recommended: True)
    ENABLE_CONDITIONAL_TIMESTAMPS = os.getenv("DB_CONDITIONAL_TIMESTAMPS", "True").lower() == "true"
    
    # Enable automatic updated_at triggers (NOT recommended for high-write scenarios)
    ENABLE_AUTO_UPDATED_AT = os.getenv("DB_AUTO_UPDATED_AT", "False").lower() == "true"
    
    # Log optimization metrics (recommended: True for monitoring)
    LOG_OPTIMIZATION_METRICS = os.getenv("DB_LOG_OPTIMIZATION_METRICS", "True").lower() == "true"
    
    @classmethod
    def get_config_summary(cls) -> Dict[str, Any]:
        """Return current configuration summary."""
        return {
            "batch_processing_enabled": cls.ENABLE_BATCH_PROCESSING,
            "inmate_batch_size": cls.INMATE_BATCH_SIZE,
            "monitor_batch_size": cls.MONITOR_BATCH_SIZE,
            "last_seen_threshold_hours": cls.LAST_SEEN_UPDATE_THRESHOLD_HOURS,
            "conditional_timestamps_enabled": cls.ENABLE_CONDITIONAL_TIMESTAMPS,
            "auto_updated_at_enabled": cls.ENABLE_AUTO_UPDATED_AT,
            "optimization_logging_enabled": cls.LOG_OPTIMIZATION_METRICS,
        }
    
    @classmethod
    def log_config(cls):
        """Log current configuration for debugging."""
        from loguru import logger
        config = cls.get_config_summary()
        logger.info("Database Optimization Configuration:")
        for key, value in config.items():
            logger.info(f"  {key}: {value}")


# Environment variable defaults for docker-compose
ENV_DEFAULTS = """
# Add these to your docker-compose.yml environment section to configure optimizations:

# Enable/disable batch processing (reduces database round trips)
DB_ENABLE_BATCH_PROCESSING=True

# Batch sizes (higher = fewer queries but more memory usage)
DB_INMATE_BATCH_SIZE=100
DB_MONITOR_BATCH_SIZE=50

# How often to update last_seen timestamps (hours)
# Higher values = less binlog bloat but less precise tracking
DB_LAST_SEEN_THRESHOLD_HOURS=1

# Enable conditional timestamp updates (prevents unnecessary writes)
DB_CONDITIONAL_TIMESTAMPS=True

# Auto updated_at columns (disable for high-write workloads)
DB_AUTO_UPDATED_AT=False

# Log optimization metrics
DB_LOG_OPTIMIZATION_METRICS=True
"""
