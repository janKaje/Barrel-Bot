import os
import json
import sqlite3
import random
import time
from datetime import datetime as dt
from datetime import timezone as tz
from datetime import timedelta as td
from math import floor
from typing import Literal, Optional

import discord

from extra_exceptions import *
from item import Item

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DAILY_RENT = 500  # coins/house/day

# Research upgrades:
#
# Base luck up (5 upgrades)
#  \__> fishing luck up (5 upgrades)
#  \__> work luck up (5 upgrades)
#        \__> work earnings up (up to 10x more, 6 upgrades) (from wl no 2)
#  \__> robbery luck up (5 upgrades)
#
# Shop item sale price increase (up to 100%, 4 upgrades)
#  \__> Fish sale price increase (up to 10x more, 10 upgrades) (from spi no 2)
#        \__> Fishing rod limit increase (up to 10) (from fpi no 5, requires at least fl no 2 as well)
#               TO BE ADDED LATER
#              \__> Chance to catch extra (% chance to keep rolling each time, maxes out at 50%, 6 upgrades)
# 
# Rent collection time extension (up to 7 days, 6 upgrades)
#  \__> Rent multiplier (up to 2x more, 5 upgrades) (from rc no 4)

class Player:

    DATABASE_PATH = os.path.join(dir_path, "data", "player_data.db")

    with open(os.path.join(dir_path, "data", "research_config.json")) as file:
        RESEARCH_CONFIG = json.load(file)

    def __init__(self, member: discord.Member):

        self.member = member
        self.user_id = member.id
        self.guild_id = member.guild.id
        self.idstr = str(member.guild.id) + "_" + str(member.id)
        
        conn = sqlite3.connect(Player.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM player_data "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")

        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO player_data (user_id, guild_id) " \
                f"VALUES ({self.user_id}, {self.guild_id})")
            conn.commit()

        conn.close()

    @property
    def balance(self):

        ret = db_query(f"SELECT balance FROM player_data "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")

        return ret[0][0]
    
    @property
    def nhouses(self):
        """number of houses that the player has bought"""

        ret = db_query(f"SELECT n_houses FROM player_data "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")

        return ret[0][0]

    @property
    def bank_balance(self):
        """get player's bank balance"""

        ret = db_query(f"SELECT bank_bal FROM player_data "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")

        return ret[0][0]

    @property
    def whole_balance(self):
        """gets player's whole balance, bank included"""

        ret = db_query(f"SELECT balance, bank_bal FROM player_data "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")
        
        return sum(ret[0])
    
    @staticmethod
    def get_guild_balances(guild_id) -> list[tuple[int, int, int]]:

        ret = db_query(f"SELECT user_id, balance + bank_bal, bank_bal FROM "\
            f"player_data WHERE guild_id = {guild_id} "\
            "ORDER BY balance + bank_bal DESC")
        
        return ret

    def give_coins(self, nocoins: int):
        """gives or takes coins from the player"""

        if nocoins < 0:
            self.take_coins(-nocoins, True)
            return
        if nocoins == 0:
            return

        db_query(f"UPDATE player_data SET balance = balance + {nocoins} "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")

    def take_coins(self, nocoins: int, include_bank=False):
        """take coins from the player"""

        conn = sqlite3.connect(Player.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT balance, bank_bal FROM player_data WHERE " \
            f"guild_id = {self.guild_id} AND user_id = {self.user_id}")

        ret = cursor.fetchone()

        if include_bank:
            cur_bal = ret[0] + ret[1]
        else:
            cur_bal = ret[0]
        
        if nocoins > cur_bal:
            raise NotEnoughCoins()
        
        taken = (min(ret[0], nocoins), max(0, nocoins - ret[0]))
        
        cursor.execute(f"UPDATE player_data SET balance = "\
            f"balance - {taken[0]}, bank_bal = bank_bal - {taken[1]} "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")

        conn.commit()
        conn.close()
        return taken    

    def increment_nhouses(self):
        """increases the number of houses that the player has bought by 1"""

        db_query(f"UPDATE player_data SET n_houses = n_houses + 1 "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")

    def has_in_inventory(self, item: Item | int) -> bool:
        """if the player has the item in their inventory"""

        if isinstance(item, Item):
            item = item.id

        ret = db_query("SELECT * FROM inventories WHERE " \
            f"guild_id = {self.guild_id} AND user_id = {self.user_id} AND " \
            f'item_id = {item} AND inv_dc = "i"')
        
        if len(ret) > 0:
            return True
        return False
        
    def add_to_inventory(self, item: Item | int):
        """adds item to player's inventory"""

        if isinstance(item, Item):
            item = item.id

        conn = sqlite3.connect(Player.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT count FROM inventories WHERE " \
            f"guild_id = {self.guild_id} AND user_id = {self.user_id} AND " \
            f'item_id = {item} AND inv_dc = "i"')

        ret = cursor.fetchone()
        if ret is None:
            cursor.execute("INSERT INTO inventories VALUES " \
            f'({self.user_id}, {self.guild_id}, {item}, {1}, "i")')
        else:
            cursor.execute("UPDATE inventories SET count = count + 1 "\
                f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id} "\
                f'AND item_id = {item} AND inv_dc = "i"')

        conn.commit()
        conn.close()

    def remove_from_inventory(self, item: Item | int):
        """removes item from player's inventory"""

        if isinstance(item, Item):
            item = item.id

        conn = sqlite3.connect(Player.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT count FROM inventories WHERE " \
            f"guild_id = {self.guild_id} AND user_id = {self.user_id} AND " \
            f'item_id = {item} AND inv_dc = "i"')

        ret = cursor.fetchone()

        if ret is None:
            conn.close()
            raise NotInInventory()
        
        elif ret[0] == 1:
            cursor.execute("DELETE FROM inventories "\
                f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id} "\
                f'AND item_id = {item} AND inv_dc = "i"')
        else:
            cursor.execute("UPDATE inventories SET count = count - 1 "\
                f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id} "\
                f'AND item_id = {item} AND inv_dc = "i"')

        conn.commit()
        conn.close()
            
    def amount_in_inventory(self, item: Item | int, include_dc: bool = False) -> int:
        """return the amount of item in player's inventory. include_dc can be used to include display case"""

        if isinstance(item, Item):
            item = item.id

        ret = db_query("SELECT count FROM inventories WHERE " \
            f"guild_id = {self.guild_id} AND user_id = {self.user_id} AND " + \
            (f'item_id = {item}' if include_dc else f'item_id = {item} AND inv_dc = "i"'))
        
        if len(ret) == 0:
            return 0
        
        return sum([r[0] for r in ret])

    def get_inventory(self) -> list[tuple[Item, int]]:
        """
        returns player's entire inventory
        format: list of tuple of (Item, count)
        """

        ret = db_query("SELECT item_id, count FROM inventories WHERE " \
            f"guild_id = {self.guild_id} AND user_id = {self.user_id} AND " \
            'inv_dc = "i" ORDER BY item_id')
        
        ret = [(Item(r[0]), r[1]) for r in ret]

        return ret

    def move_item(self, item: Item | int, frm:Literal['i', 'd'], to:Literal['i', 'd']):

        # validate inputs
        if isinstance(item, Item):
            item = item.id
        if frm not in ['i', 'd'] and to not in ['i', 'd']:
            raise ValueError("invalid arguments. frm and to must be either i or d")
        if frm == to:
            raise ValueError("invalid arguments. frm and to cannot be equal")

        conn = sqlite3.connect(Player.DATABASE_PATH)
        cursor = conn.cursor()

        # get from count
        cursor.execute("SELECT count FROM inventories WHERE " \
            f"guild_id = {self.guild_id} AND user_id = {self.user_id} AND " \
            f'item_id = {item} AND inv_dc = "{frm}"')

        ret = cursor.fetchone()

        # none - raise error
        if ret is None:
            conn.close()
            raise NotInInventory()
        
        # only one - delete row
        elif ret[0] == 1:
            cursor.execute("DELETE FROM inventories "\
                f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id} "\
                f'AND item_id = {item} AND inv_dc = "{frm}"')
        # else - decrease count by 1
        else:
            cursor.execute("UPDATE inventories SET count = count - 1 "\
                f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id} "\
                f'AND item_id = {item} AND inv_dc = "{frm}"')

        # get to count
        cursor.execute("SELECT count FROM inventories WHERE " \
            f"guild_id = {self.guild_id} AND user_id = {self.user_id} AND " \
            f'item_id = {item} AND inv_dc = "{to}"')
        ret = cursor.fetchone()

        # if none, add new row
        if ret is None:
            cursor.execute("INSERT INTO inventories VALUES " \
            f'({self.user_id}, {self.guild_id}, {item}, {1}, "{to}")')
        # else, increase count by 1
        else:
            cursor.execute("UPDATE inventories SET count = count + 1 "\
                f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id} "\
                f'AND item_id = {item} AND inv_dc = "{to}"')

        conn.commit()
        conn.close()

    def move_to_display(self, item: Item | int):
        """moves item from inventory to display case"""

        self.move_item(item, 'i', 'd')

    def move_from_display(self, item: Item | int):
        """moves item from display case to inventory"""

        self.move_item(item, 'd', 'i')

    def get_display(self) -> list[Item]:
        """
        returns player's entire display case
        format: list of tuple of (Item, count)
        """

        ret = db_query("SELECT item_id, count FROM inventories WHERE " \
            f"guild_id = {self.guild_id} AND user_id = {self.user_id} AND " \
            'inv_dc = "d" ORDER BY item_id')
        
        ret = [(Item(r[0]), r[1]) for r in ret]

        return ret

    def get_item_from_invno(self, invno: int) -> Item:
        """gets item id of item in inventory location"""

        invitems = self.get_inventory()

        try:
            itemid = invitems[invno - 1][0]

        except IndexError:
            raise NotInInventory()
        
        return itemid

    def get_item_from_dcno(self, dcno: int) -> Item:
        """gets item id of item in display case location"""

        dcitems = self.get_display()

        try:
            itemid = dcitems[dcno - 1][0]

        except IndexError:
            raise NotInInventory()
        
        return itemid

    def clear_inventory(self):
        """clears a player's inventory"""

        db_query(f"DELETE FROM inventories "\
            f"WHERE user_id = {self.user_id} AND guild_id = {self.guild_id} AND "\
            f'inv_dc = "i"')

    def deposit(self, nocoins:int):
        """move coins from bal to bank"""

        conn = sqlite3.connect(Player.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(f"SELECT balance FROM player_data "\
            f"WHERE user_id = {self.user_id} AND guild_id = {self.guild_id}")

        ret = cursor.fetchone()[0]

        if ret < nocoins:
            raise NotEnoughCoins()
        
        cursor.execute(f"UPDATE player_data SET balance = balance - "\
            f"{nocoins}, bank_bal = bank_bal + {nocoins} WHERE "\
            f"user_id = {self.user_id} AND guild_id = {self.guild_id}")

        conn.commit()
        conn.close()

        return ret
        
    def withdraw(self, nocoins):
        """move coins from bank to bal"""

        conn = sqlite3.connect(Player.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(f"SELECT bank_bal FROM player_data "\
            f"WHERE user_id = {self.user_id} AND guild_id = {self.guild_id}")

        ret = cursor.fetchone()[0]

        if ret < nocoins:
            raise NotEnoughCoins()
        
        cursor.execute(f"UPDATE player_data SET bank_bal = bank_bal - "\
            f"{nocoins}, balance = balance + {nocoins} WHERE "\
            f"user_id = {self.user_id} AND guild_id = {self.guild_id}")

        conn.commit()
        conn.close()

        return ret

    @staticmethod
    def reduce_bank_holdings_by_percent(percent: float, guildid:int) -> int:
        """reduces all bank holdings by a certain percent, then returns the money taken. for bankrob"""

        conn = sqlite3.connect(Player.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(f"SELECT bank_bal, user_id FROM player_data WHERE guild_id = {guildid}")

        all_bank_dat = cursor.fetchall()
        
        reductions = []

        for row in all_bank_dat:

            amount_reduced = int(round(percent * row[0]))
            reductions.append((amount_reduced, row[1]))

        cursor.executemany(f"UPDATE player_data SET bank_bal = bank_bal - ? "\
            f"WHERE guild_id = {guildid} AND user_id = ?",
            reductions)

        conn.commit()
        conn.close()

        return reductions

    def get_shop_price(self, item: Item | int) -> int:
        """get shop price of item"""

        if isinstance(item, int):
            item = Item(item)

        if item.id == 6:
            return int(round(item.get_shop_price() * (1 + 0.2 * self.nhouses ** 2)))
        
        return item.get_shop_price()
    
    def get_sale_price(self, item: Item | int) -> int:
        """get sale price of item"""

        if isinstance(item, int):
            item = Item(item)

        try:
            sale_price = self.get_shopitem_saleprice(item)
        except ItemNotFound:
            if item.basetype == "fish":
                sale_price = self.get_fish_saleprice(item)
            else:
                sale_price = item.get_sale_price()

        return int(round(sale_price))

    def collect_rent(self) -> tuple[int, td]:
        """collect player's rent"""

        conn = sqlite3.connect(Player.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT n_houses, last_collected_rent, "\
            "rent_time_increase, rent_multiplier FROM player_data "\
            f"WHERE user_id = {self.user_id} AND guild_id = {self.guild_id}")
        n_houses, lcr, rti, rm = cursor.fetchone()

        lcr = dt.fromtimestamp(lcr, tz=tz.utc)
        now = dt.now(tz=tz.utc)
        tpassed = now - lcr

        rm = min(rm, 5) # no more than 5

        daily_rent = int(n_houses * DAILY_RENT * rent_multiplier(rm))
        tincrement = td(seconds=86400 / daily_rent)
        increments_passed = int(floor(tpassed / tincrement))
        new_lcr = lcr + increments_passed * tincrement
        rent_to_collect = min(daily_rent * (1 + rti), increments_passed)
        if rent_to_collect == 0:
            conn.close()
            return 0, td()

        cursor.execute(f"UPDATE player_data SET balance = balance + {rent_to_collect}, "\
            f"last_collected_rent = {new_lcr.timestamp()} "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")
        
        # print(nohouses, lcr.isoformat(), now.isoformat())
        # print(tpassed.total_seconds(), tincrement.total_seconds(), increments_passed)
        # print(new_lcr.isoformat(), rent_to_collect, min(td(days=1), new_lcr-lcr).total_seconds())

        conn.commit()
        conn.close()

        return rent_to_collect, min(td(days=1 + rti), new_lcr - lcr)

    def reset_lcr(self):
        """reset player's last collected rent timestamp"""
        db_query(f"UPDATE player_data SET "\
            f"last_collected_rent = {dt.now(tz=tz.utc).timestamp()} "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")

    @staticmethod
    def get_total_in_circulation(guild_id:Optional[int]=None):
        """get total number of coins in circulation"""
        if guild_id is None:
            rows = db_query(f"SELECT balance, bank_bal FROM player_data")
        else:
            rows = db_query(f"SELECT balance, bank_bal FROM player_data "\
                f"WHERE guild_id = {guild_id}")
        total = sum([sum(row) for row in rows])
        return total

    def get_fishing_luck(self):
        """get player's fishing luck (0-999)"""
        raw = random.random()
        ret = db_query(f"SELECT base_luck, fishing_luck FROM player_data "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")
        bl, fl = ret[0]
        adj = raw ** (0.95 ** bl * 0.9 ** fl)
        return floor(adj * 1000)

    def get_working_luck(self):
        """get player's working luck (0-99)"""
        raw = random.random()
        ret = db_query(f"SELECT base_luck, work_luck FROM player_data "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")
        bl, wl = ret[0]
        adj = raw ** (0.95 ** bl * 0.9 ** wl)
        return floor(adj * 100)

    def get_work_multiplier(self):
        """get player's work earnings multiplier"""
        ret = db_query(f"SELECT work_multiplier FROM player_data "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")
        wm = work_multiplier(ret[0][0])
        return min(wm, 10)

    def get_robbing_luck(self):
        """get player's working luck (0-99)"""
        raw = random.random()
        ret = db_query(f"SELECT base_luck, rob_luck FROM player_data "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")
        bl, rl = ret[0]
        adj = raw ** (0.95 ** bl * 0.9 ** rl)
        return floor(adj * 100)

    def get_shopitem_saleprice(self, item: Item | int):
        """get sale price of shop item"""

        if isinstance(item, int):
            item = Item(item)

        raw = item.get_shop_price()

        ret = db_query(f"SELECT shop_sale_increase FROM player_data "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")
        ssi = ret[0][0]

        saleprice = min(raw * shopitem_saleprice_multiplier(ssi), raw)  # linear increase to 100%

        return saleprice

    def get_fish_saleprice(self, fish: Item | int):
        """get fish sale price"""

        if isinstance(fish, int):
            fish = Item(fish)

        ret = db_query(f"SELECT fish_sale_increase FROM player_data "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")
        fsi = ret[0][0]

        base_fishprice = fish.get_sale_price()

        return min(base_fishprice * fish_saleprice_multiplier(fsi), base_fishprice * 10)

    def get_fishing_rod_limit(self):
        """get player's fishing rod limit"""

        ret = db_query(f"SELECT rod_limit_increase FROM player_data "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")
        rli = ret[0][0]

        return min(3 + rli, 10)

    def get_research_queue(self):
        """get player's research queuea"""

        ret = db_query(f"SELECT in_progress_id, in_progress_ts FROM player_data "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")

        return ret[0]

    def get_current_level(self, techid: str) -> int:
        """get player's current level of given tech"""

        ret = db_query(f"SELECT {techid} FROM player_data "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")
        return ret[0][0]
    
    def get_available_research(self) -> dict[str, int]:
        """get all research options that are currently available to the player"""

        current_levels = self.get_research_data()
        available = dict()

        
        for techid, tech in Player.RESEARCH_CONFIG.items():

            current_level = current_levels[techid]

            if current_level >= len(tech["prereqs"]):
                continue # completed this branch of the tree

            available[techid] = current_level+1
            for prereq, i in tech["prereqs"][current_level].items():

                if current_levels[prereq] < i:
                    del available[techid]
                    break
        
        return available

    def get_research_data(self) -> dict[str, int]:
        """get player's research data"""

        res = db_query(f"""SELECT base_luck,
            fishing_luck,
            work_luck,
            work_multiplier,
            rob_luck,
            shop_sale_increase,
            fish_sale_increase,
            rod_limit_increase,
            rent_time_increase,
            rent_multiplier,
            in_progress_id,
            in_progress_ts FROM player_data 
            WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}""")
        
        ret = dict(zip(["base_luck",
            "fishing_luck",
            "work_luck",
            "work_multiplier",
            "rob_luck",
            "shop_sale_increase",
            "fish_sale_increase",
            "rod_limit_increase",
            "rent_time_increase",
            "rent_multiplier",
            "in_progress_id",
            "in_progress_ts"], res[0]))

        return ret

    def remove_all_data(self):
        """Removes all data for a player."""

        conn = sqlite3.connect(Player.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM inventories WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")
        cursor.execute(f"DELETE FROM player_data WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")
        conn.commit()
        conn.close()

    def begin_research(self, techid: str):
        """begin given research"""

        if techid not in Player.RESEARCH_CONFIG.keys():
            techid = Player.get_tech_from_short_code(techid)

        conn = sqlite3.connect(Player.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(f"SELECT in_progress_id, in_progress_ts, {techid}, balance FROM player_data "\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")
        
        ret = cursor.fetchone()
        queue = ret[0:2]
        currentlevel = ret[2]
        cur_bal = ret[3]
        
        if queue[1] is not None:
            conn.close()
            raise ResearchQueueFull()

        tech = Player.RESEARCH_CONFIG[techid]

        if cur_bal < tech["costs"][currentlevel]:
            conn.close()
            raise NotEnoughCoins()

        # check prerequisites
        for prereq, i in tech["prereqs"][currentlevel].items():

            cursor.execute(f"SELECT {prereq} FROM player_data "\
                f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")
            prereq_level = cursor.fetchone()[0]

            if prereq_level < i:
                conn.close()
                raise MissingPrerequisites(f"Missing prerequisites: "
                    f"{Player.RESEARCH_CONFIG[prereq]['name']} needs to be level {prereq_level}.")

        # Checks passed, begin Research
        now = time.time()
        done = now + tech["time"][currentlevel] * 3600
        
        self.take_coins(tech["costs"][currentlevel], True)

        cursor.execute(f'UPDATE player_data SET in_progress_id = "{tech["short_code"]}", in_progress_ts = {done} '\
            f"WHERE guild_id = {self.guild_id} AND user_id = {self.user_id}")

        conn.commit()
        conn.close()

    @staticmethod
    def update_all_research_queues():

        now = time.time()

        all_tech_queues = db_query("SELECT user_id, guild_id, in_progress_id, "\
            "in_progress_ts FROM player_data WHERE in_progress_id IS NOT NULL")
        
        for row in all_tech_queues:
            if now >= row[3]:
                techid = Player.get_tech_from_short_code(row[2])
                # if a queue is done, add level and empty queue
                db_query("UPDATE player_data SET in_progress_ts = NULL, "\
                    f"in_progress_id = NULL, {techid} = {techid} + 1 "\
                    f"WHERE user_id = {row[0]} AND guild_id = {row[1]}")

    def force_end_queue(self):
        """forcibly finish current research"""

        conn = sqlite3.connect(Player.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT in_progress_id, in_progress_ts FROM "\
            f"player_data WHERE guild_id = {self.guild_id} "\
            f"AND user_id = {self.user_id}")

        queue = cursor.fetchone()

        if queue[1] is None:
            conn.close()
            return

        techid = Player.get_tech_from_short_code(queue[0])
        cursor.execute("UPDATE player_data SET in_progress_ts = NULL, "\
                    f"in_progress_id = NULL, {techid} = {techid} + 1 "\
                    f"WHERE user_id = {self.user_id} AND guild_id = {self.guild_id}")

        conn.commit()
        conn.close()

    def remove_all_research(self):
        """reset all research back to zero"""

        db_query("UPDATE player_data SET in_progress_ts = NULL, "\
            "in_progress_id = NULL, " + ", ".join([f"{id} = 0" for id in Player.RESEARCH_CONFIG.keys()]) + \
            f" WHERE user_id = {self.user_id} AND guild_id = {self.guild_id}")

    @staticmethod
    def raw_query(query:str):

        conn = sqlite3.connect(Player.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(query)

        ret = cursor.fetchall()

        conn.commit()
        conn.close()

        return ret

    @staticmethod
    def get_tech_from_short_code(short_code:str) -> str:
        for key, v in Player.RESEARCH_CONFIG.items():
            if v['short_code'] == short_code:
                return key
        raise KeyError(f"Short code {short_code} not found.")

def db_query(query):

    """For simple, single-line queries"""

    conn = sqlite3.connect(Player.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(query)
    ret = cursor.fetchall()
    conn.commit()
    conn.close()

    return ret

def work_multiplier(we):
    return 10 ** (we / 5)

def shopitem_saleprice_multiplier(spi):
    return 0.75 + spi / 16

def fish_saleprice_multiplier(fpi):
    return 10 ** (0.1 * fpi)

def rent_multiplier(rm):
    return 2 ** (rm / 5)

def main():
    pass

if __name__ == "__main__":
    main()
