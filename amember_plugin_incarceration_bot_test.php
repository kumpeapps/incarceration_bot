<?php

class Am_Plugin_IncarcerationBot extends Am_Plugin
{
    const PLUGIN_STATUS = self::STATUS_PRODUCTION;
    const PLUGIN_COMM = self::COMM_FREE;
    const PLUGIN_REVISION = '1.0.0';
    
    protected $_configPrefix = 'incarceration_bot.';
    
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
        return false; // This will force the configuration page to show
    }
    
    function _initSetupForm(Am_Form_Setup $form)
    {
        $form->addText('api_base_url', array('class' => 'am-el-wide'))
            ->setLabel('API Base URL')
            ->addRule('required')
            ->setValue('http://localhost:8000/api');
            
        $form->addText('api_key', array('class' => 'am-el-wide'))
            ->setLabel('API Key')
            ->addRule('required')
            ->setValue('your-master-api-key-for-integrations');
    }
}
