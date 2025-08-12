import os
from colorama import Fore

class _BBGLOBALS:
    IS_IN_DEV_MODE = False
    DATA_CHANNEL_ID = 735631640939986964
    PLAYER_DATA_MSG = 1363307787848912896
    BARREL_REP_ROLE_ID = 733508144617226302  # ID for the Barrel Rep role
    
    # easily configurable reminder and deadline times
    REMINDER_TIME = [16, 30] # 16:30 UTC
    DEADLINE_TIME = [4, 00] # 04:00 UTC

    BARREL_NEWS_CHANNEL_ID = 1297025420184518708
    BARREL_REP_ROLE_ID = 1296985456105230412
    BARREL_SUB_ROLE_ID = 1297023311556907028

    BARREL_REP_MENTION = f"<@&{BARREL_REP_ROLE_ID}>"
    BARREL_SUB_MENTION = f"<@&{BARREL_SUB_ROLE_ID}>"

    # Get the news key and the API endpoint
    NEWS_KEY = "-1"
    NEWS_ENDPOINT = "-1"
    
    @classmethod
    def initGlobals(cls):
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
        
        cls.NEWS_KEY = os.environ["NEWS_KEY"]
        cls.NEWS_ENDPOINT = os.environ["NEWS_ENDPOINT"]
        
        if isinstance(cls.IS_IN_DEV_MODE, str):
            cls.IS_IN_DEV_MODE = cls.IS_IN_DEV_MODE.lower() == "true"

        if cls.IS_IN_DEV_MODE:
            # channel ID for #general in bot testing server
            cls.DATA_CHANNEL_ID = 733508144617226302
            cls.PLAYER_DATA_MSG = -1 # used nowhere ?!?
            
            cls.BARREL_NEWS_CHANNEL_ID = 733508144617226302 # general
            cls.BARREL_REP_ROLE_ID = 735700976010264667 # join test role
            cls.BARREL_SUB_ROLE_ID = 735700976010264667 # join test role

            # Modifying the mention role
            cls.BARREL_REP_MENTION = f"<@&{cls.BARREL_REP_ROLE_ID}>"
            cls.BARREL_SUB_MENTION = f"<@&{cls.BARREL_SUB_ROLE_ID}>"
            
    @classmethod
    def hide_command_from_help(cls, command_name):
        """Hides a command from the help command."""
        cls.HIDE_FROM_HELP[command_name] = True
        print(f"Command '{command_name}' is now hidden from help.")