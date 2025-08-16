<?php
/**
 * Incarceration Bot Integration Plugin
 * Checklist (mark tested items with x):
 * [x] - template generated
 * [ ] - go to aMember Cp -> Setup -> Plugins and enable this plugin
 * [ ] - test user creation
 *       try to create user in aMember and add access manually.
 *       Login to Incarceration Bot and check that
 *       that corresponding user appeared in users list and all necessary
 *       fields transferred
 * [ ] - test password generation: login to incarceration-bot as the new user
 * [ ] - update user record in amember and try to login and view profile in the script
 * [ ] - implement single-login
 *
 * @table integration
 * @id incarceration_bot
 * @title Incarceration Bot
 * @visible_link https://github.com/kumpeapps/incarceration_bot
 * @description Database integration for Incarceration Bot user authentication
 * @different_groups 1
 * @single_login 1
 * @am_protect_api 6.0
 **/
class Am_Protect_IncarcerationBot extends Am_Protect_Databased
{
    const PLUGIN_DATE = '$Date$';
    const PLUGIN_REVISION = '6.3.19';

    protected $guessTablePattern = "incarceration_bot_users";
    protected $guessFieldsPattern = [
        'username','email','password','is_active','amember_user_id','password_format','first_name','last_name'
    ];
    protected $groupMode = Am_Protect_Databased::GROUP_MULTI;

    public function afterAddConfigItems($form)
    {
        parent::afterAddConfigItems($form);
        
        // Add API sync configuration (optional)
        $form->addText('api_base_url', array('class' => 'am-el-wide'))
            ->setLabel('API Base URL (optional sync)')
            ->setValue('https://your-domain.com/api');
            
        $form->addText('api_key', array('class' => 'am-el-wide'))
            ->setLabel('API Key (optional sync)');
            
        $form->addAdvCheckbox('enable_api_sync')
            ->setLabel('Enable API Sync')
            ->setValue(0);
            
        $form->addAdvCheckbox('debug_mode')
            ->setLabel('Debug Mode')
            ->setValue(0);
    }

    public function getPasswordFormat()
    {
        return SavedPassTable::PASSWORD_PHPASS;
    }

    public function createTable()
    {
        $table = new Am_Protect_Table($this, $this->getDb(), '?_incarceration_bot_users', 'id');
        $table->setFieldsMapping([
            [Am_Protect_Table::FIELD_LOGIN, 'username'],
            [Am_Protect_Table::FIELD_EMAIL, 'email'],
            [Am_Protect_Table::FIELD_PASS, 'password'],
            [':1', 'is_active'],
            [Am_Protect_Table::FIELD_ID, 'amember_user_id'],
            [':phpass', 'password_format'],
            [Am_Protect_Table::FIELD_NAME_F, 'first_name'],
            [Am_Protect_Table::FIELD_NAME_L, 'last_name'],
        ]);
        
        $table->setGroupsTableConfig([
            Am_Protect_Table::GROUP_TABLE => '?_incarceration_bot_user_groups',
            Am_Protect_Table::GROUP_GID => 'group_id',
            Am_Protect_Table::GROUP_UID => 'user_id',
        ]);
        
        return $table;
    }

    public function getAvailableUserGroupsSql()
    {
        return "SELECT
            id as id,
            name as title,
            CASE WHEN name IN ('banned', 'locked') THEN 1 ELSE 0 END as is_banned,
            CASE WHEN name IN ('admin', 'administrator') THEN 1 ELSE 0 END as is_admin
            FROM ?_incarceration_bot_groups";
    }

    public function createSessionTable()
    {
        $table = new Am_Protect_SessionTable(
            $this, $this->getDb(),
            '?_incarceration_bot_sessions', 'id');
        $table->setTableConfig([
                Am_Protect_SessionTable::FIELD_SID => 'session_id',
                Am_Protect_SessionTable::FIELD_UID => 'user_id',
                Am_Protect_SessionTable::FIELD_SID => 'session_token',
                Am_Protect_SessionTable::FIELD_IP => 'ip_address',
                Am_Protect_SessionTable::FIELD_UA => 'user_agent',
                Am_Protect_SessionTable::FIELD_CREATED => 'created_at',
                Am_Protect_SessionTable::FIELD_CHANGED => 'updated_at',
                Am_Protect_SessionTable::SESSION_COOKIE => $this->getSessionCookieName(),
            ]
        );
        return $table;
    }

    function getSessionCookieName()
    {
        return 'incarceration_bot_session';
    }

    public function init()
    {
        parent::init();
        
        // Add hooks for API sync if enabled
        if ($this->getConfig('enable_api_sync') && $this->isApiConfigured()) {
            $this->getDi()->hook->add(Am_Event::USER_AFTER_INSERT, array($this, 'onUserInsert'));
            $this->getDi()->hook->add(Am_Event::USER_AFTER_UPDATE, array($this, 'onUserUpdate'));
            $this->getDi()->hook->add(Am_Event::USER_AFTER_DELETE, array($this, 'onUserDelete'));
            $this->getDi()->hook->add(Am_Event::ACCESS_AFTER_INSERT, array($this, 'onAccessInsert'));
            $this->getDi()->hook->add(Am_Event::ACCESS_AFTER_DELETE, array($this, 'onAccessDelete'));
        }
    }
    
    function isApiConfigured()
    {
        return strlen($this->getConfig('api_base_url')) > 0 && strlen($this->getConfig('api_key')) > 0;
    }

    // Optional API sync event handlers
    function onUserInsert(Am_Event $event)
    {
        if (!$this->getConfig('enable_api_sync')) return;
        
        $user = $event->getUser();
        $this->debugLog("User Insert: {$user->login}");
        $this->syncUserToApi($user, 'create');
    }
    
    function onUserUpdate(Am_Event $event)
    {
        if (!$this->getConfig('enable_api_sync')) return;
        
        $user = $event->getUser();
        $this->debugLog("User Update: {$user->login}");
        $this->syncUserToApi($user, 'update');
    }
    
    function onUserDelete(Am_Event $event)
    {
        if (!$this->getConfig('enable_api_sync')) return;
        
        $user = $event->getUser();
        $this->debugLog("User Delete: {$user->login}");
        $this->makeApiCall('DELETE', "users/{$user->login}");
    }
    
    function onAccessInsert(Am_Event $event)
    {
        if (!$this->getConfig('enable_api_sync')) return;
        
        $access = $event->getAccess();
        $user = $this->getDi()->userTable->load($access->user_id);
        $this->debugLog("Access granted to user {$user->login}");
        $this->syncUserToApi($user, 'update');
    }
    
    function onAccessDelete(Am_Event $event)
    {
        if (!$this->getConfig('enable_api_sync')) return;
        
        $access = $event->getAccess();
        $user = $this->getDi()->userTable->load($access->user_id);
        $this->debugLog("Access removed from user {$user->login}");
        $this->syncUserToApi($user, 'update');
    }
    
    // API sync methods (optional functionality)
    function syncUserToApi($user, $action = 'update')
    {
        try {
            // Get user's active products for group mapping
            $activeProducts = array();
            foreach ($user->getActiveAccess() as $access) {
                $activeProducts[] = $access->product_id;
            }
            
            $userData = array(
                'username' => $user->login,
                'email' => $user->email,
                'first_name' => $user->name_f ?: '',
                'last_name' => $user->name_l ?: '',
                'is_active' => $user->is_active,
                'amember_user_id' => $user->user_id,
                'groups' => $this->mapProductsToGroups($activeProducts)
            );
            
            $this->debugLog("Syncing user to API: " . json_encode($userData));
            
            if ($action === 'create') {
                $response = $this->makeApiCall('POST', 'users', $userData);
            } else {
                $response = $this->makeApiCall('PUT', "users/{$user->login}", $userData);
            }
            
            $this->debugLog("API sync response: " . json_encode($response));
            
        } catch (Exception $e) {
            $this->debugLog("Error syncing user {$user->login} to API: " . $e->getMessage());
        }
    }
    
    function mapProductsToGroups($productIds)
    {
        // Map aMember product IDs to Incarceration Bot groups
        $groupMapping = array(
            // Example: 1 => 'premium', 2 => 'admin'
            // Configure this based on your aMember products
        );
        
        $groups = array();
        foreach ($productIds as $productId) {
            if (isset($groupMapping[$productId])) {
                $groups[] = $groupMapping[$productId];
            }
        }
        
        // Default group if no specific mapping
        if (empty($groups)) {
            $groups[] = 'user';
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

    function getReadme()
    {
        return <<<CUT
    Incarceration Bot Integration README

    This plugin integrates aMember with Incarceration Bot system.

    Setup:
    1. Configure database connection in plugin settings
    2. Set table prefix if needed
    3. Optionally enable API sync for real-time updates
    4. Test user creation and login

    Tables created:
    - {prefix}_incarceration_bot_users (user credentials)
    - {prefix}_incarceration_bot_user_groups (group memberships)  
    - {prefix}_incarceration_bot_sessions (session management)
    - {prefix}_incarceration_bot_groups (available groups)

    The plugin will automatically sync aMember users to the database
    and optionally to the Incarceration Bot API if configured.

CUT;
    }
}
