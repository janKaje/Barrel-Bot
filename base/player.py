import os
import json
from datetime import datetime as dt
from datetime import timezone as tz
from datetime import timedelta as td
from math import floor
import random
import time

import discord
from numpy import isin

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from extra_exceptions import *
from item import Item

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
# 
# Rent collection time extension (up to 7 days, 6 upgrades)
#  \__> Rent multiplier (up to 2x more, 5 upgrades) (from rc no 4)

research = {
    'bl': {
        'name': 'Base luck increase', 
        'costs': [5000, 10000, 15000, 20000, 30000], 
        'time': [12, 24, 36, 48, 72], 
        'prereqs': [{}, {'bl': 1}, {'bl': 2}, {'bl': 3}, {'bl': 4}]
    }, 
    'fl': {
        'name': 'Fishing luck increase', 
        'costs': [10000, 20000, 30000, 50000, 70000], 
        'time': [24, 48, 72, 96, 120], 
        'prereqs': [{'bl': 5}, {'fl': 1}, {'fl': 2}, {'fl': 3}, {'fl': 4}]
    }, 
    'wl': {
        'name': 'Working luck increase', 
        'costs': [10000, 20000, 30000, 40000, 50000], 
        'time': [24, 48, 72, 96, 120], 
        'prereqs': [{'bl': 5}, {'wl': 1}, {'wl': 2}, {'wl': 3}, {'wl': 4}]
    }, 
    'we': {
        'name': 'Work earnings increase', 
        'costs': [10000, 15000, 20000, 30000, 40000], 
        'time': [48, 72, 96, 120, 168], 
        'prereqs': [{'wl': 2}, {'we': 1}, {'we': 2}, {'we': 3}, {'we': 4}]
    }, 
    'rl': {
        'name': 'Robbery luck increase', 
        'costs': [10000, 30000, 50000, 70000, 100000], 
        'time': [24, 48, 72, 96, 120], 
        'prereqs': [{'bl': 5}, {'rl': 1}, {'rl': 2}, {'rl': 3}, {'rl': 4}]
    }, 
    'spi': {
        'name': 'Shop item sale price increase', 
        'costs': [2000, 3000, 5000, 7500], 
        'time': [12, 24, 36, 60], 
        'prereqs': [{}, {'spi': 1}, {'spi': 2}, {'spi': 3}]
    }, 
    'fpi': {
        'name': 'Fish sale price increase', 
        'costs': [20000, 40000, 60000, 100000, 130000, 160000, 200000, 250000, 300000, 350000], 
        'time': [48, 60, 72, 84, 96, 120, 144, 168, 240, 336], 
        'prereqs': [{'spi': 2}, {'fpi': 1}, {'fpi': 2}, {'fpi': 3}, {'fpi': 4}, {'fpi': 5}, {'fpi': 6}, {'fpi': 7}, {'fpi': 8}, {'fpi': 9}]
    }, 
    'frl': {
        'name': 'Fishing rod limit increase', 
        'costs': [50000, 100000, 150000, 200000, 300000, 400000, 500000], 
        'time': [72, 96, 120, 144, 240, 336, 504], 
        'prereqs': [{'fpi': 5, 'fl': 2}, {'frl': 1}, {'frl': 2}, {'frl': 3}, {'frl': 4}, {'frl': 5}, {'frl': 6}]
    }, 
    'rc': {
        'name': 'Rent collection time limit increase', 
        'costs': [5000, 10000, 15000, 20000, 25000, 30000], 
        'time': [12, 24, 36, 48, 72, 96], 
        'prereqs': [{}, {'rc': 1}, {'rc': 2}, {'rc': 3}, {'rc': 4}, {'rc': 5}]
    }, 
    'rm': {
        'name': 'Rent multiplier', 
        'costs': [50000, 100000, 200000, 300000, 400000], 
        'time': [72, 120, 144, 240, 336], 
        'prereqs': [{'rc': 4}, {'rm': 1}, {'rm': 2}, {'rm': 3}, {'rm': 4}]
    }
}


class Player:

    with open(dir_path + "/data/playerdata.json") as file:
        _playerdata = json.load(file)
        for key in _playerdata.keys():
            for invi in range(len(_playerdata[key]["inv"])):
                if isinstance(_playerdata[key]["inv"][invi], int):
                    _playerdata[key]["inv"][invi] = Item(_playerdata[key]["inv"][invi])
            for dci in range(len(_playerdata[key]["dc"])):
                if isinstance(_playerdata[key]["dc"][dci], int):
                    _playerdata[key]["dc"][dci] = Item(_playerdata[key]["dc"][dci])
            if "lcr" not in _playerdata[key].keys():
                _playerdata[key]["lcr"] = 0
            if "tech" not in _playerdata[key].keys():
                _playerdata[key]["tech"] = {
                    "bl": 0,  # base luck
                    "fl": 0,  # fishing luck
                    "wl": 0,  # working luck
                    "we": 0,  # work earnings multiplier
                    "rl": 0,  # robbery luck
                    "spi": 0, # shop item sale price increase
                    "fpi": 0, # fish sale price increase
                    "frl": 0, # fishing rod limit increase
                    "rc": 0,  # rent collection time increase
                    "rm": 0,  # rent multiplier
                    "in progress": [None, None] # should be in the form [techid, timestamp it finishes]
                }

    def __init__(self, user:discord.User):
        
        self.user = user
        self.id = user.id
        self.idstr = str(user.id)
        if self.idstr not in Player._playerdata.keys():
            Player._playerdata[self.idstr] = {"bal": 0, "inv": [], "dc": [], "bank": 0, "lcr": 0, "tech": []}

    def give_coins(self, nocoins:int):
        if (Player._playerdata[self.idstr]["bal"] + nocoins) < 0:
            raise NotEnoughCoins("Not enough coins")
        Player._playerdata[self.idstr]["bal"] += nocoins
        return
    
    def get_balance(self):
        return Player._playerdata[self.idstr]["bal"]
    
    def has_in_inventory(self, item:Item|int) -> bool:
        if isinstance(item, int):
            item = Item(id=item)
        return item in Player._playerdata[self.idstr]["inv"]
    
    def add_to_inventory(self, item:Item|int):
        if isinstance(item, int):
            item = Item(id=item)
        Player._playerdata[self.idstr]["inv"].append(item)
        return
    
    def remove_from_inventory(self, item:Item|int):
        if isinstance(item, int):
            item = Item(id=item)
        if item not in Player._playerdata[self.idstr]["inv"]:
            raise NotInInventory()
        Player._playerdata[self.idstr]["inv"].remove(item)
        return
    
    def amount_in_inventory(self, item:Item|int, include_dc:bool=False) -> int:
        if isinstance(item, int):
            item = Item(id=item)
        if include_dc == True:
            return Player._playerdata[self.idstr]["inv"].count(item) + Player._playerdata[self.idstr]["dc"].count(item)
        return Player._playerdata[self.idstr]["inv"].count(item)
    
    def recent_in_inventory(self) -> Item:
        return Player._playerdata[self.idstr]["inv"][-1]
    
    def get_inventory(self) -> list[Item]:
        return Player._playerdata[self.idstr]["inv"]
    
    def move_to_display(self, item:Item|int):
        if isinstance(item, int):
            item = Item(id=item)
        if item not in Player._playerdata[self.idstr]["inv"]:
            raise NotInInventory()
        Player._playerdata[self.idstr]["inv"].remove(item)
        Player._playerdata[self.idstr]["dc"].append(item)
        return
    
    def move_from_display(self, item:Item|int):
        if isinstance(item, int):
            item = Item(id=item)
        if item not in Player._playerdata[self.idstr]["dc"]:
            raise NotInDisplayCase()
        Player._playerdata[self.idstr]["dc"].remove(item)
        Player._playerdata[self.idstr]["inv"].append(item)
        return
    
    def recent_in_display(self) -> Item:
        return Player._playerdata[self.idstr]["dc"][-1]
    
    def get_display(self) -> list[Item]:
        return Player._playerdata[self.idstr]["dc"]
    
    def get_item_from_invno(self, invno:int) -> Item:
        invitems = list(set(Player._playerdata[self.idstr]["inv"]))
        invitems.sort(key=lambda i: i.id)
        try:
            itemid = invitems[invno-1]
        except IndexError:
            raise NotInInventory()
        return itemid
    
    def get_item_from_dcno(self, dcno:int) -> Item:
        dcitems = list(set(Player._playerdata[self.idstr]["dc"]))
        dcitems.sort(key=lambda i: i.id)
        try:
            itemid = dcitems[dcno-1]
        except IndexError:
            raise NotInDisplayCase()
        return itemid
    
    def clear_inventory(self):
        Player._playerdata[self.idstr]["inv"] = []

    def get_json_data():
        jsond = {key: {"bal":0, "inv":[], "dc":[], "bank":0, "lcr":0, "tech":{}} for key in Player._playerdata.keys()}
        for key, val in Player._playerdata.items():
            for i, item in val.items():
                if isinstance(item, list):
                    jsond[key][i] = [int(j) for j in item]
                else:
                    jsond[key][i] = item
        return jsond
    staticmethod(get_json_data)

    def deposit(self, nocoins):
        self.give_coins(-nocoins)
        Player._playerdata[self.idstr]["bank"] += nocoins

    def withdraw(self, nocoins):
        if nocoins > Player._playerdata[self.idstr]["bank"]:
            raise NotEnoughCoins
        self.give_coins(nocoins)
        Player._playerdata[self.idstr]["bank"] -= nocoins
        
    def get_bank_balance(self):
        return Player._playerdata[self.idstr]["bank"]
    
    def get_all_bank_data():
        return [[key, val["bank"]] for key, val in Player._playerdata.items()]
    staticmethod(get_all_bank_data)

    def reduce_bank_holdings_by_percent(percent:float):
        reductions = []
        for key in Player._playerdata.keys():
            amount_reduced = int(round(percent * Player._playerdata[key]["bank"]))
            reductions.append(amount_reduced)
            Player._playerdata[key]["bank"] -= amount_reduced
        return reductions
    staticmethod(reduce_bank_holdings_by_percent)

    def get_whole_balance(self):
        return Player._playerdata[self.idstr]["bank"] + Player._playerdata[self.idstr]["bal"]
    
    def take_coins(self, nocoins:int, includeBank=False):
        bank = self.get_bank_balance(); bal = self.get_balance()
        if nocoins > bank+bal or (nocoins > bal and includeBank==False):
            raise NotEnoughCoins()
        if includeBank==True and nocoins > bal:
            frombank = nocoins-bal
            Player._playerdata[self.idstr]["bank"] -= frombank
            self.give_coins(-bal)
            return bal, frombank
        self.give_coins(-nocoins)
        return nocoins, 0
    
    def get_shop_price(self, item:Item|int):
        if isinstance(item, int):
            item = Item(item)
        if item.id == 6:
            nohouses = self.amount_in_inventory(item, include_dc=True)
            return int(round(item.get_shop_price()*(1+0.2*nohouses**2)))
        return item.get_shop_price()
    
    def collect_rent(self):
        nohouses = self.amount_in_inventory(6)
        lcr = dt.fromtimestamp(Player._playerdata[self.idstr]["lcr"], tz=tz.utc)
        now = dt.now(tz=tz.utc)
        tpassed = now-lcr
        rc = Player._playerdata[self.idstr]["tech"]["rc"]
        rm = min(Player._playerdata[self.idstr]["tech"]["rm"], 5)
        daily_rent = int(nohouses * DAILY_RENT * 2**(rm/5))
        tincrement = td(seconds=86400/daily_rent)
        increments_passed = int(floor(tpassed/tincrement))
        new_lcr = lcr + increments_passed*tincrement
        rent_to_collect = min(daily_rent*(1+rc), increments_passed)
        self.give_coins(rent_to_collect)
        Player._playerdata[self.idstr]["lcr"] = new_lcr.timestamp()
        # print(nohouses, lcr.isoformat(), now.isoformat())
        # print(tpassed.total_seconds(), tincrement.total_seconds(), increments_passed)
        # print(new_lcr.isoformat(), rent_to_collect, min(td(days=1), new_lcr-lcr).total_seconds())
        return rent_to_collect, min(td(days=1+rc), new_lcr-lcr)
    
    def reset_lcr(self):
        Player._playerdata[self.idstr]["lcr"] = dt.now(tz=tz.utc).timestamp()
        
    def get_all_players():
        players = []
        for key in Player._playerdata.keys():
            players.append(Player(discord.Object(id=int(key))))
        return players
    
        
    def get_fishing_luck(self):
        raw = random.random()
        bl = Player._playerdata[self.idstr]["tech"]["bl"]
        fl = Player._playerdata[self.idstr]["tech"]["fl"]
        adj = raw ** (0.95**bl * 0.9**fl)
        return floor(adj*1000)
        
    def get_working_luck(self):
        raw = random.random()
        bl = Player._playerdata[self.idstr]["tech"]["bl"]
        wl = Player._playerdata[self.idstr]["tech"]["wl"]
        adj = raw ** (0.95**bl * 0.9**wl)
        return floor(adj*100)
    
    def get_work_multiplier(self):
        we = Player._playerdata[self.idstr]["tech"]["we"]
        return min(work_multiplier(we), 10)
        
    def get_robbing_luck(self):
        raw = random.random()
        bl = Player._playerdata[self.idstr]["tech"]["bl"]
        rl = Player._playerdata[self.idstr]["tech"]["rl"]
        adj = raw ** (0.95**bl * 0.9**rl)
        return floor(adj*100)
    
    def get_shopitem_saleprice(self, item:Item|int):
        if isinstance(item, int):
            item = Item(item)
        if item.id == 6:
            nohouses = self.amount_in_inventory(item) - 1
            raw = int(item.get_shop_price()*(1+0.2*nohouses**2))
        else:
            raw = item.get_shop_price()
        spi = Player._playerdata[self.idstr]["tech"]["spi"]
        saleprice = min(raw * shopitem_saleprice_multiplier(spi), raw) # linear increase to 100%
        return saleprice
    
    def get_fish_saleprice(self, fish:Item|int):
        if isinstance(fish, int):
            fish = Item(fish)
        fpi = Player._playerdata[self.idstr]["tech"]["fpi"]
        base_fishprice = fish.get_sale_price()
        return min(base_fishprice * fish_saleprice_multiplier(fpi), base_fishprice * 10)
    
    def get_fishing_rod_limit(self):
        frl = Player._playerdata[self.idstr]["tech"]["frl"]
        return min(3 + frl, 10)

    def get_research_queue(self):
        return Player._playerdata[self.idstr]["tech"]["in progress"]
    
    def get_current_level(self, techid:str):
        return Player._playerdata[self.idstr]["tech"][techid]
    
    def get_research_data(self):
        return Player._playerdata[self.idstr]["tech"]
    
    def begin_research(self, techid:str):

        queue = self.get_research_queue()
        if queue[1] is None:
            raise ResearchQueueFull()
        
        currentlevel = self.get_current_level(techid)
        tech = research[techid]
        for prereq, i in tech["prereqs"][currentlevel].items():
            if self.get_current_level(prereq) < i:
                raise MissingPrerequisites()
            
        if self.get_whole_balance() < tech["costs"][currentlevel]:
            raise NotEnoughCoins()
        
        # checks passed, begin research
        now = time.time()
        done = now + tech["time"][currentlevel]*3600
        self.take_coins(tech["costs"][currentlevel], True)
        Player._playerdata[self.idstr]["tech"]["in progress"] = [techid, done]
    
    def update_all_research_queues():
        now = time.time()
        for playerkey in Player._playerdata.keys():
            inprogress = Player._playerdata[playerkey]["tech"]["in progress"]
            if inprogress[1] is not None:
                if now >= inprogress[1]:
                    Player._playerdata[playerkey]["tech"][inprogress[0]] += 1
                    Player._playerdata[playerkey]["tech"]["in progress"] = [None, None]
    staticmethod(update_all_research_queues)

    def force_end_queue(self):

        queue = self.get_research_queue()
        if queue[1] is None:
            return 
        
        Player._playerdata[self.idstr]["tech"][queue[0]] += 1
        Player._playerdata[self.idstr]["tech"]["in progress"] = [None, None]


def work_multiplier(we):
    return 10**(we/6)

def shopitem_saleprice_multiplier(spi):
    return 0.75 + spi/16

def fish_saleprice_multiplier(fpi):
    return 10**(0.1*fpi)

def main():
    print(research)

if __name__ == "__main__":
    main()
