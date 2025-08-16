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
            ->addRule('required')
            ->setValue('https://your-domain.com/api');
            
        $form->addText('api_key', array('class' => 'am-el-wide'))
            ->setLabel('API Key')
            ->addRule('required');
            
        // Use static groups instead of API call for now
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
        
        if (!$this->isConfigured()) {
            return;
        }
        
        // Hook into aMember events
        $this->getDi()->hook->add(Am_Event::USER_AFTER_INSERT, array($this, 'onUserInsert'));
        $this->getDi()->hook->add(Am_Event::USER_AFTER_UPDATE, array($this, 'onUserUpdate'));
        $this->getDi()->hook->add(Am_Event::USER_AFTER_DELETE, array($this, 'onUserDelete'));
    }
    
    function isConfigured()
    {
        return strlen($this->getConfig('api_base_url')) > 0 && strlen($this->getConfig('api_key')) > 0;
    }
    
    function onUserInsert(Am_Event $event)
    {
        $user = $event->getUser();
        $this->logDebug("User created: " . $user->login);
        
        // Basic user data
        $userData = array(
            'username' => $user->login,
            'email' => $user->email,
            'amember_user_id' => $user->user_id,
            'is_active' => true
        );
        
        // Always sync aMember password
        if (!empty($user->pass)) {
            $userData['hashed_password'] = $user->pass;
            $userData['password_format'] = 'phpass'; // Default for aMember
        }
        
        $this->apiRequest('POST', '/users/amember', $userData);
    }
    
    function onUserUpdate(Am_Event $event)
    {
        $user = $event->getUser();
        $this->logDebug("User updated: " . $user->login);
        // Basic update logic here
    }
    
    function onUserDelete(Am_Event $event)
    {
        $user = $event->getUser();
        $this->logDebug("User deleted: " . $user->login);
        // Basic delete logic here
    }
    
    private function apiRequest($method, $endpoint, $data = null)
    {
        $api_base_url = rtrim($this->getConfig('api_base_url', ''), '/');
        $api_key = $this->getConfig('api_key', '');
        
        if (empty($api_base_url) || empty($api_key)) {
            $this->logError("API configuration missing");
            return false;
        }
        
        // Simple API request logic
        return true; // Placeholder for now
    }
    
    private function logDebug($message)
    {
        if ($this->getConfig('debug_mode')) {
            Am_Di::getInstance()->logger->debug("[IncarcerationBot] " . $message);
        }
    }
    
    private function logError($message)
    {
        Am_Di::getInstance()->logger->error("[IncarcerationBot] " . $message);
    }
}
