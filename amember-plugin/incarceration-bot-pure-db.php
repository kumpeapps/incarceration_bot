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
        'username','email','password','is_active','amember_user_id','password_format','first_name','last_name','groups'
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
    
    function init()
    {
        parent::init();
        
        // Only add hooks for user management - no API sync
        $this->getDi()->hook->add(Am_Event::ACCESS_AFTER_INSERT, array($this, 'onAccessInsert'));
        $this->getDi()->hook->add(Am_Event::ACCESS_AFTER_DELETE, array($this, 'onAccessDelete'));
    }
    
    // Database connection and table management (same as before)
    function getDb()
    {
        static $db;
        if (!$db) {
            $host = $this->getConfig('db_host');
            $name = $this->getConfig('db_name');
            $user = $this->getConfig('db_user');
            $pass = $this->getConfig('db_pass');
            
            try {
                $dsn = "mysql:host=$host;dbname=$name;charset=utf8";
                $db = new PDO($dsn, $user, $pass, array(
                    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
                ));
            } catch (PDOException $e) {
                throw new Exception("Database connection failed: " . $e->getMessage());
            }
        }
        return $db;
    }
    
    function getTableName()
    {
        return $this->getConfig('db_table', 'incarceration_bot_users');
    }
    
    function createTable()
    {
        $table = $this->getTableName();
        $db = $this->getDb();
        
        $sql = "CREATE TABLE IF NOT EXISTS `$table` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `login` varchar(255) NOT NULL,
            `email` varchar(255) NOT NULL,
            `pass` varchar(255) NOT NULL,
            `first_name` varchar(255) DEFAULT NULL,
            `last_name` varchar(255) DEFAULT NULL,
            `is_active` tinyint(1) DEFAULT 1,
            `groups` text,
            `session_id` varchar(255) DEFAULT NULL,
            `session_expires` datetime DEFAULT NULL,
            `last_login` datetime DEFAULT NULL,
            `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
            `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`),
            UNIQUE KEY `login` (`login`),
            KEY `email` (`email`),
            KEY `session_id` (`session_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8";
        
        $db->exec($sql);
        $this->debugLog("Table $table created/verified");
    }
    
    // Core protect plugin methods (no API sync)
    function addUser(User $user, $password)
    {
        $db = $this->getDb();
        $table = $this->getTableName();
        
        $groups = $this->getUserGroups($user);
        
        $sql = "INSERT INTO `$table` (login, email, pass, first_name, last_name, is_active, groups) 
                VALUES (?, ?, ?, ?, ?, ?, ?)";
        
        $stmt = $db->prepare($sql);
        $stmt->execute(array(
            $user->login,
            $user->email,
            $password,
            $user->name_f ?: '',
            $user->name_l ?: '',
            1,
            json_encode($groups)
        ));
        
        $this->debugLog("User {$user->login} added to protect table");
    }
    
    function changePass(User $user, $password)
    {
        $db = $this->getDb();
        $table = $this->getTableName();
        
        $sql = "UPDATE `$table` SET pass = ?, updated_at = NOW() WHERE login = ?";
        $stmt = $db->prepare($sql);
        $stmt->execute(array($password, $user->login));
        
        $this->debugLog("Password changed for user {$user->login}");
    }
    
    function changeEmail(User $user, $oldEmail)
    {
        $db = $this->getDb();
        $table = $this->getTableName();
        
        $sql = "UPDATE `$table` SET email = ?, updated_at = NOW() WHERE login = ?";
        $stmt = $db->prepare($sql);
        $stmt->execute(array($user->email, $user->login));
        
        $this->debugLog("Email changed for user {$user->login}");
    }
    
    function removeUser(User $user)
    {
        $db = $this->getDb();
        $table = $this->getTableName();
        
        $sql = "DELETE FROM `$table` WHERE login = ?";
        $stmt = $db->prepare($sql);
        $stmt->execute(array($user->login));
        
        $this->debugLog("User {$user->login} removed from protect table");
    }
    
    // Session management
    function loginUser($login, $password, $ipAddress = null)
    {
        $db = $this->getDb();
        $table = $this->getTableName();
        
        $sql = "SELECT * FROM `$table` WHERE login = ? AND pass = ? AND is_active = 1";
        $stmt = $db->prepare($sql);
        $stmt->execute(array($login, $password));
        $user = $stmt->fetch();
        
        if (!$user) {
            return false;
        }
        
        if ($this->getConfig('single_session') && $user['session_id']) {
            $this->logoutUser($user['session_id']);
        }
        
        $sessionId = md5(uniqid() . $login . time());
        $timeout = $this->getConfig('session_timeout', 60);
        $expires = date('Y-m-d H:i:s', time() + ($timeout * 60));
        
        $sql = "UPDATE `$table` SET session_id = ?, session_expires = ?, last_login = NOW() WHERE login = ?";
        $stmt = $db->prepare($sql);
        $stmt->execute(array($sessionId, $expires, $login));
        
        $this->debugLog("User {$login} logged in with session {$sessionId}");
        
        return $sessionId;
    }
    
    function validateSession($sessionId)
    {
        $db = $this->getDb();
        $table = $this->getTableName();
        
        $sql = "SELECT * FROM `$table` WHERE session_id = ? AND session_expires > NOW() AND is_active = 1";
        $stmt = $db->prepare($sql);
        $stmt->execute(array($sessionId));
        $user = $stmt->fetch();
        
        if ($user) {
            $timeout = $this->getConfig('session_timeout', 60);
            $expires = date('Y-m-d H:i:s', time() + ($timeout * 60));
            
            $sql = "UPDATE `$table` SET session_expires = ? WHERE session_id = ?";
            $stmt = $db->prepare($sql);
            $stmt->execute(array($expires, $sessionId));
            
            return $user;
        }
        
        return false;
    }
    
    function logoutUser($sessionId)
    {
        $db = $this->getDb();
        $table = $this->getTableName();
        
        $sql = "UPDATE `$table` SET session_id = NULL, session_expires = NULL WHERE session_id = ?";
        $stmt = $db->prepare($sql);
        $stmt->execute(array($sessionId));
        
        $this->debugLog("Session {$sessionId} logged out");
    }
    
    // Group management
    function getUserGroups(User $user)
    {
        $groups = array();
        $groupMap = $this->getGroupMap();
        
        foreach ($user->getActiveAccess() as $access) {
            $productId = $access->product_id;
            if (isset($groupMap[$productId])) {
                $groups[] = $groupMap[$productId];
            }
        }
        
        if (empty($groups)) {
            $groups[] = 'user';
        }
        
        return array_unique($groups);
    }
    
    function onAccessInsert(Am_Event $event)
    {
        $access = $event->getAccess();
        $user = $this->getDi()->userTable->load($access->user_id);
        $this->debugLog("Access granted to user {$user->login}");
        $this->updateUserGroups($user);
    }
    
    function onAccessDelete(Am_Event $event)
    {
        $access = $event->getAccess();
        $user = $this->getDi()->userTable->load($access->user_id);
        $this->debugLog("Access removed from user {$user->login}");
        $this->updateUserGroups($user);
    }
    
    function updateUserGroups(User $user)
    {
        $db = $this->getDb();
        $table = $this->getTableName();
        
        $groups = $this->getUserGroups($user);
        
        $sql = "UPDATE `$table` SET groups = ?, updated_at = NOW() WHERE login = ?";
        $stmt = $db->prepare($sql);
        $stmt->execute(array(json_encode($groups), $user->login));
        
        $this->debugLog("Updated groups for user {$user->login}: " . implode(', ', $groups));
    }
    
    function debugLog($message)
    {
        if ($this->getConfig('debug_mode')) {
            $this->getDi()->logger->info("Incarceration Bot Pure: $message");
        }
    }
    
    function canAutoCreate()
    {
        return true;
    }
    
    function getIntegrationFormElements()
    {
        return array();
    }
}
