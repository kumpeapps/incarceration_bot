<?php
/**
 * Incarceration-bot Integration Plugin
 * Checklist (mark tested items with x):
 * [x] - template generated
 * [ ] - go to aMember Cp -> Setup -> Plugins and enable this plugin
 * [ ] - test user creation
 *       try to create user in aMember and add access manually.
 *       Login to Incarceration-bot and check that
 *       that corresponding user appeared in users list and all necessary
 *       fields transferred
 * [ ] - test password generation: login to incarceration-bot as the new user
 * [ ] - update user record in amember and try to login and view profile in the script
 * [ ] - implement single-login
 *
 **/
class Am_Protect_IncarcerationBot extends Am_Protect_Databased
{
    const PLUGIN_DATE = '$Date$';
    const PLUGIN_REVISION = '@@VERSION@@';

    protected $guessTablePattern = "users";
    protected $guessFieldsPattern = [
        'username','email','hashed_password','is_active','amember_user_id','password_format',    ];
    protected $groupMode = Am_Protect_Databased::GROUP_MULTI;

    public function afterAddConfigItems($form)
    {
        parent::afterAddConfigItems($form);
        // additional configuration items for the plugin may be inserted here
    }

    public function getPasswordFormat()
    {
        return SavedPassTable::PASSWORD_PHPASS;
    }

    public function createTable()
    {
        $table = new Am_Protect_Table($this, $this->getDb(), '?_users', 'id');
        $table->setFieldsMapping([
            [Am_Protect_Table::FIELD_LOGIN, 'username'],
            [Am_Protect_Table::FIELD_EMAIL, 'email'],
            [Am_Protect_Table::FIELD_PASS, 'hashed_password'],
            [':1', 'is_active'],
            [Am_Protect_Table::FIELD_ID, 'amember_user_id'],
            [':phpass', 'password_format'],
        ]);
        
        $table->setGroupsTableConfig([
            Am_Protect_Table::GROUP_TABLE => '?_user_groups',
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
            NULL as is_banned, #must be customized
            NULL as is_admin # must be customized
            FROM ?_groups";
    }

    public function createSessionTable()
    {
        $table = new Am_Protect_SessionTable(
            $this, $this->getDb(),
            '?_sessions', 'id');
        $table->setTableConfig([
                Am_Protect_SessionTable::FIELD_SID => 'id',
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
        //return name of cookie that used for sessions
    }

    function getReadme()
    {
        return <<<CUT
    incarceration-bot README

CUT;
    }
}