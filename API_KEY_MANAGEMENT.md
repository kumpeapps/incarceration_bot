# API Key Management for aMember Integration

This document explains how to generate and manage API keys for the Incarceration Bot aMember integration.

## Overview

The Incarceration Bot system supports two methods for API authentication with aMember:

1. **Master API Key** (Environment Variable) - Recommended for production
2. **User-Generated API Key** (Admin Panel) - For development/testing

## Method 1: Master API Key (Recommended)

### Setup
1. Set the `MASTER_API_KEY` environment variable in your backend deployment
2. Use any secure 32+ character string as the key
3. Configure aMember plugin with this key

### Benefits
- No database dependency
- Always available
- Full admin permissions
- Simple deployment

### Example
```bash
# In your .env file or deployment config
MASTER_API_KEY=your-secure-32-character-api-key-here
```

## Method 2: User-Generated API Key

### Setup
1. Login to your Incarceration Bot admin panel
2. Navigate to Users page
3. Find an admin user
4. Click the Key icon to generate API key
5. Copy the generated key to aMember plugin config

### Benefits
- User-specific permissions
- Audit trail
- Can be regenerated
- Revocable

### Steps
1. **Access Admin Panel**: Login with admin credentials
2. **Navigate to Users**: Go to the Users management page
3. **Select User**: Choose an admin user for API key generation
4. **Generate Key**: Click the key icon (🔑) next to the user
5. **Copy Key**: Copy the generated API key from the dialog
6. **Configure aMember**: Paste the key into the aMember plugin configuration

## aMember Plugin Configuration

### Required Settings
- **API Base URL**: Your Incarceration Bot API endpoint (e.g., `https://your-domain.com/api`)
- **API Key**: Either master key or user-generated key
- **Default Group**: Group to assign new users (`user`, `admin`, `moderator`)

### Optional Settings
- **Sync Existing Users**: Check to sync all existing aMember users on activation
- **Product Mappings**: Map aMember products to Incarceration Bot groups

## Security Considerations

### Master API Key
- Use a cryptographically secure random string
- Store securely in environment variables
- Rotate periodically
- Never commit to version control

### User API Keys
- Generate for admin users only
- Store securely in aMember configuration
- Regenerate if compromised
- Monitor usage in logs

## Testing

1. **Verify API Access**: Test API endpoint with your key
2. **Create Test User**: Create a user in aMember and verify sync
3. **Check Groups**: Ensure users are assigned to correct groups
4. **Monitor Logs**: Watch for sync errors or issues

## Troubleshooting

### Common Issues
- **Invalid API Key**: Regenerate key or check environment variable
- **Connection Failed**: Verify API base URL and network connectivity
- **Sync Errors**: Check user data format and group mappings
- **Permission Denied**: Ensure API key has admin permissions

### Debug Mode
Enable debug mode in aMember plugin to see detailed sync logs.

## Support

For issues with:
- **API Key Generation**: Check admin panel access and user permissions
- **aMember Plugin**: Verify plugin activation and configuration
- **Sync Issues**: Check API logs and group mappings
