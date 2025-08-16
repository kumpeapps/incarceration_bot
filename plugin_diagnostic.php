<?php
/**
 * aMember Plugin Diagnostic Script
 * 
 * This script helps diagnose why the Incarceration Bot plugin 
 * won't activate in aMember.
 * 
 * Usage: Place this file in your aMember root directory and run:
 * php plugin_diagnostic.php
 */

echo "aMember Plugin Diagnostic Script\n";
echo "================================\n\n";

// Check if we're in aMember directory
if (!file_exists('application/default/plugins/misc/incarceration-bot.php')) {
    echo "❌ ERROR: incarceration-bot.php not found in application/default/plugins/misc/\n";
    echo "   Please ensure the plugin file is in the correct location.\n\n";
    exit(1);
}

echo "✅ Plugin file found in correct location\n";

// Check PHP syntax
echo "Checking PHP syntax...\n";
$output = shell_exec('php -l application/default/plugins/misc/incarceration-bot.php 2>&1');
if (strpos($output, 'No syntax errors detected') !== false) {
    echo "✅ PHP syntax is valid\n";
} else {
    echo "❌ PHP syntax errors detected:\n";
    echo $output . "\n";
    echo "Please fix syntax errors before continuing.\n\n";
    exit(1);
}

// Check file permissions
$perms = fileperms('application/default/plugins/misc/incarceration-bot.php');
$octal = substr(sprintf('%o', $perms), -4);
echo "File permissions: $octal\n";
if ($perms & 0x0004) {
    echo "✅ File is readable\n";
} else {
    echo "❌ File is not readable by web server\n";
    echo "   Try: chmod 644 application/default/plugins/misc/incarceration-bot.php\n\n";
}

// Try to include the plugin file
echo "Testing plugin file inclusion...\n";
try {
    // Define aMember constants to prevent die() calls
    if (!defined('AM_APPLICATION_PATH')) {
        define('AM_APPLICATION_PATH', dirname(__FILE__));
    }
    
    // Capture any output from the include
    ob_start();
    include_once 'application/default/plugins/misc/incarceration-bot.php';
    $includeOutput = ob_get_clean();
    
    if (!empty($includeOutput)) {
        echo "⚠️  Plugin file produced output during inclusion:\n";
        echo $includeOutput . "\n";
    }
    
    // Check if class was defined
    if (class_exists('Am_Plugin_IncarcerationBot')) {
        echo "✅ Plugin class Am_Plugin_IncarcerationBot defined successfully\n";
        
        // Check class methods
        $class = new ReflectionClass('Am_Plugin_IncarcerationBot');
        $requiredMethods = ['getTitle', 'getDescription', '_initSetupForm', 'init'];
        
        foreach ($requiredMethods as $method) {
            if ($class->hasMethod($method)) {
                echo "✅ Required method $method() exists\n";
            } else {
                echo "❌ Missing required method $method()\n";
            }
        }
        
    } else {
        echo "❌ Plugin class Am_Plugin_IncarcerationBot not defined\n";
        echo "   Check that the class name matches the filename convention\n\n";
    }
    
} catch (ParseError $e) {
    echo "❌ Parse error in plugin file:\n";
    echo $e->getMessage() . "\n\n";
} catch (Error $e) {
    echo "❌ Fatal error in plugin file:\n";
    echo $e->getMessage() . "\n\n";
} catch (Exception $e) {
    echo "❌ Exception in plugin file:\n";
    echo $e->getMessage() . "\n\n";
}

// Check aMember cache
if (is_dir('data/cache')) {
    echo "Checking aMember cache...\n";
    $cacheFiles = glob('data/cache/*');
    if (!empty($cacheFiles)) {
        echo "⚠️  aMember cache contains " . count($cacheFiles) . " files\n";
        echo "   Consider clearing cache: rm -rf data/cache/*\n";
    } else {
        echo "✅ aMember cache is empty\n";
    }
} else {
    echo "ℹ️  aMember cache directory not found (normal for some setups)\n";
}

echo "\n";
echo "Common Solutions:\n";
echo "================\n";
echo "1. Clear aMember cache: rm -rf data/cache/*\n";
echo "2. Check file permissions: chmod 644 incarceration-bot.php\n";
echo "3. Restart web server/PHP-FPM if using opcache\n";
echo "4. Check aMember error logs in data/logs/\n";
echo "5. Ensure plugin filename matches: incarceration-bot.php\n";
echo "\n";
echo "If plugin still won't activate, check aMember admin > Setup/Config > Logs\n";
echo "for detailed error messages.\n";
?>
