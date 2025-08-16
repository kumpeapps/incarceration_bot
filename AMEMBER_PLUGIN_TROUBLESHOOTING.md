# aMember Plugin Installation Instructions

## Plugin Installation Issue - Troubleshooting

If the aMember plugin is not activating, here are the most common causes and solutions:

### 1. File Naming and Location

aMember plugins must follow a specific naming convention:

**Correct Structure:**
```
amember/application/default/plugins/misc/incarceration-bot.php
```

**Or for newer aMember versions:**
```
amember/application/default/plugins/misc/incarceration-bot/
    incarceration-bot.php
    bootstrap.php (optional)
```

### 2. File Permissions

Ensure the plugin file has correct permissions:
```bash
chmod 644 incarceration-bot.php
chown www-data:www-data incarceration-bot.php  # or your web server user
```

### 3. PHP Syntax Check

Check for PHP syntax errors:
```bash
php -l incarceration-bot.php
```

### 4. aMember Version Compatibility

Different aMember versions have different plugin structures:

#### For aMember 4.x:
- Plugins go in `amember/application/default/plugins/misc/`
- Use `public function` instead of just `function`
- Configuration prefix should be `misc.pluginname.`

#### For aMember 5.x and 6.x:
- May require additional bootstrap files
- Different event system
- Different configuration methods

### 5. Common Code Issues

#### Issue 1: Configuration Prefix
```php
// Wrong
protected $_configPrefix = 'misc.';

// Correct
protected $_configPrefix = 'misc.incarceration_bot.';
```

#### Issue 2: Method Visibility
```php
// Wrong (in newer versions)
function init() { }

// Correct
public function init() { }
```

#### Issue 3: Missing isConfigured() Method
```php
public function isConfigured()
{
    return strlen($this->getConfig('api_base_url')) && strlen($this->getConfig('api_key'));
}
```

### 6. Plugin Activation Steps

1. **Upload the plugin file** to the correct directory
2. **Clear aMember cache**:
   ```
   Admin -> Utilities -> Clear Cache
   ```
3. **Check aMember error logs**:
   ```
   amember/data/logs/
   ```
4. **Go to Admin -> Setup -> Plugins**
5. **Look for "Incarceration Bot Integration"** in the Misc section
6. **Click "Configure"** to activate

### 7. Debug Steps

#### Check aMember Logs
```bash
tail -f amember/data/logs/error.log
tail -f amember/data/logs/php_error.log
```

#### Enable Debug Mode
Add to `amember/application/configs/config.php`:
```php
$config['debug'] = true;
$config['display_errors'] = true;
```

#### Test Plugin Loading
Create a simple test file in the same directory:
```php
<?php
// test-plugin.php
if (!defined('AM_APPLICATION_PATH')) {
    die('Direct access not allowed');
}

class Am_Plugin_TestPlugin extends Am_Plugin
{
    const PLUGIN_STATUS = self::STATUS_PRODUCTION;
    const PLUGIN_COMM = self::COMM_FREE;
    const PLUGIN_REVISION = '1.0.0';
    
    protected $_configPrefix = 'misc.test_plugin.';
    
    public function getTitle()
    {
        return "Test Plugin";
    }
    
    public function getDescription()
    {
        return "Test plugin to verify plugin system works";
    }
}
```

### 8. Alternative Plugin Structure (For Newer aMember)

Create a directory structure:
```
incarceration-bot/
    incarceration-bot.php  (main plugin file)
    bootstrap.php         (optional loader)
```

**bootstrap.php:**
```php
<?php
if (!defined('AM_APPLICATION_PATH')) {
    die('Direct access not allowed');
}

require_once __DIR__ . '/incarceration-bot.php';
```

### 9. Manual Plugin Registration (Last Resort)

If automatic detection fails, you can manually register the plugin by adding to `amember/application/configs/config.php`:

```php
$config['plugins']['misc'][] = 'incarceration-bot';
```

### 10. Contact Information

If none of these solutions work:

1. **Check aMember version**: Admin -> Utilities -> System Info
2. **Check PHP version compatibility**
3. **Review aMember documentation** for your specific version
4. **Contact aMember support** with the plugin file and error logs

### 11. Quick Fix Version

Here's a minimal version that should definitely activate:

```php
<?php
if (!defined('AM_APPLICATION_PATH')) {
    die('Direct access not allowed');
}

class Am_Plugin_IncarcerationBot extends Am_Plugin
{
    const PLUGIN_STATUS = self::STATUS_PRODUCTION;
    const PLUGIN_COMM = self::COMM_FREE;
    const PLUGIN_REVISION = '1.0.0';
    
    protected $_configPrefix = 'misc.incarceration_bot.';
    
    public function getTitle()
    {
        return "Incarceration Bot Integration";
    }
    
    public function getDescription()
    {
        return "Basic plugin for testing activation";
    }
    
    public function _initSetupForm(Am_Form_Setup $form)
    {
        $form->addText('test_field')
            ->setLabel('Test Field')
            ->setValue('Plugin is working!');
    }
}
```

This minimal version should activate and appear in the plugins list. Once it's working, you can gradually add the full functionality back.
