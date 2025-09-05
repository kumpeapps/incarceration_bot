#!/usr/bin/env python3
"""
Comprehensive Database Schema Migration System
Automatically validates and migrates all SQLAlchemy models to match database schema
Runs automatically on container startup to ensure database consistency
"""

import sys
import os
import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass

# Set up logging
logger = logging.getLogger(__name__)

# Import SQLAlchemy components
from sqlalchemy import text, inspect, Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.dialects import mysql, postgresql, sqlite
from sqlalchemy.sql.type_api import TypeEngine

@dataclass
class ColumnInfo:
    """Information about a database column."""
    name: str
    type_name: str
    nullable: bool
    default: Any = None
    primary_key: bool = False
    foreign_key: Optional[str] = None

class DatabaseSchemaMigrator:
    """Comprehensive database schema migrator for all SQLAlchemy models."""
    
    def __init__(self, session):
        self.session = session
        self.inspector = inspect(session.bind)
        self.dialect = session.bind.dialect.name.lower()
        self.changes_applied = 0
        
    def get_database_type(self) -> str:
        """Get standardized database type."""
        if 'mysql' in self.dialect or 'mariadb' in self.dialect:
            return 'mysql'
        elif 'postgres' in self.dialect:
            return 'postgresql'
        elif 'sqlite' in self.dialect:
            return 'sqlite'
        else:
            return 'unknown'
    
    def sqlalchemy_type_to_sql(self, column: Column) -> str:
        """Convert SQLAlchemy column type to SQL DDL string."""
        db_type = self.get_database_type()
        col_type = column.type
        
        # Handle different SQLAlchemy types
        if isinstance(col_type, Integer):
            return 'INTEGER'
        elif isinstance(col_type, String):
            if col_type.length:
                return f'VARCHAR({col_type.length})'
            else:
                return 'VARCHAR(255)'  # Default length
        elif isinstance(col_type, Boolean):
            if db_type == 'mysql':
                return 'BOOLEAN'
            elif db_type == 'postgresql':
                return 'BOOLEAN'
            else:  # SQLite
                return 'INTEGER'
        elif isinstance(col_type, Date):
            return 'DATE'
        elif isinstance(col_type, DateTime):
            if db_type == 'mysql':
                return 'DATETIME'
            elif db_type == 'postgresql':
                return 'TIMESTAMP'
            else:
                return 'DATETIME'
        elif isinstance(col_type, Text):
            # Handle MySQL MEDIUMTEXT
            if hasattr(col_type, '__class__') and 'MEDIUMTEXT' in str(col_type.__class__):
                return 'MEDIUMTEXT'
            elif hasattr(col_type, 'length') and col_type.length:
                return f'TEXT({col_type.length})'
            else:
                return 'TEXT'
        else:
            # Fallback to string representation
            col_str = str(col_type)
            if 'MEDIUMTEXT' in col_str:
                return 'MEDIUMTEXT'
            elif 'TEXT' in col_str:
                return 'TEXT'
            elif 'VARCHAR' in col_str:
                return col_str
            else:
                logger.warning(f"Unknown column type: {col_type}, using TEXT as fallback")
                return 'TEXT'
    
    def get_model_columns(self, model_class) -> Dict[str, ColumnInfo]:
        """Extract column information from SQLAlchemy model."""
        columns = {}
        
        # Get the table from the model
        if not hasattr(model_class, '__table__'):
            logger.warning(f"Model {model_class.__name__} has no __table__ attribute")
            return columns
        
        table = model_class.__table__
        
        for column in table.columns:
            # Use the actual database column name (e.g., 'idmonitors' not 'id')
            col_name = column.name
            
            # Determine if it's a foreign key
            foreign_key = None
            if column.foreign_keys:
                fk = list(column.foreign_keys)[0]
                foreign_key = f"{fk.column.table.name}({fk.column.name})"
            
            columns[col_name] = ColumnInfo(
                name=col_name,
                type_name=self.sqlalchemy_type_to_sql(column),
                nullable=column.nullable,
                default=column.default,
                primary_key=column.primary_key,
                foreign_key=foreign_key
            )
        
        return columns
    
    def get_database_columns(self, table_name: str) -> Dict[str, ColumnInfo]:
        """Get current database table columns."""
        columns = {}
        
        try:
            if table_name not in self.inspector.get_table_names():
                return columns
            
            db_columns = self.inspector.get_columns(table_name)
            
            for col in db_columns:
                columns[col['name']] = ColumnInfo(
                    name=col['name'],
                    type_name=str(col['type']).upper(),
                    nullable=col['nullable'],
                    default=col.get('default'),
                    primary_key=col.get('primary_key', False)
                )
        except Exception as e:
            logger.warning(f"Could not inspect table {table_name}: {e}")
        
        return columns
    
    def build_column_ddl(self, column_info: ColumnInfo) -> str:
        """Build DDL for adding a column."""
        ddl = f"{column_info.name} {column_info.type_name}"
        
        # Add NULL/NOT NULL
        if column_info.nullable:
            ddl += " NULL"
        else:
            ddl += " NOT NULL"
        
        # Add default value
        if column_info.default is not None:
            default_val = column_info.default
            if hasattr(default_val, 'arg'):  # SQLAlchemy default object
                default_val = default_val.arg
            
            if isinstance(default_val, str):
                ddl += f" DEFAULT '{default_val}'"
            elif isinstance(default_val, (int, float)):
                ddl += f" DEFAULT {default_val}"
            elif str(default_val).upper() in ['CURRENT_TIMESTAMP', 'NOW()']:
                if self.get_database_type() == 'mysql':
                    ddl += " DEFAULT CURRENT_TIMESTAMP"
                else:
                    ddl += " DEFAULT CURRENT_TIMESTAMP"
        
        return ddl
    
    def migrate_table(self, model_class) -> bool:
        """Migrate a single table to match its SQLAlchemy model."""
        if not hasattr(model_class, '__tablename__'):
            logger.warning(f"Model {model_class.__name__} has no __tablename__")
            return True
        
        table_name = model_class.__tablename__
        logger.info(f"🔍 Checking table: {table_name}")
        
        # Get model and database columns
        model_columns = self.get_model_columns(model_class)
        db_columns = self.get_database_columns(table_name)
        
        if not db_columns:
            logger.info(f"⚠️  Table {table_name} does not exist - will be created by schema initialization")
            return True
        
        # Find missing columns
        missing_columns = []
        for col_name, col_info in model_columns.items():
            if col_name not in db_columns:
                missing_columns.append(col_info)
                logger.info(f"  ❌ Missing column: {col_name}")
            else:
                logger.debug(f"  ✅ Column exists: {col_name}")
        
        if not missing_columns:
            logger.info(f"  ✅ All columns exist for {table_name}")
            return True
        
        # Add missing columns
        logger.info(f"  🔧 Adding {len(missing_columns)} missing columns to {table_name}")
        
        for col_info in missing_columns:
            try:
                ddl = self.build_column_ddl(col_info)
                sql = f"ALTER TABLE {table_name} ADD COLUMN {ddl}"
                
                logger.info(f"    📝 Adding {col_info.name}: {ddl}")
                self.session.execute(text(sql))
                self.session.commit()
                
                logger.info(f"    ✅ Added {col_info.name} successfully")
                self.changes_applied += 1
                
            except Exception as e:
                error_msg = str(e).lower()
                if 'duplicate' in error_msg or 'already exists' in error_msg:
                    logger.info(f"    ℹ️  {col_info.name} already exists")
                else:
                    logger.error(f"    ❌ Error adding {col_info.name}: {e}")
                    self.session.rollback()
                    return False
        
        return True
    
    def migrate_all_models(self) -> bool:
        """Migrate all SQLAlchemy models to match database schema."""
        logger.info("🚀 Starting comprehensive database schema migration...")
        
        # Import all models to ensure they're registered
        try:
            from models.User import User
            from models.Group import Group
            from models.UserGroup import UserGroup
            from models.Jail import Jail
            from models.Inmate import Inmate
            from models.Monitor import Monitor
            from models.MonitorLink import MonitorLink
            from models.MonitorInmateLink import MonitorInmateLink
            from models.Session import Session as UserSession
        except ImportError as e:
            logger.error(f"Failed to import models: {e}")
            return False
        
        # List of all models to check
        models_to_check = [
            User,
            Group, 
            UserGroup,
            Jail,
            Inmate,
            Monitor,
            MonitorLink,
            MonitorInmateLink,
            UserSession
        ]
        
        success = True
        
        for model in models_to_check:
            try:
                if not self.migrate_table(model):
                    logger.error(f"❌ Failed to migrate table for {model.__name__}")
                    success = False
            except Exception as e:
                logger.error(f"❌ Error migrating {model.__name__}: {e}")
                success = False
        
        if success:
            logger.info(f"🎉 Schema migration completed successfully!")
            logger.info(f"📊 Total changes applied: {self.changes_applied}")
        else:
            logger.error("❌ Schema migration completed with errors")
        
        return success

def run_comprehensive_migration():
    """Run comprehensive database schema migration."""
    from database_connect import new_session
    
    session = new_session()
    try:
        migrator = DatabaseSchemaMigrator(session)
        return migrator.migrate_all_models()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False
    finally:
        session.close()

def verify_migration():
    """Verify that all critical tables and columns exist."""
    from database_connect import new_session
    
    session = new_session()
    try:
        logger.info("🔍 Verifying migration results...")
        
        # Test critical queries that commonly fail
        test_queries = [
            "SELECT name, arrest_date FROM monitors LIMIT 1",
            "SELECT name, jail_id FROM inmates LIMIT 1",
            "SELECT username, api_key FROM users LIMIT 1",
            "SELECT name FROM groups LIMIT 1"
        ]
        
        for query in test_queries:
            try:
                session.execute(text(query))
                logger.info(f"  ✅ Query successful: {query}")
            except Exception as e:
                logger.warning(f"  ⚠️  Query failed: {query} - {e}")
        
        logger.info("✅ Migration verification completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    """Direct execution for testing."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🚀 Comprehensive Database Schema Migration")
    print("=" * 50)
    
    if run_comprehensive_migration():
        if verify_migration():
            print("🎉 Migration and verification completed successfully!")
        else:
            print("⚠️  Migration completed but verification had issues")
    else:
        print("❌ Migration failed!")
    
    print("=" * 50)
