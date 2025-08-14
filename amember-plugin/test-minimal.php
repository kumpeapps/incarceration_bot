<?php

if (!defined('AM_APPLICATION_PATH')) {
    die('Direct access not allowed');
}

class Am_Plugin_TestMinimal extends Am_Plugin
{
    const PLUGIN_STATUS = self::STATUS_PRODUCTION;
    const PLUGIN_COMM = self::COMM_FREE;
    const PLUGIN_REVISION = '1.0.0';
    
    function getTitle()
    {
        return "Test Minimal Plugin";
    }
    
    function getDescription()
    {
        return "Minimal test plugin to check aMember compatibility";
    }
    
    function isConfigured()
    {
        return true;
    }
    
    function init()
    {
        parent::init();
    }
}
