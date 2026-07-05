import os
import json
import math
from random import randint
from typing import Any, Optional

from extra_exceptions import ItemNotFound
from emojis import EmojiDefs as ED


# Inventory item ids
# Fishing rod: 1
# Dagger: 2
# Shield: 3
# Barrel Crate: 4
# Golden Barrel Crate: 5
# House: 6
# Beer: 7
# ...
# Prizes and unique items: 20-99
# Fish: (second two numbers are stats: length and weight)
#   Squid: 100
#   Jellyfish: 200
#   Shrimp: 300
#   Lobster: 400
#   Crab: 500
#   Blowfish: 600
#   Yellow fish: 700
#   Blue fish: 800
#   Shark: 900

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Item:

    with open(os.path.join(dir_path, "config", "item_config.json")) as file:
        ITEM_CONFIG:dict[dict[str,str|list]] = json.load(file)
        
    with open(os.path.join(dir_path, "config", "shop_config.json")) as file:
        SHOP_CONFIG:dict[dict[str,str|int]] = json.load(file)

    def __init__(self, item_id: int|str):

        if isinstance(item_id, int):
            self.id = abs(int(item_id))
            for key, val in self.ITEM_CONFIG.items():
                if val["id_range"][0] <= item_id <= val["id_range"][1]:
                    self.name = key
                    self.basetype = val["basetype"]
                    self.emoji = val["emoji"]
                    self.propername = val["proper_name"]
                    self.aliases = val["aliases"] + [
                        self.name, self.emoji, self.propername
                    ]
                    break
        elif item_id in self.ITEM_CONFIG.keys():
            config = self.ITEM_CONFIG[item_id]
            self.name = item_id
            self.basetype = config["basetype"]
            self.emoji = config["emoji"]
            self.propername = config["proper_name"]
            self.aliases = config["aliases"] + [
                self.name, self.emoji, self.propername
            ]
            self.id = config["id_range"][0]
        else:
            # try aliases
            for key, val in self.ITEM_CONFIG.items():
                if item_id in [key, val["emoji"], val["proper_name"]] + val["aliases"]:
                    self.name = key
                    self.basetype = val["basetype"]
                    self.emoji = val["emoji"]
                    self.propername = val["proper_name"]
                    self.aliases = val["aliases"] + [
                        self.name, self.emoji, self.propername
                    ]
                    self.id = val["id_range"][0]
                    break
        
        if getattr(self, "name", None) is None:
            raise ItemNotFound()
        
        self.emojiname = self.emoji + " - " + self.propername

        self.shop_price:Optional[int] = None
        self.shop_msg:Optional[str] = None
        self.shop_desc:Optional[str] = None

        if self.name in self.SHOP_CONFIG.keys():

            self.shop_price = self.SHOP_CONFIG[self.name]["price"]
            self.shop_msg = self.SHOP_CONFIG[self.name]["message"]
            self.shop_desc = self.SHOP_CONFIG[self.name]["description"]

            emoji_defs = [i for i in dir(ED) if i.upper() == i and isinstance(getattr(ED,i,None), str)] # filter for all-caps
            for emoj in emoji_defs:
                self.shop_msg = self.shop_msg.replace(emoj, getattr(ED, emoj))
                self.shop_desc = self.shop_desc.replace(emoj, getattr(ED, emoj))

        if getattr(ED, self.emoji, None) is not None:
            self.emoji = getattr(ED, self.emoji)
        

    def get_shop_price(self):
        if self.shop_price is None:
            raise ItemNotFound
        return self.shop_price

    def get_shop_message(self):
        if self.shop_msg is None:
            raise ItemNotFound
        return self.shop_msg

    def get_shop_description(self):
        if self.shop_desc is None:
            raise ItemNotFound
        return self.shop_desc

    def get_sale_price(self):
        if self.shop_price is not None:
            return int(math.floor(self.shop_price * 0.75))

        if self.id == 4:
            return randint(300, 500)

        if self.id == 5:
            return randint(700, 1200)

        if self.id == 7:
            return 3

        if self.basetype == "fish":
            fish_type = int(str(self.id)[0])
            length = int(str(self.id)[1])
            weight = int(str(self.id)[2])
            match fish_type:
                case 1:  # squid
                    multiplier = 5
                case 2:  # jellyfish
                    multiplier = 0.5
                case 3:  # shrimp
                    multiplier = 1.5
                case 4:  # lobster
                    multiplier = 2
                case 5:  # crab
                    multiplier = 2.5
                case 6:  # blowfish
                    multiplier = 4
                case 7:  # yellow fish
                    multiplier = 1
                case 8:  # blue fish
                    multiplier = 1
                case 9:  # shark
                    multiplier = 8
                case _:  # ???
                    multiplier = 1
            return max(int(multiplier * (math.exp(length / 3) + 1.5 * weight)), 1)
        return None  # not found

    def __str__(self):
        extra_info = self._extra_info()
        if extra_info == "":
            return self.emojiname
        return self.emojiname + " - " + extra_info

    def _extra_info(self):
        if self.basetype == "fish":
            return f"{(int(str(self.id)[1]) + 1) * 5} cm, {(int(str(self.id)[2]) + 1) * 0.5} kg"
        return ""

    def __int__(self):
        return self.id

    def __eq__(self, other):
        if isinstance(other, Item):
            return self.id == other.id
        return False

    def __hash__(self):
        return hash(self.id)


def main():
    to_json = {}
    for item_id in Item._shop_prices.keys():
        item = Item(item_id)
        to_json[item.name] = {
            "price": Item._shop_prices[item_id],
            "message": Item._shop_messages[item_id],
            "description": Item._shop_descriptions[item_id]
        }

    #     all_aliases = item._aliases[item_id]
    #     try:
    #         all_aliases.remove(item.propername)
    #         all_aliases.remove(item.emoji)
    #         all_aliases.remove(item.easyalias)
    #     except:
    #         pass
    #     to_json[item.easyalias] = {
    #         "basetype": item.basetype,
    #         "emoji": item.emoji,
    #         "proper_name": item.propername[4:],
    #         "aliases": all_aliases,
    #         "id_range": [item_id, int(item_id if item_id < 10 else item_id+99)]
    #     }
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "shop_config.json"), "w") as file:
        json.dump(to_json, file)

if __name__ == "__main__":
    main()
