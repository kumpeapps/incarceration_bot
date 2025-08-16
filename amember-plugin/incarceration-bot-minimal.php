<?php

/**
 * DEPRECATED: This file is deprecated in favor of incarceration-bot-consolidated.php
 * 
 * This minimal plugin version is for testing only and lacks all functionality.
 * Please use incarceration-bot-consolidated.php instead.
 */

class Am_Plugin_IncarcerationBot extends Am_Plugin
{
    const PLUGIN_STATUS = self::STATUS_PRODUCTION;
    const PLUGIN_COMM = self::COMM_FREE;
    const PLUGIN_REVISION = '1.0.0';
    
    protected $_configPrefix = 'misc.';
    
    function getTitle()
    {
        return "Incarceration Bot Integration";
    }
    
    function getDescription()
    {
        return "Synchronizes aMember users with Incarceration Bot";
    }
    
    function isConfigured()
    {
        return true;
    }
}
