# aMember Plugin for Incarceration Bot

## **Consolidated Plugin (RECOMMENDED)**

**Use this file**: `incarceration-bot-consolidated.php`

This is the main, fully-featured plugin with:
- ✅ Complete user synchronization (create, update, delete)
- ✅ Product-to-group mapping with validation
- ✅ Comprehensive error logging and debugging
- ✅ Access control integration
- ✅ Malformed mapping validation with detailed error messages

## **Legacy Files (For Reference Only)**

These files are kept for reference but should not be used in production:

- `incarceration-bot.php` - Original version with basic setup form only
- `incarceration-bot-simple.php` - Minimal version with basic user creation
- `incarceration-bot-minimal.php` - Bare minimum plugin structure
- `incarceration-bot.php.backup` - Backup of previous version
- `test-minimal.php` - Testing file

## **Installation Instructions**

1. Copy `incarceration-bot-consolidated.php` to your aMember `application/default/plugins/misc/` directory
2. Rename it to `incarceration-bot.php` in the target directory
3. Activate the plugin in aMember admin panel
4. Configure the API settings:
   - **API Base URL**: Your Incarceration Bot API endpoint (e.g., `https://your-domain.com/api`)
   - **API Key**: Use your `MASTER_API_KEY` environment variable or generate a new API key from an admin user
   - **Default Group**: Choose the default group for new users
   - **Product Mappings**: Map aMember product IDs to Incarceration Bot groups

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

The consolidated plugin includes validation for:
- ✅ Product IDs must be numeric
- ✅ Group names cannot be empty
- ✅ Malformed lines are logged with line numbers
- ✅ Comments and empty lines are properly ignored

## **API Key Configuration**

You can use either:
1. **Master API Key** (recommended): Set `MASTER_API_KEY` environment variable in your backend
2. **User API Key**: Generate an API key from an admin user in Incarceration Bot admin panel

## **Debugging**

Enable "Debug Mode" in the plugin settings to see detailed logs in aMember's log files.
