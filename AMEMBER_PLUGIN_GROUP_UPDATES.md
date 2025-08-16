# aMember Plugin Group Management Updates

## Overview
Updated the aMember plugin (`amember_plugin_incarceration_bot.php`) to properly integrate with the new group-based user management system, specifically adding support for the `locked` group while preserving `banned` group integrity.

## Changes Made

### 1. Updated Default Group Options
Added more group options in the configuration:
- `user` - Regular User (default)
- `admin` - Administrator  
- `moderator` - Moderator
- `guest` - Guest
- `locked` - Locked User

### 2. Password Hash Synchronization
- **aMember Password Sync**: Uses aMember's bcrypt password hashes directly
- **Seamless Login**: Users can login to Incarceration Bot with their aMember passwords
- **No Password Management**: No need for separate password handling or generation
- **Security**: Maintains the same security level as aMember's password storage

### 3. Automatic Lock Status Management
- **User Creation**: When a user is created in aMember as locked, they are automatically assigned to the `locked` group
- **User Updates**: When a user's lock status changes in aMember, their `locked` group membership is automatically updated
- **Banned User Protection**: Users in the `banned` group are completely protected from lock status changes

### 3. Smart Lock Handling Logic
The plugin now includes `handleUserLockStatus()` method that:
- Checks if user is in `banned` group before making any changes
- Adds users to `locked` group when they are locked in aMember
- Removes users from `locked` group when they are unlocked in aMember
- Logs all group assignment/removal actions for debugging

### 4. Enhanced Configuration UI
- Added informational text explaining that `locked` and `banned` groups are automatically managed
- Updated product mapping examples to show all available groups
- Added note that `banned` group is reserved for manual administration

### 5. Group Creation Service Updates
Updated `user_group_service.py` to ensure all default groups are created:
- `admin` - Administrators
- `user` - Regular Users
- `moderator` - Moderators  
- `locked` - Locked Users
- `banned` - Banned Users
- `guest` - Guests

## Key Features

### Banned User Protection
- Users in the `banned` group are completely immune to lock status changes
- This ensures manual banning cannot be overridden by aMember sync

### Password Synchronization
- **Perfect Integration**: Uses aMember's bcrypt password hashes directly - no separate password management needed
- **Seamless User Experience**: Users login to Incarceration Bot with their existing aMember passwords
- **Security**: Maintains the same security level as aMember's password storage
- **No Conflicts**: Eliminates password sync issues and provides a unified authentication experience

### Automatic Lock Management
- **Seamless integration** between aMember user lock status and Incarceration Bot groups
- **No manual intervention** required for lock/unlock operations

### Comprehensive Logging
- All group assignments and changes are logged
- Debug mode provides detailed information about group management decisions

## Usage

1. **Install**: Place `amember_plugin_incarceration_bot.php` in your aMember plugins directory
2. **Configure**: Set API URL, API key, and default group
3. **Map Products**: Configure product-to-group mappings as needed
4. **Enable**: Activate the plugin

The plugin will automatically:
- Create users in Incarceration Bot when they subscribe in aMember
- Assign appropriate groups based on products and user status
- Manage locked status automatically
- Respect banned users and never modify their groups
- Update user information when changed in aMember

## API Endpoints Used

- `POST /users/amember` - Create new user
- `PUT /users/amember/{id}` - Update user
- `GET /users/amember/{id}` - Get user info (for group checking)
- `POST /users/amember/{id}/groups` - Assign user to group
- `DELETE /users/amember/{id}/groups/{group}` - Remove user from group

## Testing

To test the locked group functionality:
1. Create a user in aMember
2. Lock the user in aMember admin
3. Verify user is added to `locked` group in Incarceration Bot
4. Unlock the user in aMember
5. Verify user is removed from `locked` group in Incarceration Bot

Banned users should never have their group memberships modified by the plugin.
