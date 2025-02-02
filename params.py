"""Parameters file for Kumpe3D-Python"""

import setup  # pylint: disable=unused-import, wrong-import-order
import configparser

config = configparser.ConfigParser()
config.read("config.ini")
mysql_config = config["mysql"]
settings_config = config["settings"]
api_config = config["api"]

app_env = settings_config["app_env"]

class Params:
    """Parameters"""

    preprod: bool = True if app_env == "dev" else False

    class SQL:
        """SQL Parameters for Web_3d User"""

        username = mysql_config["username"]
        password = mysql_config["password"]
        server = mysql_config["server"]
        port = mysql_config["port"]
        database = mysql_config["database"]

        @staticmethod
        def dict():
            """returns as dictionary"""
            return {
                "username": Params.SQL.username,
                "password": Params.SQL.password,
                "server": Params.SQL.server,
                "port": Params.SQL.port,
                "database": Params.SQL.database,
            }

    class KumpeApps:
        """KumpeApps Params"""

        api_key = api_config["kumpeapps_apikey"]

    class PushOver:
        """PushOver Params"""

        api_key = api_config["pushover_apikey"]

        group = api_config["pushover_group"]


if __name__ == "__main__":
    print(
        """Error: This file is a module to be imported and has no functions
          to be ran directly."""
    )
