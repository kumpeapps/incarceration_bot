<?php

/**
 * DEPRECATED: This file is deprecated in favor of incarceration-bot-consolidated.php
 * 
 * This simple plugin version lacks:
 * - Product-to-group mapping
 * - Complete user lifecycle event handling
 * - Access control integration
 * - Proper validation and error logging
 * 
 * Please use incarceration-bot-consolidated.php instead.
 */

if (!defined('AM_APPLICATION_PATH')) {
    die('Direct access not allowed');
}

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
        return strlen($this->getConfig('api_base_url')) > 0;
    }
    
    function init()
    {
        parent::init();
        
        if (!$this->isConfigured()) {
            return;
        }
        
        $this->getDi()->hook->add(Am_Event::USER_AFTER_INSERT, array($this, 'onUserInsert'));
    }
    
    function _initSetupForm(Am_Form_Setup $form)
    {
        $form->addText('api_base_url', array('class' => 'am-el-wide'))
            ->setLabel('API Base URL')
            ->addRule('required')
            ->setValue('https://your-domain.com/api');
            
        $form->addText('api_key', array('class' => 'am-el-wide'))
            ->setLabel('API Key')
            ->addRule('required');
    }
    
    function onUserInsert(Am_Event $event)
    {
        $user = $event->getUser();
        // Simple logging for testing
        Am_Di::getInstance()->logger->debug("IncarcerationBot: User created - " . $user->login);
    }
}
