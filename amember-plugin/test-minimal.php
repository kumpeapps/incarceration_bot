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
    
    function getTitle()
    {
        return "Incarceration Bot Integration";
    }
    
    function getDescription()
    {
        return "Test plugin for Incarceration Bot";
    }
    
    function _initSetupForm(Am_Form_Setup $form)
    {
        $form->addText('api_base_url')
            ->setLabel('API Base URL')
            ->addRule('required');
    }
    
    function init()
    {
        parent::init();
    }
}
