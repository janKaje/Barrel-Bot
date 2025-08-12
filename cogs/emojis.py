from base import env

class EmojiDefs:
    BARREL_COIN = "<:barrelcoin:1364027068936884405>"
    BARREL_EMOJI = "<:barrel:1296987889942397001>"
    HOLY_BARREL_EMOJI = "<:holybarrel:1303080132642209826>"

    ## Debug
    @classmethod
    def initEmojis(cls):
        if env._BBGLOBALS.IS_IN_DEV_MODE : 

            # Same emoji because we only have one on the test server
            cls.BARREL_COIN = "<:TESTbarrel:1303842935715921941>"
            cls.BARREL_EMOJI = "<:TESTbarrel:1303842935715921941>"
            cls.HOLY_BARREL_EMOJI = "<:TESTbarrel:1303842935715921941>"