try:
    import env
except ImportError:
    from base import env
    
from discord import Guild

class EmojiDefs:
    BARREL_COIN: str = "<:barrelcoin:1364027068936884405>"
    BARREL_EMOJI: str = "<:barrel:1296987889942397001>"
    HOLY_BARREL_EMOJI: str = "<:holybarrel:1303080132642209826>"
    ALL_EMOJIS: list[str] = [
        "<:agonybarrel:1313267644933083296>",
        "<:alinebarrel:1297712447637028925>",
        "<:barrel:1296987889942397001>",
        "<:barrelart:1316098891782946836>",
        "<:barrelcake:1348850816123011102>",
        "<:barrelcoin:1364027068936884405>",
        "<:barrelconfetti:1316102028253991003>",
        "<:barrelglitch:1304136026759102566>",
        "<:barrelgun:1303207776142626847>",
        "<:barrelrocket:1380572933113647214>",
        "<:barrelsadge:1298695216185872500>",
        "<:bibarrel:1318044568398331994>",
        "<:brassbarrel:1303122968129572884>",
        "<:brickbarrel:1304145349912428614>",
        "<:catbarrel:1316152299210412112>",
        "<:ceddybarrel:1297712311976595536>",
        "<:coolbarrel:1316105850082820166>",
        "<:crimasbarrel:1321531495965265971>",
        "<:deepfriedbarrel:1297024342458368110>",
        "<:downbarrel:1297022173353082961>",
        "<:drugbarrel:1386751283955892264>",
        "<:duskbarrel:1302368437233909770>",
        "<:ghostbarrel:1304122865322426459>",
        "<:holybarrel:1303080132642209826>",
        "<:honeybarrel:1439009554930208990>",
        "<:invertedbarrel:1297024778493886507>",
        "<:jankajebarrel:1297711845439963156>",
        "<:junabarrel:1297712537131028481>",
        "<:leftbarrel:1297023099362869330>",
        "<:minecraftbarrel:1311041231685419008>",
        "<:purplegoldbarrel:1303126781364011080>",
        "<:rightbarrel:1297023173434540042>",
        "<:rosegoldbarrel:1303137439690395658>",
        "<:sleepybarrel:1316241890294763592>",
        "<:sparklebarrel:1380573448832684193>",
        "<:transbarrel:1318014752278056970>",
        "<:ultradeepfriedbarrel:1297025375616110644>",
        "<:uwubarrel:1386483676392591450>"
    ]
    
    @staticmethod
    def guild_barrel_emojis(guild: Guild):
        for emoji in guild.emojis:
            if "barrel" in emoji.name.lower():
                yield emoji

    # Debug
    @classmethod
    def init_emojis(cls):
        if env.BBGLOBALS.IS_IN_DEV_MODE:
            # Same emoji because we only have one on the test server
            cls.BARREL_COIN: str = "<:TESTbarrel:1303842935715921941>"
            cls.BARREL_EMOJI: str = "<:TESTbarrel:1303842935715921941>"
            cls.HOLY_BARREL_EMOJI: str = "<:TESTbarrel:1303842935715921941>"

            cls.ALL_EMOJIS: list[str] = [
                "<:TESTbarrel:1303842935715921941>",
                "<:rombic_dod:1266426479303196793>",
                "<:deepfriedbarrel:1499672037717966848>",
                "<:invertedbarrel:1499672169498808431>",
                "<:rightbarrel:1499672209541562520>",
                "<:sleepybarrel:1499672119917678712>"
            ]
        return