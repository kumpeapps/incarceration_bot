"""Parameters file for Kumpe3D-Python"""

import setup  # pylint: disable=unused-import, wrong-import-order
import os
from dotenv import load_dotenv
from infisical_api import infisical_api


load_dotenv()
service_token = os.getenv("SERVICE_TOKEN")
app_env = os.getenv("APP_ENV")
creds = infisical_api(
    service_token=service_token, infisical_url="https://creds.kumpeapps.com"
)


class Params:
    """Parameters"""
    preprod: bool = True if app_env == 'dev' else False

    class SQL:
        """SQL Parameters for Web_3d User"""

        username = creds.get_secret(  # pylint: disable=no-member
            secret_name="USERNAME", environment=app_env, path="/MYSQL/"
        ).secretValue
        password = creds.get_secret(  # pylint: disable=no-member
            secret_name="PASSWORD", environment=app_env, path="/MYSQL/"
        ).secretValue
        server = creds.get_secret(  # pylint: disable=no-member
            secret_name="SERVER", environment=app_env, path="/MYSQL/"
        ).secretValue
        port = creds.get_secret(  # pylint: disable=no-member
            secret_name="PORT", environment=app_env, path="/MYSQL/"
        ).secretValue
        database = "BOT_Data"

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

        api_key = creds.get_secret(  # pylint: disable=no-member
            secret_name="KUMPEAPPS", environment=app_env, path="/API/"
        ).secretValue


if __name__ == "__main__":
    print(
        """Error: This file is a module to be imported and has no functions
          to be ran directly."""
    )
