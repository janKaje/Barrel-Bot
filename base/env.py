import os
from colorama import Fore


class BBGLOBALS:
    HIDE_FROM_HELP: dict = {}
    IS_IN_DEV_MODE: bool = False
    DATA_CHANNEL_ID: int = 735631640939986964
    BARREL_REP_ROLE_ID: int = 1296985456105230412  # ID for the Barrel Rep role

    # easily configurable reminder and deadline times
    REMINDER_TIME: list[int] = [16, 30]  # 16:30 UTC
    DEADLINE_TIME: list[int] = [4, 00]  # 04:00 UTC

    BARREL_NEWS_CHANNEL_ID: int = 1297025420184518708
    BARREL_SUB_ROLE_ID: int = 1297023311556907028
    BB_DEV_ROLE_ID: int = 1303765973324533781

    BARREL_REP_MENTION: str = f"<@&{BARREL_REP_ROLE_ID}>"
    BARREL_SUB_MENTION: str = f"<@&{BARREL_SUB_ROLE_ID}>"

    # Get the news key and the API endpoint
    NEWS_KEY: str = "-1"
    NEWS_ENDPOINT: str = "-1"

    @classmethod
    def init_globals(cls):
        try:
            import dotenv
            if dotenv.load_dotenv():
                print("Loaded environment variables from .env file")
            else:
                raise ImportError(Fore.RED, "dotenv.load_dotenv() returned False")
        except ImportError as e:
            print(e.msg)
            pass

        cls.IS_IN_DEV_MODE = os.environ.get("IS_IN_DEV_MODE", "false")

        cls.NEWS_KEY: str = os.environ["NEWS_KEY"]
        cls.NEWS_ENDPOINT: str = os.environ["NEWS_ENDPOINT"]

        if isinstance(cls.IS_IN_DEV_MODE, str):
            cls.IS_IN_DEV_MODE: bool = cls.IS_IN_DEV_MODE.lower() == "true"

        if cls.IS_IN_DEV_MODE:
            # channel ID for #general in bot testing server
            cls.DATA_CHANNEL_ID: int = 733508144617226302

            cls.BARREL_NEWS_CHANNEL_ID: int = 733508144617226302  # general
            cls.BARREL_REP_ROLE_ID: int = 735700976010264667  # join test role
            cls.BARREL_SUB_ROLE_ID: int = 735700976010264667  # join test role
            cls.BB_DEV_ROLE_ID: int = 735700976010264667  # join test role

            # Modifying the mention role
            cls.BARREL_REP_MENTION: str = f"<@&{cls.BARREL_REP_ROLE_ID}>"
            cls.BARREL_SUB_MENTION: str = f"<@&{cls.BARREL_SUB_ROLE_ID}>"

    @classmethod
    def hide_command_from_help(cls, command_name):
        """Hides a command from the help command."""
        cls.HIDE_FROM_HELP[command_name] = True
        print(f"Command '{command_name}' is now hidden from help.")
