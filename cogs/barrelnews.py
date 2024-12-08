import os
import datetime as dt

import discord
from discord.ext import commands, tasks

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# easily configurable reminder and deadline times
REMINDER_TIME = [16, 30] # 16:30 UTC
DEADLINE_TIME = [4, 0] # 04:00 UTC

BARREL_NEWS_CHANNEL_ID = 1297025420184518708
BARREL_REP_ROLE_ID = 1296985456105230412
BARREL_SUB_ROLE_ID = 1297023311556907028

BARREL_EMOJI = "<:barrel:1296987889942397001>"

remind_time = dt.time(hour=REMINDER_TIME[0], minute=REMINDER_TIME[1], tzinfo=dt.timezone.utc)
deadline_time = dt.time(hour=DEADLINE_TIME[0], minute=DEADLINE_TIME[1], tzinfo=dt.timezone.utc)


async def setup(bot):
    await bot.add_cog(barrelnews(bot))


class barrelnews(commands.Cog, name="Barrel News"):

    """To help with barrel news reminders and posts"""

    def __init__(self, bot:commands.Bot):
        self.bot = bot

        print(f"cog: {self.qualified_name} loaded")

    @commands.command()
    @commands.has_role(BARREL_REP_ROLE_ID)
    async def test_timing(self, ctx: commands.Context):
        prev_d = self.get_deadline(True)
        next_d = self.get_deadline(False)
        already = await self.check_if_already_posted()
        days_since_reveal = (dt.date.today() - dt.date(year=2024, month=1, day=25)).days
        days_of_bnn = days_since_reveal - 266 - 6 #6 days missed?

        outstr = f"Previous deadline: <t:{int(prev_d.timestamp())}>, or <t:{int(prev_d.timestamp())}:R>\n" +\
                 f"Next deadline: <t:{int(next_d.timestamp())}>, or <t:{int(next_d.timestamp())}:R>\n" +\
                 f"Already done for today: {already}\n" +\
                 f"Days since PS reveal: {days_since_reveal}\n" +\
                 f"Day of BNN: {days_of_bnn}"

        await ctx.send(outstr)

    @tasks.loop(time=remind_time)
    async def remind_loop(self):
        """Called every day at the time of reminder"""
        # check if bnn already posted
        if await self.check_if_already_posted():
            return

        next_deadline = self.get_deadline(prev=False)

        await self.news_channel.send(f"<@&{BARREL_REP_ROLE_ID}> don't forget to do daily {BARREL_EMOJI} news! "\
                                     f"If you haven't done it <t:{int(next_deadline.timestamp())}:R> I'll have to do it myself.")
        
    @tasks.loop(time=deadline_time)
    async def post_loop(self):
        """Called every day at the deadline. If the barrel reps haven't already sent BNN, barrelbot will"""
        # check if bnn already posted
        if await self.check_if_already_posted():
            return
        
        days_since_reveal = (dt.date.today() - dt.date(year=2024, month=1, day=25)).days
        days_of_bnn = days_since_reveal - 266 - 6 #6 days missed?

        await self.news_channel.send(f"# TODAY\n## ON BNN\nDay {days_of_bnn} of bringing you your daily {BARREL_EMOJI} news\n"\
                                     f"There has been no news to report on {BARREL_EMOJI} today "\
                                     f"(except for the fact that the <@&{BARREL_REP_ROLE_ID}> forgot to do this and I had to pick up their slack...)\n"\
                                     f"{days_since_reveal} days since PS reveal\n"\
                                     f"<@&{BARREL_SUB_ROLE_ID}>")

    async def cog_load(self):

        self.news_channel:discord.TextChannel = await self.bot.fetch_channel(BARREL_NEWS_CHANNEL_ID)

        self.remind_loop.start()
        self.post_loop.start()

    async def check_if_already_posted(self) -> bool:

        # get previous deadline
        prev_deadline = self.get_deadline(prev=True)

        # if any non-bot messages have been sent since last deadline, return true
        async for message in self.news_channel.history(after=prev_deadline):
            if not message.author.bot:
                return True
        
        # otherwise
        return False
    
    def get_deadline(self, prev:bool) -> dt.datetime:
        now = dt.datetime.now(tz=dt.timezone.utc)
        nowtime = now.time().replace(tzinfo=dt.timezone.utc)
        to_return = None
        if prev:
            if nowtime > deadline_time:
                # same day
                to_return = now.replace(hour=DEADLINE_TIME[0], minute=DEADLINE_TIME[1], second=0, microsecond=0)
            else:
                # previous day
                to_return = (now - dt.timedelta(days=1)).replace(hour=DEADLINE_TIME[0], minute=DEADLINE_TIME[1], second=0, microsecond=0)

            if (now - to_return).total_seconds() < 60: # if difference is small, get day before 
                return to_return - dt.timedelta(days=1)
            else:
                return to_return
        else:
            if nowtime >= deadline_time:
                # next day
                to_return = (now + dt.timedelta(days=1)).replace(hour=DEADLINE_TIME[0], minute=DEADLINE_TIME[1], second=0, microsecond=0)
            else:
                # same day
                to_return = now.replace(hour=DEADLINE_TIME[0], minute=DEADLINE_TIME[1], second=0, microsecond=0)

            if (to_return - now).total_seconds() < 60: # if difference is small, get day after
                return to_return + dt.timedelta(days=1)
            else:
                return to_return
        
