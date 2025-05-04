import os
import json

import discord

from base.extra_exceptions import *
from item import Item

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
            if "bank" not in _playerdata[key].keys():
                _playerdata[key]["bank"] = 0

    def __init__(self, user:discord.User):
        
        self.user = user
        self.id = user.id
        self.idstr = str(user.id)
        if self.idstr not in Player._playerdata.keys():
            Player._playerdata[self.idstr] = {"bal": 0, "inv": [], "dc": [], "bank": 0}
        if "bank" not in Player._playerdata[self.idstr]:
            Player._playerdata[self.idstr]["bank"] = 0

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
    
    def amount_in_inventory(self, item:Item|int) -> int:
        if isinstance(item, int):
            item = Item(id=item)
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
        jsond = {}
        for key in Player._playerdata.keys():
            jsond[key] = {
                "bal": Player._playerdata[key]["bal"],
                "inv": [int(item) for item in Player._playerdata[key]["inv"]],
                "dc": [int(item) for item in Player._playerdata[key]["dc"]],
                "bank": Player._playerdata[key]["bank"]
            }
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
            nohouses = self.amount_in_inventory(item)
            return int(item.get_shop_price()*(1+0.2*nohouses**2))
        return item.get_shop_price()