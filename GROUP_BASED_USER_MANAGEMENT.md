# Group-Based User Management System

## Overview

The Incarceration Bot system has been updated to use a flexible group-based user management system instead of simple role-based permissions. This allows for more granular control over user permissions and easier integration with external systems like aMember.

## Database Structure

### New Tables

#### `groups` Table
- `id` (int): Primary key
- `name` (varchar): Unique group identifier (e.g., 'admin', 'user', 'moderator')
- `display_name` (varchar): Human-readable name
- `description` (text): Description of group's purpose
- `is_active` (boolean): Whether group is active
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp

#### `user_groups` Table (Junction Table)
- `id` (int): Primary key
- `user_id` (int): Foreign key to users table
- `group_id` (int): Foreign key to groups table
- `assigned_by` (int): Foreign key to users table (who assigned this group)
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp

### Updated Tables

#### `users` Table
- Removed `role` column
- Users now get their permissions through group membership
- Added backward compatibility property `role` that returns 'admin' if user is in admin group, else 'user'

## Default Groups

The system creates three default groups:

1. **admin** - Administrators
   - Full system access
   - User management capabilities
   - All API endpoints

2. **user** - Regular Users
   - Standard user access
   - Can manage their own monitors
   - Limited API access

3. **moderator** - Moderators
   - Enhanced access for content moderation
   - Future enhancement placeholder

## API Endpoints

### Group Management

#### Get All Groups
```
GET /groups
```
- **Auth**: Admin only
- **Response**: Array of group objects

#### Create Group
```
POST /groups
Content-Type: application/json

{
  "name": "new_group",
  "display_name": "New Group",
  "description": "Description of the group"
}
```
- **Auth**: Admin only

#### Get User Groups
```
GET /users/{user_id}/groups
```
- **Auth**: Admin or self
- **Response**: Array of groups user belongs to

#### Assign User to Group
```
POST /users/{user_id}/groups
Content-Type: application/json

{
  "group_name": "admin"
}
```
- **Auth**: Admin only

#### Remove User from Group
```
DELETE /users/{user_id}/groups/{group_name}
```
- **Auth**: Admin only

#### Get Group Users
```
GET /groups/{group_name}/users
```
- **Auth**: Admin only
- **Response**: Array of users in the group

### aMember Integration

The system includes dedicated endpoints for aMember integration:

#### Create User from aMember
```
POST /users/amember
Content-Type: application/json

{
  "username": "user123",
  "email": "user@example.com",
  "password": "generated_password",
  "amember_user_id": 123,
  "is_active": true
}
```

#### Update User from aMember
```
PUT /users/amember/{amember_user_id}
Content-Type: application/json

{
  "username": "updated_username",
  "email": "updated@example.com",
  "is_active": true
}
```

#### Assign aMember User to Group
```
POST /users/amember/{amember_user_id}/groups
Content-Type: application/json

{
  "group_name": "admin"
}
```

## Migration Guide

### Running the Migration

1. **Run the Alembic migration:**
   ```bash
   cd backend
   alembic upgrade head
   ```

2. **Initialize groups and migrate existing users:**
   ```bash
   cd backend
   python init_groups.py
   ```

3. **Remove the role column (optional, after verifying everything works):**
   ```bash
   cd backend
   alembic upgrade 009_remove_role_column
   ```

### Migration Steps

1. **Create new tables**: `groups` and `user_groups`
2. **Insert default groups**: admin, user, moderator
3. **Migrate existing users**: 
   - Users with `role = 'admin'` → assigned to 'admin' group
   - Users with `role = 'user'` or `NULL` → assigned to 'user' group
4. **Update API endpoints**: Use group-based permissions
5. **Remove role column**: After verification (optional)

## User Model Updates

The User model now includes:

```python
def has_group(self, group_name: str) -> bool:
    """Check if user belongs to a specific group."""

def is_admin(self) -> bool:
    """Check if user has admin privileges."""

def get_groups(self) -> list:
    """Get list of active groups user belongs to."""

@property
def role(self) -> str:
    """Backward compatibility property."""
```

## aMember Plugin

The included aMember plugin (`amember_plugin_incarceration_bot.php`) handles:

1. **User synchronization**: Create/update/deactivate users
2. **Group assignment**: Map aMember products to groups
3. **Automatic management**: Handle subscription changes
4. **Configuration**: API URL, credentials, product mappings

### Plugin Configuration

1. Install the plugin in your aMember installation
2. Configure:
   - API Base URL: `https://your-domain.com/api`
   - API Key: Your authentication key
   - Product Mappings: Map product IDs to group names
   - Default Group: Group for new users

### Product Mapping Format

```
# Product ID = Group Name
1=user
2=admin
3=moderator
```

## Backward Compatibility

The system maintains backward compatibility:

1. **Role property**: Users still have a `role` property that returns 'admin' or 'user'
2. **API responses**: Include both groups and legacy role field
3. **Permission checks**: Old `current_user.role == "admin"` still works via `current_user.is_admin()`

## Security Considerations

1. **API Key Authentication**: aMember endpoints should use API key authentication in production
2. **Group Validation**: Ensure only valid groups can be assigned
3. **Admin Protection**: Prevent removal of last admin user
4. **Audit Trail**: Track who assigns/removes group memberships

## Testing

After migration, verify:

1. **Admin users**: Can access admin functions
2. **Regular users**: Have appropriate restrictions
3. **Group management**: CRUD operations work correctly
4. **aMember integration**: User sync and group assignment
5. **API endpoints**: All permissions work as expected

## Future Enhancements

1. **Permission system**: More granular permissions per group
2. **Role inheritance**: Hierarchical group relationships
3. **Time-based groups**: Temporary group assignments
4. **API rate limiting**: Per-group rate limits
5. **Audit logging**: Detailed permission change logs
