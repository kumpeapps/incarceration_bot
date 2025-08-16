# GitHub Copilot Instructions for Incarceration Bot

## Project Overview
Incarceration Bot is a Python-based web scraping and notification system that monitors jail rosters and notifies users when people of interest are incarcerated or released. The system includes a FastAPI backend, React frontend, and aMember integration for user management.

## Architecture
- **Backend**: FastAPI with SQLAlchemy ORM, Alembic migrations, Docker containerized
- **Frontend**: React with TypeScript, Vite build system, nginx-served in container
- **Database**: MySQL (production), SQLite (development), database-agnostic SQLAlchemy models
- **Authentication**: JWT tokens with master API key support for integrations
- **User Management**: Internal user system with optional aMember integration
- **Deployment**: Docker Compose with automatic migrations and schema updates

## Key Technologies
- **Python 3.11+**: FastAPI, SQLAlchemy, Alembic, BeautifulSoup4, Requests, Passlib
- **Frontend**: React, TypeScript, Vite, Tailwind CSS
- **Database**: MySQL/MariaDB with PyMySQL connector
- **Containerization**: Docker, Docker Compose with multi-stage builds
- **Authentication**: JWT with bcrypt password hashing
- **Integration**: aMember PHP plugin for external user management

## Development Guidelines

### Code Style
- **Python**: Follow PEP 8, use type hints, docstrings for all functions/classes
- **TypeScript**: Use strict mode, explicit typing, functional components with hooks
- **Database**: Use SQLAlchemy ORM, never raw SQL except in migrations
- **API**: RESTful endpoints, proper HTTP status codes, comprehensive error handling

### Database Operations
- Always use SQLAlchemy ORM for database operations
- Create database-agnostic code (support MySQL, PostgreSQL, SQLite)
- Use Alembic for all schema changes with idempotent migrations
- Include proper foreign key constraints and indexes
- Use the `safe_add_column`, `safe_drop_column` utilities for migrations

### Authentication & Security
- All API endpoints require authentication except health checks
- Use JWT tokens for user sessions
- Master API key for integration endpoints (aMember, external systems)
- Check authorization with `check_integration_permissions()` for sensitive endpoints
- Hash passwords with bcrypt, never store plaintext

### Error Handling
- Use FastAPI's HTTPException with proper status codes
- Log errors with appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Provide user-friendly error messages
- Handle database connection failures gracefully

### Container & Deployment
- All database migrations run automatically on container startup via `init_db.py`
- Use environment variables for configuration
- Support for production deployment with Docker Compose
- Automatic schema updates for missing columns/constraints

## File Structure
```
/backend/
  api.py              # Main FastAPI application
  database_connect.py # Database connection and session management
  init_db.py         # Database initialization and migration runner
  create_admin.py    # Admin user creation utility
  startup.sh         # Container startup script
  models/            # SQLAlchemy models (User, Group, Inmate, etc.)
  helpers/           # Utility functions and helpers
  scrapes/           # Jail scraping modules
  utils/             # Shared utilities (MasterUser, etc.)
  alembic/           # Database migrations
    migration_utils.py # Idempotent migration helpers

/frontend/
  src/               # React TypeScript source
  public/            # Static assets
  index.html         # Main HTML template

/amember-plugin/
  incarceration-bot-consolidated.php # Main aMember plugin
  README.md          # Plugin installation instructions
```

## Common Patterns

### Database Models
```python
class MyModel(Base):
    __tablename__ = "my_table"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Always include relationships with back_populates
    related_items = relationship("RelatedModel", back_populates="my_model")
```

### API Endpoints
```python
@app.get("/api/endpoint")
async def get_data(
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    # Implementation
    return {"data": result}
```

### Idempotent Migrations
```python
def upgrade():
    safe_add_column('table_name', 'column_name', sa.String(255), nullable=True)
    
def downgrade():
    safe_drop_column('table_name', 'column_name')
```

## Integration Points

### aMember Plugin
- Located in `/amember-plugin/incarceration-bot-consolidated.php`
- Handles user synchronization between aMember and Incarceration Bot
- Uses product-to-group mapping for access control
- Validates all configuration and provides detailed error logging

### External APIs
- Use master API key authentication for integration endpoints
- All aMember-specific endpoints require `check_integration_permissions()`
- Support for webhooks and external system notifications

## Testing & Quality
- Write tests for all business logic
- Use type hints throughout codebase
- Validate all user inputs
- Test database migrations in isolated environments
- Use environment variables for all configuration

## Deployment Checklist
- [ ] Database migrations run automatically on startup
- [ ] Environment variables properly configured
- [ ] SSL/TLS configured for production
- [ ] Proper logging levels set
- [ ] Resource limits configured for containers
- [ ] Backup strategy for database
- [ ] Monitoring and health checks enabled

## Common Issues & Solutions

### Database Schema Mismatches
- The system automatically handles missing columns via `init_db.py`
- Broken Alembic revisions are detected and fixed automatically
- All schema updates are idempotent and safe to re-run

### Authentication Problems
- Check JWT_SECRET_KEY and MASTER_API_KEY environment variables
- Verify user has proper groups/permissions for requested operations
- Integration endpoints require admin privileges or master API key

### Container Startup Issues
- Check database connectivity and credentials
- Review `init_db.py` logs for migration failures
- Ensure all required environment variables are set

Remember: Always prioritize database agnosticism, security, and automated deployment capabilities when making changes.
