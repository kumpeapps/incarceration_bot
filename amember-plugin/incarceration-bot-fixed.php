<?php

/**
 * aMember Plugin for Incarceration Bot Integration
 * 
 * Always syncs aMember passwords - no random password generation
 * 
 * Version: 1.0.0
 * Author: Incarceration Bot Development Team
 */

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
        return "Synchronizes aMember users with Incarceration Bot user management system. Always syncs existing aMember passwords - no random password generation.";
    }
    
    function isConfigured()
    {
        return strlen($this->getConfig('api_base_url')) > 0 && strlen($this->getConfig('api_key')) > 0;
    }
    
    function init()
    {
        parent::init();
        
        if (!$this->isConfigured()) {
            return;
        }
        
        // Add event hooks with error handling
        try {
            $this->getDi()->hook->add(Am_Event::USER_AFTER_INSERT, array($this, 'onUserInsert'));
            $this->getDi()->hook->add(Am_Event::USER_AFTER_UPDATE, array($this, 'onUserUpdate'));
            $this->getDi()->hook->add(Am_Event::USER_AFTER_DELETE, array($this, 'onUserDelete'));
            $this->getDi()->hook->add(Am_Event::ACCESS_AFTER_INSERT, array($this, 'onAccessInsert'));
            $this->getDi()->hook->add(Am_Event::ACCESS_AFTER_DELETE, array($this, 'onAccessDelete'));
        } catch (Exception $e) {
            // Silently continue if hooks fail
        }
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
            
        // Use static groups instead of API call to prevent activation issues
        $availableGroups = array(
            'user' => 'Regular User',
            'admin' => 'Administrator', 
            'moderator' => 'Moderator',
            'super_admin' => 'Super Administrator',
            'api_user' => 'API User',
            'guest' => 'Guest',
            'locked' => 'Locked',
            'banned' => 'Banned'
        );
        
        $form->addSelect('default_group')
            ->setLabel('Default Group for New Users')
            ->loadOptions($availableGroups)
            ->setValue('user');
            
        $form->addSelect('locked_group')
            ->setLabel('Group for Locked Users')
            ->loadOptions(array_merge(array('' => 'No Change'), $availableGroups))
            ->setValue('locked');
            
        $form->addSelect('banned_group')
            ->setLabel('Group for Banned Users') 
            ->loadOptions(array_merge(array('' => 'No Change'), $availableGroups))
            ->setValue('banned');
            
        $form->addAdvCheckbox('debug_mode')
            ->setLabel('Debug Mode');
            
        $group = $form->addGroup('product_mapping')
            ->setLabel('Product to Group Mapping');
            
        $group->addStatic()
            ->setContent('<div class="am-info">Map aMember products to Incarceration Bot groups. Format: product_id=group_name (one per line)</div>');
            
        $group->addTextarea('mapping', array('class' => 'am-el-wide', 'rows' => 10))
            ->setLabel('Product Mappings')
            ->setValue("# Example mappings:\n# 1=user\n# 2=admin\n# 3=moderator");
    }
    
    function onUserInsert(Am_Event $event)
    {
        try {
            $user = $event->getUser();
            $this->logDebug("User created: " . $user->login);
            
            // Prepare user data for Incarceration Bot
            $userData = array(
                'username' => $user->login,
                'email' => $user->email,
                'amember_user_id' => $user->user_id,
                'is_active' => $this->determineUserActiveStatus($user)
            );
            
            // Always sync aMember password - never generate random passwords
            if (!empty($user->pass)) {
                $userData['hashed_password'] = $user->pass;
                $userData['password_format'] = $this->detectPasswordFormat($user->pass);
            } else {
                $this->logError("User password is empty for: " . $user->login);
                return;
            }
            
            $response = $this->apiRequest('POST', '/users/amember', $userData);
            
            if ($response && isset($response['id'])) {
                $this->logDebug("User created successfully in Incarceration Bot: " . $response['id']);
                
                // Assign appropriate group based on user status
                $groupName = $this->determineUserGroup($user);
                if ($groupName) {
                    $this->assignUserToGroup($response['id'], $groupName);
                }
            } else {
                $this->logError("Failed to create user in Incarceration Bot for: " . $user->login);
            }
        } catch (Exception $e) {
            $this->logError("Exception in onUserInsert: " . $e->getMessage());
        }
    }
    
    function onUserUpdate(Am_Event $event)
    {
        try {
            $user = $event->getUser();
            $this->logDebug("User updated: " . $user->login);
            
            $userData = array(
                'username' => $user->login,
                'email' => $user->email,
                'is_active' => $this->determineUserActiveStatus($user)
            );
            
            // Always sync password if it exists
            if (!empty($user->pass)) {
                $userData['hashed_password'] = $user->pass;
                $userData['password_format'] = $this->detectPasswordFormat($user->pass);
            }
            
            $response = $this->apiRequest('PUT', '/users/amember/' . $user->user_id, $userData);
            
            if ($response) {
                $this->updateUserGroups($user);
            } else {
                $this->logError("Failed to update user in Incarceration Bot for: " . $user->login);
            }
        } catch (Exception $e) {
            $this->logError("Exception in onUserUpdate: " . $e->getMessage());
        }
    }
    
    function onUserDelete(Am_Event $event)
    {
        try {
            $user = $event->getUser();
            $this->logDebug("User deleted: " . $user->login);
            
            $response = $this->apiRequest('DELETE', '/users/amember/' . $user->user_id);
            
            if (!$response) {
                $this->logError("Failed to delete user in Incarceration Bot for: " . $user->login);
            }
        } catch (Exception $e) {
            $this->logError("Exception in onUserDelete: " . $e->getMessage());
        }
    }
    
    function onAccessInsert(Am_Event $event)
    {
        try {
            $access = $event->getAccess();
            $user = $access->getUser();
            $product = $access->getProduct();
            
            $this->logDebug("Access granted for user: " . $user->login . ", product: " . $product->title);
            
            $group = $this->getGroupForProduct($product->product_id);
            if ($group) {
                $this->assignUserToGroupByAmemberId($user->user_id, $group);
            }
        } catch (Exception $e) {
            $this->logError("Exception in onAccessInsert: " . $e->getMessage());
        }
    }
    
    function onAccessDelete(Am_Event $event)
    {
        try {
            $access = $event->getAccess();
            $user = $access->getUser();
            $product = $access->getProduct();
            
            $this->logDebug("Access removed for user: " . $user->login . ", product: " . $product->title);
            
            $group = $this->getGroupForProduct($product->product_id);
            if ($group && !$this->userHasOtherAccessToGroup($user, $group)) {
                $this->removeUserFromGroupByAmemberId($user->user_id, $group);
            }
        } catch (Exception $e) {
            $this->logError("Exception in onAccessDelete: " . $e->getMessage());
        }
    }
    
    private function apiRequest($method, $endpoint, $data = null)
    {
        $api_base_url = rtrim($this->getConfig('api_base_url', ''), '/');
        $api_key = $this->getConfig('api_key', '');
        
        if (empty($api_base_url) || empty($api_key)) {
            $this->logError("API configuration missing");
            return false;
        }
        
        $url = $api_base_url . $endpoint;
        
        $ch = curl_init();
        curl_setopt_array($ch, array(
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 30,
            CURLOPT_CUSTOMREQUEST => $method,
            CURLOPT_HTTPHEADER => array(
                'Content-Type: application/json',
                'Authorization: Bearer ' . $api_key,
                'User-Agent: aMember-IncarcerationBot-Plugin/1.0.0'
            )
        ));
        
        if ($data && in_array($method, array('POST', 'PUT', 'PATCH'))) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);
        
        if ($error) {
            $this->logError("CURL Error: " . $error);
            return false;
        }
        
        if ($httpCode >= 400) {
            $this->logError("HTTP Error {$httpCode}: " . $response);
            return false;
        }
        
        return json_decode($response, true);
    }
    
    private function assignUserToGroupByAmemberId($amemberUserId, $groupName)
    {
        $response = $this->apiRequest('POST', "/users/amember/{$amemberUserId}/groups", array(
            'group_name' => $groupName
        ));
        
        if ($response) {
            $this->logDebug("User {$amemberUserId} assigned to group: {$groupName}");
        } else {
            $this->logError("Failed to assign user {$amemberUserId} to group: {$groupName}");
        }
    }
    
    private function removeUserFromGroupByAmemberId($amemberUserId, $groupName)
    {
        $response = $this->apiRequest('DELETE', "/users/amember/{$amemberUserId}/groups/{$groupName}");
        
        if ($response) {
            $this->logDebug("User {$amemberUserId} removed from group: {$groupName}");
        } else {
            $this->logError("Failed to remove user {$amemberUserId} from group: {$groupName}");
        }
    }
    
    private function assignUserToGroup($userId, $groupName)
    {
        $response = $this->apiRequest('POST', "/users/{$userId}/groups", array(
            'group_name' => $groupName
        ));
        
        if ($response) {
            $this->logDebug("User {$userId} assigned to group: {$groupName}");
        } else {
            $this->logError("Failed to assign user {$userId} to group: {$groupName}");
        }
    }
    
    private function getGroupForProduct($productId)
    {
        $mappings = $this->getProductGroupMappings();
        return isset($mappings[$productId]) ? $mappings[$productId] : null;
    }
    
    private function getProductGroupMappings()
    {
        $mappingString = $this->getConfig('product_mapping.mapping', '');
        $mappings = array();
        
        $lines = explode("\n", $mappingString);
        foreach ($lines as $lineNumber => $line) {
            $line = trim($line);
            if (empty($line) || strpos($line, '#') === 0) {
                continue;
            }
            
            if (strpos($line, '=') !== false) {
                list($productId, $groupName) = explode('=', $line, 2);
                $productId = trim($productId);
                $groupName = trim($groupName);
                
                if (!is_numeric($productId)) {
                    $this->logError("Invalid product mapping on line " . ($lineNumber + 1) . ": Product ID must be numeric. Found: '$productId'");
                    continue;
                }
                
                if (empty($groupName)) {
                    $this->logError("Invalid product mapping on line " . ($lineNumber + 1) . ": Group name cannot be empty. Found: '$line'");
                    continue;
                }
                
                $mappings[$productId] = $groupName;
            } else {
                $this->logError("Malformed product mapping on line " . ($lineNumber + 1) . ": Expected format 'product_id=group_name'. Found: '$line'");
            }
        }
        
        return $mappings;
    }
    
    private function userHasOtherAccessToGroup($user, $groupName)
    {
        $mappings = $this->getProductGroupMappings();
        $productsInGroup = array_keys($mappings, $groupName);
        
        foreach ($user->getActiveAccessRecords() as $access) {
            if (in_array($access->product_id, $productsInGroup)) {
                return true;
            }
        }
        
        return false;
    }
    
    private function determineUserActiveStatus($user)
    {
        return $user->is_approved && !$user->is_locked;
    }
    
    private function determineUserGroup($user)
    {
        if ($user->is_locked) {
            $lockedGroup = $this->getConfig('locked_group', '');
            if (!empty($lockedGroup)) {
                return $lockedGroup;
            }
        }
        
        if (!$user->is_approved) {
            $bannedGroup = $this->getConfig('banned_group', '');
            if (!empty($bannedGroup)) {
                return $bannedGroup;
            }
        }
        
        return $this->getConfig('default_group', 'user');
    }
    
    private function updateUserGroups($user)
    {
        $newGroup = $this->determineUserGroup($user);
        if ($newGroup) {
            $this->removeUserFromStatusGroups($user->user_id);
            $this->assignUserToGroupByAmemberId($user->user_id, $newGroup);
        }
    }
    
    private function removeUserFromStatusGroups($amemberUserId)
    {
        $statusGroups = array(
            $this->getConfig('default_group', 'user'),
            $this->getConfig('locked_group', ''),
            $this->getConfig('banned_group', '')
        );
        
        foreach ($statusGroups as $group) {
            if (!empty($group)) {
                $this->removeUserFromGroupByAmemberId($amemberUserId, $group);
            }
        }
    }
    
    private function detectPasswordFormat($passwordHash)
    {
        if (empty($passwordHash)) {
            return 'plain';
        }
        
        // Detect aMember/WordPress phpass format (most common in aMember)
        if (substr($passwordHash, 0, 3) === '$P$' || substr($passwordHash, 0, 3) === '$H$') {
            return 'phpass';
        }
        
        // Detect PHP password_hash() bcrypt format
        if (substr($passwordHash, 0, 4) === '$2a$' || substr($passwordHash, 0, 4) === '$2b$' || 
            substr($passwordHash, 0, 4) === '$2x$' || substr($passwordHash, 0, 4) === '$2y$') {
            return 'bcrypt';
        }
        
        // Detect argon2i format (newer PHP password_hash)
        if (substr($passwordHash, 0, 9) === '$argon2i$') {
            return 'argon2i';
        }
        
        // Detect argon2id format (newest PHP password_hash)
        if (substr($passwordHash, 0, 10) === '$argon2id$') {
            return 'argon2id';
        }
        
        // Detect Unix MD5 crypt format
        if (substr($passwordHash, 0, 3) === '$1$') {
            return 'crypt';
        }
        
        // Detect simple MD5 hash (32 hex characters)
        if (strlen($passwordHash) === 32 && ctype_xdigit($passwordHash)) {
            return 'md5';
        }
        
        // Detect simple SHA1 hash (40 hex characters)
        if (strlen($passwordHash) === 40 && ctype_xdigit($passwordHash)) {
            return 'sha1';
        }
        
        // Default to phpass for aMember (most likely format)
        return 'phpass';
    }
    
    private function logDebug($message)
    {
        try {
            if ($this->getConfig('debug_mode')) {
                Am_Di::getInstance()->logger->debug("[IncarcerationBot] " . $message);
            }
        } catch (Exception $e) {
            // Silently continue if logging fails
        }
    }
    
    private function logError($message)
    {
        try {
            Am_Di::getInstance()->logger->error("[IncarcerationBot] " . $message);
        } catch (Exception $e) {
            // Silently continue if logging fails
        }
    }
}
