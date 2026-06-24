from os import path
import sqlite3
from discord import Guild, TextChannel


class GUILD_CONFIG:

    DIR_PATH = path.dirname(path.dirname(path.abspath(__file__))) 
    DATABASE_PATH = path.join(DIR_PATH, 'data/guild_config.db')

    @staticmethod
    def is_bb_channel(channel: TextChannel) -> bool:

        conn = sqlite3.connect(GUILD_CONFIG.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM bb_channels WHERE guild_id = {channel.guild.id} AND channel_id = {channel.id}")

        if cursor.fetchone() is None:
            ret = False
        else:
            ret = True
        
        conn.close()
        return ret
    
    @staticmethod
    def is_gambling_enabled(guild: Guild|int) -> bool:

        if isinstance(guild, int):
            guild_id = guild
        else:
            guild_id = guild.id

        conn = sqlite3.connect(GUILD_CONFIG.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(f"SELECT gambling FROM guild_config WHERE guild_id = {guild_id}")
        row:tuple = cursor.fetchone()
        
        conn.close()
        return bool(row[0])
    
    @staticmethod
    def is_robbing_enabled(guild: Guild|int) -> bool:

        if isinstance(guild, int):
            guild_id = guild
        else:
            guild_id = guild.id

        conn = sqlite3.connect(GUILD_CONFIG.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(f"SELECT robbing FROM guild_config WHERE guild_id = {guild_id}")
        row:tuple = cursor.fetchone()
        
        conn.close()
        return bool(row[0])
    
    @staticmethod
    def update_gambling(guild: Guild|int, new: bool):

        if isinstance(guild, int):
            guild_id = guild
        else:
            guild_id = guild.id

        new_int = 1 if new else 0

        conn = sqlite3.connect(GUILD_CONFIG.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(f"UPDATE guild_config SET gambling = {new_int} WHERE guild_id = {guild_id}")
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def update_robbing(guild: Guild|int, new: bool):

        if isinstance(guild, int):
            guild_id = guild
        else:
            guild_id = guild.id

        new_int = 1 if new else 0

        conn = sqlite3.connect(GUILD_CONFIG.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(f"UPDATE guild_config SET robbing = {new_int} WHERE guild_id = {guild_id}")
        
        conn.commit()
        conn.close()

    @staticmethod
    def add_bb_channel(channel: TextChannel):

        conn = sqlite3.connect(GUILD_CONFIG.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM bb_channels WHERE guild_id = {channel.guild.id} AND channel_id = {channel.id}")

        if cursor.fetchone() is not None:
            conn.close()
            raise ValueError(f"Channel {channel.name} already in bb_channels")

        cursor.execute(f"INSERT INTO bb_channels VALUES ({channel.id}, {channel.guild.id})")
        
        conn.commit()
        conn.close()

    @staticmethod
    def remove_bb_channel(channel: TextChannel):

        conn = sqlite3.connect(GUILD_CONFIG.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM bb_channels WHERE guild_id = {channel.guild.id} AND channel_id = {channel.id}")

        if cursor.fetchone() is None:
            conn.close()
            raise ValueError(f"Channel {channel.name} not in bb_channels")

        cursor.execute(f"DELETE FROM bb_channels WHERE guild_id = {channel.guild.id} AND channel_id = {channel.id}")
        
        conn.commit()
        conn.close()

    @staticmethod
    def get_server_config(guild: Guild|int) -> tuple[bool, bool, list[int]]:

        if isinstance(guild, int):
            guild_id = guild
        else:
            guild_id = guild.id

        conn = sqlite3.connect(GUILD_CONFIG.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(f"SELECT gambling, robbing FROM guild_config WHERE guild_id = {guild_id}")
        row:tuple = cursor.fetchone()
        g = bool(row[0]); r = bool(row[1])

        cursor.execute(f"SELECT channel_id FROM bb_channels WHERE guild_id = {guild_id}")
        rows:list[tuple] = cursor.fetchall()
        chs = [r[0] for r in rows]
        
        conn.close()
        return g, r, chs
    
    @staticmethod
    def add_guild(guild: Guild|int):

        if isinstance(guild, int):
            guild_id = guild
        else:
            guild_id = guild.id

        conn = sqlite3.connect(GUILD_CONFIG.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM guild_config WHERE guild_id = {guild_id};")

        if cursor.fetchone() is not None:
            conn.close()
            raise ValueError(f"Guild {guild_id} already in database")

        cursor.execute(f"INSERT INTO guild_config VALUES ({guild_id}, 0, 0);")
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def remove_guild(guild: Guild|int):

        if isinstance(guild, int):
            guild_id = guild
        else:
            guild_id = guild.id

        conn = sqlite3.connect(GUILD_CONFIG.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM guild_config WHERE guild_id = {guild_id};")

        if cursor.fetchone() is None:
            conn.close()
            raise ValueError(f"Guild {guild_id} not in database")

        cursor.execute(f"DELETE FROM bb_channels WHERE guild_id = {guild_id};")
        cursor.execute(f"DELETE FROM guild_config WHERE guild_id = {guild_id};")
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def raw_query(query:str):

        conn = sqlite3.connect(GUILD_CONFIG.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(query)

        ret = cursor.fetchall()

        conn.commit()
        conn.close()

        return ret

    @staticmethod
    def get_all_bb_channels() -> list[int]:

        conn = sqlite3.connect(GUILD_CONFIG.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT channel_id FROM bb_channels")

        ret = cursor.fetchall()

        conn.commit()
        conn.close()

        return [r[0] for r in ret] # flatten
        
    @staticmethod
    def get_bb_channels(guild: Guild|int) -> list[int]:

        if isinstance(guild, int):
            guild_id = guild
        else:
            guild_id = guild.id

        conn = sqlite3.connect(GUILD_CONFIG.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(f"SELECT channel_id FROM bb_channels WHERE guild_id = {guild_id}")

        ret = cursor.fetchall()

        conn.commit()
        conn.close()

        return [r[0] for r in ret] # flatten

    @staticmethod
    def get_all_guilds() -> list[int]:

        conn = sqlite3.connect(GUILD_CONFIG.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(f"SELECT guild_id FROM guild_config")

        ret = cursor.fetchall()

        conn.commit()
        conn.close()

        return [r[0] for r in ret] # flatten and return
