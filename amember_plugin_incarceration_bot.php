<?php
/**
 * aMember Plugin for Incarceration Bot User Management
 * 
 * This plugin synchronizes aMember user accounts and groups with the Incarceration Bot system.
 * It handles user creation, updates, and group assignments based on aMember product subscriptions.
 * 
 * @package aMember_Plugin_IncarcerationBot
 * @version 1.0.0
 */

class Am_Plugin_IncarcerationBot extends Am_Plugin
{
    const PLUGIN_STATUS = self::STATUS_PRODUCTION;
    const PLUGIN_COMM = self::COMM_FREE;
    const PLUGIN_REVISION = '1.0.0';
    
    protected $_configPrefix = 'misc.';
    
    // API configuration
    private $api_base_url;
    private $api_key;
    private $timeout = 30;
    
    public function init()
    {
        parent::init();
        
        // Get configuration
        $this->api_base_url = rtrim($this->getConfig('api_base_url', ''), '/');
        $this->api_key = $this->getConfig('api_key', '');
        
        // Hook into aMember events
        $this->getDi()->hook->add(Am_Event::USER_AFTER_INSERT, [$this, 'onUserInsert']);
        $this->getDi()->hook->add(Am_Event::USER_AFTER_UPDATE, [$this, 'onUserUpdate']);
        $this->getDi()->hook->add(Am_Event::USER_AFTER_DELETE, [$this, 'onUserDelete']);
        $this->getDi()->hook->add(Am_Event::ACCESS_AFTER_INSERT, [$this, 'onAccessInsert']);
        $this->getDi()->hook->add(Am_Event::ACCESS_AFTER_DELETE, [$this, 'onAccessDelete']);
    }
    
    public function getTitle()
    {
        return "Incarceration Bot Integration";
    }
    
    public function getDescription()
    {
        return "Synchronizes aMember users and subscriptions with Incarceration Bot user management system";
    }
    
    public function _initSetupForm(Am_Form_Setup $form)
    {
        $form->addText('api_base_url', array('class' => 'am-el-wide'))
            ->setLabel('API Base URL')
            ->addRule('required')
            ->addRule('regex', 'Please enter a valid URL', '/^https?:\/\/.+/')
            ->setValue('https://your-domain.com/api');
            
        $form->addText('api_key', array('class' => 'am-el-wide'))
            ->setLabel('API Key')
            ->addRule('required');
            
        $form->addSelect('default_group')
            ->setLabel('Default Group for New Users')
            ->loadOptions([
                'user' => 'Regular User',
                'admin' => 'Administrator',
                'moderator' => 'Moderator'
            ])
            ->setValue('user');
            
        $form->addAdvCheckbox('debug_mode')
            ->setLabel('Debug Mode')
            ->addRule('required');
            
        $group = $form->addGroup('product_mapping')
            ->setLabel('Product to Group Mapping');
            
        $group->addStatic()
            ->setContent('<div class="am-info">Map aMember products to Incarceration Bot groups. Format: product_id=group_name (one per line)</div>');
            
        $group->addTextarea('mapping', array('class' => 'am-el-wide', 'rows' => 10))
            ->setLabel('Product Mappings')
            ->setValue("# Example mappings:\n# 1=user\n# 2=admin\n# 3=moderator");
    }
    
    /**
     * Handle user creation
     */
    public function onUserInsert(Am_Event $event)
    {
        $user = $event->getUser();
        $this->logDebug("User created: " . $user->login);
        
        // Create user in Incarceration Bot
        $userData = [
            'username' => $user->login,
            'email' => $user->email,
            'password' => $this->generateRandomPassword(),
            'amember_user_id' => $user->user_id,
            'is_active' => true
        ];
        
        $response = $this->apiRequest('POST', '/users/amember', $userData);
        
        if ($response && isset($response['id'])) {
            $this->logDebug("User created successfully in Incarceration Bot: " . $response['id']);
            
            // Assign default group
            $defaultGroup = $this->getConfig('default_group', 'user');
            $this->assignUserToGroup($response['id'], $defaultGroup);
        } else {
            $this->logError("Failed to create user in Incarceration Bot for: " . $user->login);
        }
    }
    
    /**
     * Handle user updates
     */
    public function onUserUpdate(Am_Event $event)
    {
        $user = $event->getUser();
        $this->logDebug("User updated: " . $user->login);
        
        // Update user in Incarceration Bot
        $userData = [
            'username' => $user->login,
            'email' => $user->email,
            'is_active' => $user->is_approved && !$user->is_locked
        ];
        
        $response = $this->apiRequest('PUT', '/users/amember/' . $user->user_id, $userData);
        
        if (!$response) {
            $this->logError("Failed to update user in Incarceration Bot for: " . $user->login);
        }
    }
    
    /**
     * Handle user deletion
     */
    public function onUserDelete(Am_Event $event)
    {
        $user = $event->getUser();
        $this->logDebug("User deleted: " . $user->login);
        
        // Deactivate user in Incarceration Bot
        $response = $this->apiRequest('DELETE', '/users/amember/' . $user->user_id);
        
        if (!$response) {
            $this->logError("Failed to delete user in Incarceration Bot for: " . $user->login);
        }
    }
    
    /**
     * Handle new access (subscription)
     */
    public function onAccessInsert(Am_Event $event)
    {
        $access = $event->getAccess();
        $user = $access->getUser();
        $product = $access->getProduct();
        
        $this->logDebug("Access granted for user: " . $user->login . ", product: " . $product->title);
        
        // Get group mapping for this product
        $group = $this->getGroupForProduct($product->product_id);
        if ($group) {
            $this->assignUserToGroupByAmemberId($user->user_id, $group);
        }
    }
    
    /**
     * Handle access removal
     */
    public function onAccessDelete(Am_Event $event)
    {
        $access = $event->getAccess();
        $user = $access->getUser();
        $product = $access->getProduct();
        
        $this->logDebug("Access removed for user: " . $user->login . ", product: " . $product->title);
        
        // Remove user from group if no other active access to products in this group
        $group = $this->getGroupForProduct($product->product_id);
        if ($group && !$this->userHasOtherAccessToGroup($user, $group)) {
            $this->removeUserFromGroupByAmemberId($user->user_id, $group);
        }
    }
    
    /**
     * Make API request to Incarceration Bot
     */
    private function apiRequest($method, $endpoint, $data = null)
    {
        if (empty($this->api_base_url) || empty($this->api_key)) {
            $this->logError("API configuration missing");
            return false;
        }
        
        $url = $this->api_base_url . $endpoint;
        
        $ch = curl_init();
        curl_setopt_array($ch, [
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => $this->timeout,
            CURLOPT_CUSTOMREQUEST => $method,
            CURLOPT_HTTPHEADER => [
                'Content-Type: application/json',
                'Authorization: Bearer ' . $this->api_key,
                'User-Agent: aMember-IncarcerationBot-Plugin/1.0.0'
            ]
        ]);
        
        if ($data && in_array($method, ['POST', 'PUT', 'PATCH'])) {
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
    
    /**
     * Assign user to group by aMember user ID
     */
    private function assignUserToGroupByAmemberId($amemberUserId, $groupName)
    {
        $response = $this->apiRequest('POST', "/users/amember/{$amemberUserId}/groups", [
            'group_name' => $groupName
        ]);
        
        if ($response) {
            $this->logDebug("User {$amemberUserId} assigned to group: {$groupName}");
        } else {
            $this->logError("Failed to assign user {$amemberUserId} to group: {$groupName}");
        }
    }
    
    /**
     * Remove user from group by aMember user ID
     */
    private function removeUserFromGroupByAmemberId($amemberUserId, $groupName)
    {
        $response = $this->apiRequest('DELETE', "/users/amember/{$amemberUserId}/groups/{$groupName}");
        
        if ($response) {
            $this->logDebug("User {$amemberUserId} removed from group: {$groupName}");
        } else {
            $this->logError("Failed to remove user {$amemberUserId} from group: {$groupName}");
        }
    }
    
    /**
     * Assign user to group by internal user ID
     */
    private function assignUserToGroup($userId, $groupName)
    {
        $response = $this->apiRequest('POST', "/users/{$userId}/groups", [
            'group_name' => $groupName
        ]);
        
        if ($response) {
            $this->logDebug("User {$userId} assigned to group: {$groupName}");
        } else {
            $this->logError("Failed to assign user {$userId} to group: {$groupName}");
        }
    }
    
    /**
     * Get group mapping for product
     */
    private function getGroupForProduct($productId)
    {
        $mappings = $this->getProductGroupMappings();
        return isset($mappings[$productId]) ? $mappings[$productId] : null;
    }
    
    /**
     * Parse product group mappings from configuration
     */
    private function getProductGroupMappings()
    {
        $mappingString = $this->getConfig('product_mapping.mapping', '');
        $mappings = [];
        
        $lines = explode("\n", $mappingString);
        foreach ($lines as $line) {
            $line = trim($line);
            if (empty($line) || strpos($line, '#') === 0) {
                continue;
            }
            
            if (strpos($line, '=') !== false) {
                list($productId, $groupName) = explode('=', $line, 2);
                $mappings[trim($productId)] = trim($groupName);
            }
        }
        
        return $mappings;
    }
    
    /**
     * Check if user has other active access to products in the same group
     */
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
    
    /**
     * Generate random password for new users
     */
    private function generateRandomPassword($length = 16)
    {
        $characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*';
        return substr(str_shuffle(str_repeat($characters, ceil($length / strlen($characters)))), 0, $length);
    }
    
    /**
     * Log debug message
     */
    private function logDebug($message)
    {
        if ($this->getConfig('debug_mode')) {
            Am_Di::getInstance()->logger->debug("[IncarcerationBot] " . $message);
        }
    }
    
    /**
     * Log error message
     */
    private function logError($message)
    {
        Am_Di::getInstance()->logger->error("[IncarcerationBot] " . $message);
    }
}
