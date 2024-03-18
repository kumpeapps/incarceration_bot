"""Incarceration Bot"""

import setup  # pylint: disable=unused-import, wrong-import-order
import pymysql
from kumpeapi import KAPI
from params import Params

kumpeapi = KAPI(
    Params.KumpeApps.api_key, mysql_creds=Params.SQL.dict(), preprod=Params.preprod
)


def get_incarcerated_users():
    """Get list of incarcerated users"""
    database = mysql_connect()
    cursor = database.cursor(pymysql.cursors.DictCursor)
    sql = "SELECT * FROM BOT_Data.vw_incarcerationbot__incarcerated_users;"
    cursor.execute(sql)
    users = cursor.fetchall()
    cursor.close()
    database.close()
    get_incarcerated_user_access(users)


def get_incarcerated_user_access(users: dict):
    """Get the incarcerated users access to systems requiring revocation"""
    for user in users:
        user_id = user["user_id"]
        database = mysql_connect()
        cursor = database.cursor(pymysql.cursors.DictCursor)
        sql = "SELECT * FROM BOT_Data.vw_incarcerationbot__revoke_access WHERE user_id = %s;"
        cursor.execute(sql, user_id)
        revoke_list = cursor.fetchall()
        cursor.close()
        database.close()
        revoke_access(user, revoke_list)


def build_access_restore(revoke_list: dict):
    """Backup User Access for Restore Later"""
    for access in revoke_list:
        database = mysql_connect()
        cursor = database.cursor(pymysql.cursors.DictCursor)
        sql = """INSERT INTO `BOT_Data`.`incarcerationbot__access_backup`
                    (
                        `user_id`,
                        `product_id`,
                        `expire_date`
                    )
                VALUES
                    (
                        %s,
                        %s,
                        %s
                        );
            """
        cursor.execute(
            sql,
            (
                access["user_id"],
                access["product_id"],
                access["expire_date"],
            ),
        )
        database.commit()
        cursor.close()


def revoke_access(user: dict, revoke_list: dict):
    """Revoke Access to Incarcerated user and Lock Account"""
    user_id = user["user_id"]
    for access in revoke_list:
        kumpeapi.expire_access(
            user_id, access["product_id"], "Revoked due to incarceration"
        )
    kumpeapi.update_user_comment(
        user_id, comment=f"User Locked by Incarceration Bot: {user['comment']}"
    )
    kumpeapi.update_user_field(user_id, "is_locked", "1")
    build_access_restore(revoke_list)


def get_restore_list():
    """Get Restore List"""
    database = mysql_connect()
    cursor = database.cursor(pymysql.cursors.DictCursor)
    sql = "SELECT * FROM BOT_Data.vw_incarcerationbot__pending_restore;"
    cursor.execute(sql)
    restore_list = cursor.fetchall()
    cursor.close()
    database.close()
    restore_access(restore_list)


def restore_access(restore_list: dict):
    """Restore User's Access"""
    for restore in restore_list:
        user_id = restore["user_id"]
        product_id = restore["product_id"]
        expire = restore["expire_date"]
        release = restore["release_date"]
        kumpeapi.add_access(
            user_id=user_id,
            product_id=product_id,
            expire_date=expire,
            comment=f"Added via incarceration_bot due to release on {release}",
        )
        kumpeapi.update_user_comment(user_id, comment="")
        kumpeapi.update_user_field(user_id, "is_locked", "0")


def mysql_connect():
    """Connect to MySQL"""
    database = pymysql.connect(
        db=Params.SQL.database,
        user=Params.SQL.username,
        passwd=Params.SQL.password,
        host=Params.SQL.server,
        port=3306,
    )
    return database


if __name__ == "__main__":
    get_incarcerated_users()
    get_restore_list()
