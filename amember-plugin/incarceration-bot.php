<?php

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
    
    function _initSetupForm(Am_Form_Setup $form)
    {
        $form->addStatic()
            ->setContent('<div class="am-info"><strong>Setup Instructions:</strong><br/>
            1. <strong>Option A:</strong> Set MASTER_API_KEY environment variable in your backend for automatic access<br/>
            2. <strong>Option B:</strong> Generate an API key for an admin user in your Incarceration Bot admin panel<br/>
            3. Enter the API key below and configure your product mappings<br/>
            4. aMember will then sync all users to Incarceration Bot automatically</div>');
            
        $form->addText('api_base_url', array('class' => 'am-el-wide'))
            ->setLabel('API Base URL')
            ->setValue('https://your-domain.com/api')
            ->addRule('required');
            
        $form->addText('api_key', array('class' => 'am-el-wide'))
            ->setLabel('API Key')
            ->setDescription('Use MASTER_API_KEY environment variable or generate from admin user in Incarceration Bot')
            ->addRule('required');
            
        $form->addSelect('default_group')
            ->setLabel('Default Group for New Users')
            ->loadOptions(array(
                'user' => 'Regular User',
                'admin' => 'Administrator',
                'moderator' => 'Moderator',
                'super_admin' => 'Super Administrator',
                'api_user' => 'API User',
                'guest' => 'Guest',
                'banned' => 'Banned',
                'locked' => 'Locked'
            ))
            ->setValue('user');
            
        $form->addAdvCheckbox('sync_existing_users')
            ->setLabel('Sync All Existing aMember Users')
            ->setDescription('Check this to sync all existing aMember users to Incarceration Bot on first activation');
    }
}
