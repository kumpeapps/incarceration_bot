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
        return "Synchronizes aMember users with Incarceration Bot. Always syncs existing aMember passwords.";
    }
    
    function _initSetupForm(Am_Form_Setup $form)
    {
        $form->addText('api_base_url', array('class' => 'am-el-wide'))
            ->setLabel('API Base URL')
            ->setValue('https://your-domain.com/api')
            ->addRule('required');
            
        $form->addText('api_key', array('class' => 'am-el-wide'))
            ->setLabel('API Key')
            ->addRule('required');
            
        // Use static groups - NO API calls during form setup
        $staticGroups = array(
            'user' => 'Regular User',
            'admin' => 'Administrator', 
            'moderator' => 'Moderator',
            'locked' => 'Locked',
            'banned' => 'Banned'
        );
        
        $form->addSelect('default_group')
            ->setLabel('Default Group for New Users')
            ->loadOptions($staticGroups)
            ->setValue('user');
            
        $form->addSelect('locked_group')
            ->setLabel('Group for Locked Users')
            ->loadOptions(array_merge(array('' => 'No Change'), $staticGroups))
            ->setValue('locked');
            
        $form->addSelect('banned_group')
            ->setLabel('Group for Banned Users') 
            ->loadOptions(array_merge(array('' => 'No Change'), $staticGroups))
            ->setValue('banned');
            
        $form->addAdvCheckbox('debug_mode')
            ->setLabel('Debug Mode');
    }
    
    function init()
    {
        parent::init();
        
        // NO event hooks for now - they may be causing the fatal error
    }
    
    function isConfigured()
    {
        return strlen($this->getConfig('api_base_url')) > 0 && strlen($this->getConfig('api_key')) > 0;
    }
}
