import env


class EmojiDefs:
    BARREL_COIN: str = "<:barrelcoin:1364027068936884405>"
    BARREL_EMOJI: str = "<:barrel:1296987889942397001>"
    HOLY_BARREL_EMOJI: str = "<:holybarrel:1303080132642209826>"

    # Debug
    @classmethod
    def init_emojis(cls):
        if env.BBGLOBALS.IS_IN_DEV_MODE:
            # Same emoji because we only have one on the test server
            cls.BARREL_COIN: str = "<:TESTbarrel:1303842935715921941>"
            cls.BARREL_EMOJI: str = "<:TESTbarrel:1303842935715921941>"
            cls.HOLY_BARREL_EMOJI: str = "<:TESTbarrel:1303842935715921941>"
