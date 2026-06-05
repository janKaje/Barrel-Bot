import os
import json
from typing import Literal
from colorama import Fore

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

    BB_CHANNEL_IDS = [
        1297596333976453291,
        1364450362421022750,
        735631714558148701
    ]

    CHATBOT_CHANNEL_ID = 1487874411942903829

    BARREL_CULT_GUILD_ID = 1296983356541501440

    KEN_USER_ID = 105721759373787136

    with open(dir_path + "/data/guild_config.json") as file:
        GUILD_CONFIG = json.load(file)

    @staticmethod
    def write_guild_config_raw(new):
        BBGLOBALS.GUILD_CONFIG = new
    
    @staticmethod
    def save_guild_config():
        with open(dir_path + "/data/guild_config.json", "w") as file:
            json.dump(BBGLOBALS.GUILD_CONFIG, file)

    @staticmethod
    def reload_guild_config():
        with open(dir_path + "/data/guild_config.json") as file:
            BBGLOBALS.GUILD_CONFIG = json.load(file)

    @staticmethod
    def change_toggled_option(guildid:str, option:Literal["gambling", "robbing"], new:bool):

        assert guildid in BBGLOBALS.GUILD_CONFIG.keys(), f"{guildid} not in config keys"
        assert option in ["gambling", "robbing"]
        assert isinstance(new, bool)

        BBGLOBALS.GUILD_CONFIG[guildid][option] = new

    @staticmethod
    def remove_bb_channel(guildid:str, channel_id:int):

        assert guildid in BBGLOBALS.GUILD_CONFIG.keys(), f"{guildid} not in config keys"
        assert channel_id in BBGLOBALS.GUILD_CONFIG[guildid]["channel_ids"]

        BBGLOBALS.GUILD_CONFIG[guildid]["channel_ids"].remove(channel_id)

    @staticmethod
    def add_bb_channel(guildid:str, channel_id:int):

        assert guildid in BBGLOBALS.GUILD_CONFIG.keys(), f"{guildid} not in config keys"
        assert isinstance(channel_id, int)
        assert channel_id not in BBGLOBALS.GUILD_CONFIG[guildid]["channel_ids"]

        BBGLOBALS.GUILD_CONFIG[guildid]["channel_ids"].append(channel_id)

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
            
            cls.CHATBOT_CHANNEL_ID = 1487504431829356554 # test server chatbot channel

            cls.BARREL_CULT_GUILD_ID = 733508144185081939

    @classmethod
    def hide_command_from_help(cls, command_name):
        """Hides a command from the help command."""
        cls.HIDE_FROM_HELP[command_name] = True
        print(f"Command '{command_name}' is now hidden from help.")
