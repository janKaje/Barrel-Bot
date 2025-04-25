import math
from random import randint

from base.extra_exceptions import ItemNotFound

BARREL_COIN = "<:barrelcoin:1364027068936884405>"
BARREL_EMOJI = "<:barrel:1296987889942397001>"
HOLY_BARREL_EMOJI = "<:holybarrel:1303080132642209826>"

# Inventory item ids
# Fishing rod: 1
# Dagger: 2
# Shield: 3
# Barrel Crate: 4
# Golden Barrel Crate: 5
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
# Pets:
#   10000s?
# Tech:
#   10000s (find good storage method)

class Item(object):

    _basetypes = {
        1: "item",
        3: "fish"
    }

    _aliases = {
        0: ["Item not found."],
        1: ["🎣 - Fishing Rod", "fishing rod", "fishing pole", "🎣"],
        2: ["🗡️ - Dagger", "dagger", "🗡️"],
        3: ["🛡️ - Shield", "shield", "🛡️"],
        4: [BARREL_EMOJI + " - Barrel Crate", "barrel", "barrel crate", BARREL_EMOJI],
        5: [HOLY_BARREL_EMOJI + " - Golden Barrel Crate", "golden barrel", "golden barrel crate", "holy barrel", HOLY_BARREL_EMOJI],
        100: ["🦑 - Squid", "squid", "🦑"],
        200: ["🪼 - Jellyfish", "jellyfish", "🪼"],
        300: ["🦐 - Shrimp", "shrimp", "🦐"],
        400: ["🦞 - Lobster", "lobster", "🦞"],
        500: ["🦀 - Crab", "crab", "🦀"],
        600: ["🐡 - Blowfish", "blowfish", "🐡"],
        700: ["🐠 - Yellow Fish", "yellow fish", "🐠"],
        800: ["🐟 - Blue Fish", "blue fish", "🐟"],
        900: ["🦈 - Shark", "shark", "🦈"]
    }

    _shop_prices = {
        1: 100,
        2: 300,
        3: 300
    }

    _shop_messages = {
        1: "You bought a 🎣! If you didn't have one before, now you can do `bb fish`.",
        2: "You bought a 🗡️! If you didn't have one before, you can now try to rob people. Be warned, though: the life of crime isn't kind.",
        3: "You bought a 🛡️! If you didn't have one before, you're now mostly protected against people trying to rob you."
    }

    _shop_descriptions = {
        1: "Allows you to use the command `fish`. Collect fish to keep as trophies or sell for more " + BARREL_COIN,
        2: "Allows you to try to rob other people.",
        3: "Does a good job of blocking you from getting robbed." # finish later
    }

    def __init__(self, id:int):

        object.__init__(self)

        self.id = abs(int(id))
        self.typeid = int(str(id)[0] + "0"*(len(str(id))-1))
        try:
            self.emoji = Item._aliases[self.typeid][-1]
            self.propername = Item._aliases[self.typeid][0]
            self.easyalias = Item._aliases[self.typeid][1]
        except KeyError or ValueError:
            self.emoji = "❓"
            self.propername = "Item not found."
            self.easyalias = "Item not found."
        try:
            self.basetype = Item._basetypes[len(str(id))]
        except KeyError:
            self.basetype = "unknown"

    def get_shop_price(self):
        if self.id in Item._shop_prices.keys():
            return Item._shop_prices[self.id]
        raise ItemNotFound
    
    def get_shop_message(self):
        if self.id in Item._shop_messages.keys():
            return Item._shop_messages[self.id]
        raise ItemNotFound
    
    def get_shop_description(self):
        if self.id in Item._shop_descriptions.keys():
            return Item._shop_descriptions[self.id]
        raise ItemNotFound

    def get_sale_price(self):
        if self.id in Item._shop_prices.keys():
            return int(math.floor(Item._shop_prices[self.id]*0.75))
        if self.id == 4:
            return randint(300, 500)
        if self.id == 5:
            return randint(700, 1200)
        if self.basetype == "fish":
            type = int(str(self.id)[0])
            length = int(str(self.id)[1])
            weight = int(str(self.id)[2])
            match type:
                case 1: # squid
                    multiplier = 5
                case 2: # jellyfish
                    multiplier = 0.5
                case 3: # shrimp
                    multiplier = 1.5
                case 4: # lobster
                    multiplier = 2
                case 5: # crab
                    multiplier = 2.5
                case 6: # blowfish
                    multiplier = 4
                case 7: # yellow fish
                    multiplier = 1
                case 8: # blue fish
                    multiplier = 1
                case 9: # shark
                    multiplier = 8
                case _: # ???
                    multiplier = 1
            return max(int(multiplier * (math.exp(length/3) + 1.5*weight)), 1)
        return None # not found

    def __str__(self):
        if self.basetype == "item":
            return self.propername
        return self.propername + " - " + self._extra_info()

    def _extra_info(self):
        if self.basetype == "fish":
            return f"{(int(str(self.id)[1])+1)*5} cm, {(int(str(self.id)[2])+1)*0.5} kg"
        return ""
    
    def __int__(self):
        return self.id
    
    def get_from_string(instr:str):
        for key, val in Item._aliases.items():
            if instr.lower() in val:
                return Item(key)
            if instr.isdecimal():
                if int(instr) == key:
                    return Item(key)
        raise ItemNotFound()
    staticmethod(get_from_string)

    def __eq__(self, other):
        if isinstance(other, Item):
            return self.id == other.id
        return False
    
    def __hash__(self):
        return hash(self.id)

def main():
    fishingrod = Item(1)
    print(fishingrod.id, fishingrod.propername, fishingrod.basetype, fishingrod.easyalias, fishingrod.emoji, fishingrod.typeid)
    print(fishingrod.get_shop_price(), fishingrod.get_sale_price(), fishingrod.get_shop_message(), fishingrod.get_shop_description())

    rareshark = Item(687)
    print(rareshark.id, rareshark.propername, rareshark.basetype, rareshark.easyalias, rareshark.emoji, rareshark.typeid)
    print(rareshark.get_sale_price())

if __name__ == "__main__":
    main()