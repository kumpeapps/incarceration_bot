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
        
        // Add event hooks only if plugin is configured
        if ($this->isConfigured()) {
            $this->getDi()->hook->add(Am_Event::USER_AFTER_INSERT, array($this, 'onUserInsert'));
            $this->getDi()->hook->add(Am_Event::USER_AFTER_UPDATE, array($this, 'onUserUpdate'));
            $this->getDi()->hook->add(Am_Event::USER_AFTER_DELETE, array($this, 'onUserDelete'));
            $this->getDi()->hook->add(Am_Event::ACCESS_AFTER_INSERT, array($this, 'onAccessInsert'));
            $this->getDi()->hook->add(Am_Event::ACCESS_AFTER_DELETE, array($this, 'onAccessDelete'));
        }
    }
    
    function isConfigured()
    {
        return strlen($this->getConfig('api_base_url')) > 0 && strlen($this->getConfig('api_key')) > 0;
    }
    
    // Event Handlers
    function onUserInsert(Am_Event $event)
    {
        $user = $event->getUser();
        $this->debugLog("User Insert Event: {$user->login}");
        $this->syncUserToBot($user, 'create');
    }
    
    function onUserUpdate(Am_Event $event)
    {
        $user = $event->getUser();
        $this->debugLog("User Update Event: {$user->login}");
        $this->syncUserToBot($user, 'update');
    }
    
    function onUserDelete(Am_Event $event)
    {
        $user = $event->getUser();
        $this->debugLog("User Delete Event: {$user->login}");
        $this->makeApiCall('DELETE', "users/{$user->login}");
    }
    
    function onAccessInsert(Am_Event $event)
    {
        $access = $event->getAccess();
        $user = $this->getDi()->userTable->load($access->user_id);
        $this->debugLog("Access Insert Event: {$user->login}");
        $this->syncUserToBot($user, 'update');
    }
    
    function onAccessDelete(Am_Event $event)
    {
        $access = $event->getAccess();
        $user = $this->getDi()->userTable->load($access->user_id);
        $this->debugLog("Access Delete Event: {$user->login}");
        $this->syncUserToBot($user, 'update');
    }
    
    // Core sync functionality
    function syncUserToBot($user, $action = 'update')
    {
        try {
            // Get user's active products
            $activeProducts = array();
            foreach ($user->getActiveAccess() as $access) {
                $activeProducts[] = $access->product_id;
            }
            
            // Map products to groups
            $userGroups = $this->mapProductsToGroups($activeProducts);
            
            // Prepare user data - ALWAYS sync password, never generate random
            $userData = array(
                'username' => $user->login,
                'email' => $user->email,
                'first_name' => $user->name_f ?: '',
                'last_name' => $user->name_l ?: '',
                'is_active' => !empty($activeProducts),
                'groups' => $userGroups,
                'password' => $user->pass,  // Always use aMember password
                'password_format' => $this->detectPasswordFormat($user->pass)
            );
            
            $this->debugLog("Syncing user data: " . json_encode($userData));
            
            if ($action === 'create') {
                $response = $this->makeApiCall('POST', 'users', $userData);
            } else {
                $response = $this->makeApiCall('PUT', "users/{$user->login}", $userData);
            }
            
            $this->debugLog("Sync response: " . json_encode($response));
            
        } catch (Exception $e) {
            $this->debugLog("Error syncing user {$user->login}: " . $e->getMessage());
        }
    }
    
    function detectPasswordFormat($password)
    {
        if (empty($password)) {
            return 'bcrypt'; // Default for new passwords
        }
        
        // aMember typically uses phpass format
        if (preg_match('/^\$P\$/', $password)) {
            return 'phpass';
        }
        
        // Check for other formats
        if (preg_match('/^\$2[aby]\$/', $password)) {
            return 'bcrypt';
        }
        
        if (preg_match('/^\$argon2/', $password)) {
            return 'argon2';
        }
        
        if (preg_match('/^\$[1-6]\$/', $password)) {
            return 'crypt';
        }
        
        if (preg_match('/^[a-fA-F0-9]{32}$/', $password)) {
            return 'md5';
        }
        
        if (preg_match('/^[a-fA-F0-9]{40}$/', $password)) {
            return 'sha1';
        }
        
        // Default to phpass for aMember
        return 'phpass';
    }
    
    function mapProductsToGroups($productIds)
    {
        $groupMapping = array(
            // Add your product ID to group mappings here
            // Example: 1 => 'premium', 2 => 'admin'
        );
        
        $groups = array();
        foreach ($productIds as $productId) {
            if (isset($groupMapping[$productId])) {
                $groups[] = $groupMapping[$productId];
            }
        }
        
        // If no specific groups mapped, use default
        if (empty($groups)) {
            $groups[] = $this->getConfig('default_group', 'user');
        }
        
        return $groups;
    }
    
    function makeApiCall($method, $endpoint, $data = null)
    {
        $url = rtrim($this->getConfig('api_base_url'), '/') . '/' . ltrim($endpoint, '/');
        $apiKey = $this->getConfig('api_key');
        
        $ch = curl_init();
        curl_setopt_array($ch, array(
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_CUSTOMREQUEST => $method,
            CURLOPT_HTTPHEADER => array(
                'Authorization: Bearer ' . $apiKey,
                'Content-Type: application/json'
            ),
            CURLOPT_TIMEOUT => 30,
            CURLOPT_SSL_VERIFYPEER => false
        ));
        
        if ($data && in_array($method, array('POST', 'PUT', 'PATCH'))) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);
        
        if ($error) {
            throw new Exception("CURL Error: $error");
        }
        
        if ($httpCode >= 400) {
            throw new Exception("HTTP Error $httpCode: $response");
        }
        
        return json_decode($response, true);
    }
    
    function debugLog($message)
    {
        if ($this->getConfig('debug_mode')) {
            $this->getDi()->logger->info("Incarceration Bot: $message");
        }
    }
}
