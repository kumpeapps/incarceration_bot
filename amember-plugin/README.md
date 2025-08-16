# aMember Plugin for Incarceration Bot

## **Installation**

**File**: `incarceration-bot.php`

This is the complete, production-ready plugin with:
- ✅ Complete user synchronization (create, update, delete)
- ✅ Automatic password sync (phpass, bcrypt, argon2, MD5, SHA1, crypt)
- ✅ Product-to-group mapping with validation
- ✅ User status handling (active, locked, banned)
- ✅ Dynamic group loading from Incarceration Bot API
- ✅ Comprehensive error logging and debugging
- ✅ Malformed mapping validation with detailed error messages

## **Installation Instructions**

1. Copy `incarceration-bot.php` to your aMember `application/default/plugins/misc/` directory
2. Activate the plugin in aMember admin panel
3. Configure the API settings:
   - **API Base URL**: Your Incarceration Bot API endpoint (e.g., `https://your-domain.com/api`)
   - **API Key**: Use your `MASTER_API_KEY` environment variable or generate a new API key from an admin user
   - **Default Group**: Choose the default group for new users
   - **Locked Group**: Group to assign when users are locked (optional)
   - **Banned Group**: Group to assign when users are banned/not approved (optional)
   - **Product Mappings**: Map aMember product IDs to Incarceration Bot groups

## **User Status Handling**

The plugin automatically handles different user states:

- **Active Users**: Assigned to default group or product-mapped groups
- **Locked Users**: Moved to locked group (if configured)
- **Banned/Unapproved Users**: Moved to banned group (if configured)
- **Status Changes**: Automatically updates groups when user status changes

## **Password Synchronization**

The plugin **always** syncs aMember passwords to Incarceration Bot (no random password generation):

- ✅ **phpass** (aMember/WordPress default): `$P$` and `$H$` formats
- ✅ **bcrypt**: `$2a$`, `$2b$`, `$2x$`, `$2y$` formats  
- ✅ **argon2i/argon2id**: Modern PHP password_hash() formats
- ✅ **crypt**: Unix MD5 crypt format `$1$`
- ✅ **MD5**: 32-character hex strings
- ✅ **SHA1**: 40-character hex strings
- ✅ **Auto-detection**: Automatically detects password format from hash

**No random passwords are ever generated.** The plugin preserves your existing aMember user experience by syncing the actual password hashes.

## **Product Mapping Format**

```
# Format: product_id=group_name (one per line)
# Comments start with #
1=user
2=admin
3=moderator
4=super_admin
```

## **Validation Features**

The plugin includes validation for:
- ✅ Product IDs must be numeric
- ✅ Group names cannot be empty
- ✅ Malformed lines are logged with line numbers
- ✅ Comments and empty lines are properly ignored
- ✅ Groups are dynamically loaded from Incarceration Bot API

## **API Key Configuration**

You can use either:
1. **Master API Key** (recommended): Set `MASTER_API_KEY` environment variable in your backend
2. **User API Key**: Generate an API key from an admin user in Incarceration Bot admin panel

## **Debugging**

Enable "Debug Mode" in the plugin settings to see detailed logs in aMember's log files.
