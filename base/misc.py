import re

import discord
from discord.ext import commands

try:
    import env
except ImportError:
    from base import env

env.BBGLOBALS.init_globals()

# Command prefix function
def is_command(_: commands.Bot, message: discord.Message) -> str:
    # Allow to match with "bb " or "bb, "
    if env.BBGLOBALS.IS_IN_DEV_MODE:
        # !bb as dev-mode command
        _m = re.match("!?bb,? ", message.content)
        if _m is not None:
            return _m.group(0)
    else:
        _m = re.match("bb,? ", message.content)
        if _m is not None:
            return _m.group(0)

    # Allow to match with direct address
    m = re.match("(hey |hello |hi )?barrel ?bot[,!.]? +", message.content, flags=re.I)
    if m is not None:
        return m.group(0)

    # Allow to match with mention
    m_ = re.match("<@733514909823926293>[,!.]? +", message.content)
    if m_ is not None:
        return m_.group(0)

    # Default
    return "BarrelBot, "

def time_str(time):
    """Takes a float of seconds and turns it into appropriate days, hours, minutes, and seconds."""

    res = [0,0,0,0]

    # days
    res[0] = time // 86400
    time = time % 86400

    # hours
    res[1] = time // 3600
    time = time % 3600

    # minutes, seconds
    res[2] = time // 60
    res[3] = time % 60

    strs = (" day"," hour"," minute"," second")
    outstr = ""

    for i in range(4):
        if res[i] == 0:
            continue
        elif res[i] == 1:
            if outstr == "":
                outstr += "1" + strs[i]
            else:
                outstr += ", 1" + strs[i]
        else:
            if outstr == "":
                outstr += str(res[i]) + strs[i] + "s"
            else:
                outstr += ", " + str(res[i]) + strs[i] + "s"

    return outstr

def main():
    print(time_str(48*60*60 + 32*60 + 42))
    print(time_str(49*60*60 + 32*60 + 42))
    print(time_str(49*60*60 + 42))
    print(time_str(24*60*60 + 1*60 + 1))
    print(time_str(24*60*60 + 1))
    print(time_str(1))

if __name__ == "__main__":
    main()