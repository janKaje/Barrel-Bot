import os
import sys
import json
import datetime as dt
from random import choice, randint, random
from math import floor
import requests  # http(s) requests (POST in our case)

import discord
from discord.ext import commands, tasks

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(dir_path, "base"))

import env
from emojis import EmojiDefs as ED

remind_time = dt.time(hour=env.BBGLOBALS.REMINDER_TIME[0], minute=env.BBGLOBALS.REMINDER_TIME[1],
                      tzinfo=dt.timezone.utc)
deadline_time = dt.time(hour=env.BBGLOBALS.DEADLINE_TIME[0], minute=env.BBGLOBALS.DEADLINE_TIME[1],
                        tzinfo=dt.timezone.utc)

with open("data/words.json") as file:
    words = json.load(file)
    emotions = words["emotions"]
    verbs = words["verbs"]
    adjectives = words["adjectives"]
    nouns = words["nouns"]
    interjections = words["interjections"]
    relationalterms = words["relationalterms"]

del words


async def setup(bot):
    await bot.add_cog(BarrelNews(bot))


class BarrelNews(commands.Cog, name="Barrel News"):
    """To help with barrel news reminders and posts"""

    def __init__(self, bot: commands.Bot):
        self.news_channel = None
        self.bot = bot
        self.bot_send = None

    def set_bot_send(self, bot_send):
        self.bot_send = bot_send

    @commands.command()
    @commands.has_role(env.BBGLOBALS.BARREL_REP_ROLE_ID)
    async def test_timing(self, ctx: commands.Context):
        prev_d = self.get_deadline(True)
        next_d = self.get_deadline(False)
        already = await self.check_if_already_posted()
        days_since_reveal = (dt.date.today() - dt.date(year=2024, month=1, day=25)).days - 1
        days_of_bnn = days_since_reveal - 266 - 6  # 6 days missed?

        outstr = f"Previous deadline: <t:{int(prev_d.timestamp())}>, or <t:{int(prev_d.timestamp())}:R>\n" + \
                 f"Next deadline: <t:{int(next_d.timestamp())}>, or <t:{int(next_d.timestamp())}:R>\n" + \
                 f"Already done for today: {already}\n" + \
                 f"Days since PS reveal: {days_since_reveal}\n" + \
                 f"Day of BNN: {days_of_bnn}"

        await self.bot_send(ctx, outstr)

    @commands.command()
    @commands.is_owner()
    async def test_reminder(self, ctx: commands.Context):

        remindmsg = self.get_reminder()

        await self.bot_send(ctx, remindmsg)

    @commands.command()
    @commands.is_owner()
    async def test_bnnmsg(self, ctx: commands.Context, msgtype: str):

        try:
            await self.bot_send(ctx, get_bnnmsg(int(msgtype)))
        except:
            msgtype = randint(1, 6)
            await self.bot_send(ctx, get_bnnmsg(msgtype))

    @tasks.loop(time=remind_time)
    async def remind_loop(self):
        """Called every day at the time of reminder"""
        # check if bnn already posted
        if await self.check_if_already_posted():
            return

        remindmsg = self.get_reminder()

        await self.news_channel.send(remindmsg)

    @tasks.loop(time=deadline_time)
    async def post_loop(self):
        """Called every day at the deadline. If the barrel reps haven't already sent BNN, barrelbot will"""
        # check if bnn already posted
        if await self.check_if_already_posted():
            return

        msgtype = randint(1, 6)

        bnnmsg = get_bnnmsg(msgtype)

        # POST TO WEBSITE (message and username)
        post_to_website(bnnmsg, self.bot.user.name)

        await self.news_channel.send(bnnmsg)

    async def cog_load(self):

        self.news_channel: discord.TextChannel = await self.bot.fetch_channel(env.BBGLOBALS.BARREL_NEWS_CHANNEL_ID)

        self.remind_loop.start()
        self.post_loop.start()

        # print loaded
        print(f"cog: {self.qualified_name} loaded")

    async def check_if_already_posted(self) -> bool:

        # get previous deadline
        prev_deadline = self.get_deadline(prev=True) + dt.timedelta(
            hours=1)  # one hour grace period between one deadline and start of next day

        # if any non-bot messages have been sent since last deadline, return true
        async for message in self.news_channel.history(after=prev_deadline):
            if not message.author.bot and str(env.BBGLOBALS.BARREL_SUB_MENTION) in message.content:
                return True

        # otherwise
        return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listens for messages, when it is in the news channel, and has pinged the news role, it counts as news and
        will be posted to the website"""
        if message.channel.id == env.BBGLOBALS.BARREL_NEWS_CHANNEL_ID:  # Checking in news channel
            print(message.content)
            print(str(env.BBGLOBALS.BARREL_SUB_MENTION))
            if (not message.author.bot) and str(
                    env.BBGLOBALS.BARREL_SUB_MENTION) in message.content:
                # checking if the message is from a User and has the barrel news mention
                name = message.author.name
                message_content = message.content

                print("")
                print("News Have Been Posted")
                print("POSTing to barrel website")
                print("Status :", end="")

                post_to_website(message_content, name)

                print("---")
                print("")

    @staticmethod
    def get_deadline(prev: bool) -> dt.datetime:
        now = dt.datetime.now(tz=dt.timezone.utc)
        nowtime = now.time().replace(tzinfo=dt.timezone.utc)
        if prev:
            if nowtime > deadline_time:
                # same day
                to_return = now.replace(hour=env.BBGLOBALS.DEADLINE_TIME[0], minute=env.BBGLOBALS.DEADLINE_TIME[1],
                                        second=0, microsecond=0)
            else:
                # previous day
                to_return = (now - dt.timedelta(days=1)).replace(hour=env.BBGLOBALS.DEADLINE_TIME[0],
                                                                 minute=env.BBGLOBALS.DEADLINE_TIME[1], second=0,
                                                                 microsecond=0)

            if (now - to_return).total_seconds() < 60:  # if difference is small, get day before
                return to_return - dt.timedelta(days=1)
            else:
                return to_return
        else:
            if nowtime >= deadline_time:
                # next day
                to_return = (now + dt.timedelta(days=1)).replace(hour=env.BBGLOBALS.DEADLINE_TIME[0],
                                                                 minute=env.BBGLOBALS.DEADLINE_TIME[1], second=0,
                                                                 microsecond=0)
            else:
                # same day
                to_return = now.replace(hour=env.BBGLOBALS.DEADLINE_TIME[0], minute=env.BBGLOBALS.DEADLINE_TIME[1],
                                        second=0, microsecond=0)

            if (to_return - now).total_seconds() < 60:  # if difference is small, get day after
                return to_return + dt.timedelta(days=1)
        return to_return

    def get_reminder(self):

        next_deadline = self.get_deadline(prev=False)

        remindmsg = choice(reminders)

        try:
            remindmsg = remindmsg.format(int(next_deadline.timestamp()))
        except:
            pass

        return remindmsg


def post_to_website(message, username):
    """Posts the message and username to the website as news, the endpoint and the key are environment variables
    
    The return object is a status code being printed to the console
    """
    obj = {
        "message": message,
        "discord_user": username,
        "key": env.BBGLOBALS.NEWS_KEY,
    }
    url = env.BBGLOBALS.NEWS_ENDPOINT
    request = requests.post(url, data=obj)
    print("Status", request)  # status


def rand_temp():
    rand = random() * 3.5
    return floor(10 ** rand)


def get_bnnmsg(msgtype):
    days_since_reveal = (dt.date.today() - dt.date(year=2024, month=1, day=25)).days - 1
    days_of_bnn = days_since_reveal - 266 - 6  # 6 days missed?

    bnnmsg = (f"# TODAY\n## ON BNN\nWelcome to day {days_of_bnn} of bringing you your daily {ED.BARREL_EMOJI} news! "
              f"I'm your host, Barrelbot, here to bring you your randomly-generated, `{choice(adjectives).lower()}` "
              f"news for today.\n\n")

    if msgtype == 1:

        ch1 = [
            'this week\'s episode of',
            'your mom\'s favorite',
            'every single',
            'Benadryl Cucumberpatch\'s',
            'the warm, toasty',
            'the wretched',
            'my'
        ]
        ch2 = [
            'eye patch',
            'Reddit account',
            'vtuber alter ego',
            'butler',
            'exploding beach ball',
            'weapons-grade plutonium',
            'oil refinery',
            'sled pulled by rabid opossums',
            '3-inch tungsten cube',
            'antique chandelier',
            'T6 Series 1000W AC Servo Motor Kit',
            'LORELEI S9 Wired Headphones with Microphone for School，On-Ear Kids Headphones for Girls Boys，Folding '
            'Lightweight and 3.5mm Audio Jack Headset for Phone, Ipad，Tablet, PC, Chromebook (Pearl Pink)'
        ]

        bnnmsg += (f"Today the {ED.BARREL_EMOJI} is feeling some `{choice(emotions).lower()}`, so please take that "
                   f"into account when you `{choice(verbs).lower()}` your `{choice(nouns).lower()}` today. It may "
                   f"also affect the way that you choose to `{choice(verbs).lower()}`. \n\nNew Research shows that a "
                   f"`{choice(adjectives).lower()}` `{choice(nouns).lower()}` is `{choice(adjectives).lower()}` to "
                   f"some `{choice(nouns).lower()}s`! So be sure to `{choice(verbs).lower()}` as much as you can "
                   f"today. That way you can be sure `{choice(ch1)}` `{choice(ch2)}` stays `"
                   f"{choice(adjectives).lower()}` and `{choice(adjectives).lower()}`!\n\n")

    elif msgtype == 2:

        ch1 = [
            'sky',
            'tea leaves',
            'WalMart parking lot',
            'heavens',
            'attic',
            'depths of Tartarus'
        ]
        ch2 = [
            'eating it up',
            'vomiting profusely',
            'singing silly songs with Larry',
            'going wild',
            'sending death threats to their enemies',
            'cheering so loud the arena is caving in',
            'blackout drunk'
        ]

        bnnmsg += (f"Signs in the `{choice(ch1)}` show that every human is required to feel "
                   f"`{choice(emotions).lower()}` today! Otherwise the {ED.BARREL_EMOJI} might not like your style of "
                   f"`{choice(nouns).lower()}`. Life is short, so tell your `{choice(relationalterms)}` you "
                   f"`{choice(verbs).lower()}` them. `{choice(interjections).capitalize()}`!\n\nIn other news, the "
                   f"Intergalactic Badminton Tournament is going great! The `{choice(adjectives).lower()}` players "
                   f"are winning, and the `{choice(adjectives).lower()}` players are losing. Only `"
                   f"{randint(1, 1000)}` people have died so far today, and the fans are `{choice(ch2)}`!\n\n")

    elif msgtype == 3:

        bnnmsg += (f"We have some very special news for you today! Mr. `{choice(adjectives).capitalize()}` has decided "
                   f"he no longer wants his `{choice(nouns).lower()}`! Anybody who wants to `{choice(verbs).lower()}` "
                   f"it is welcome to come claim it. Offer valid for the next `{randint(0, 300)}` `"
                   f"{choice(['years', 'minutes', 'months', 'seconds', 'nanoseconds'])}`. Be warned, though, "
                   f"as it is rumored to hold the curse of `{choice(adjectives).lower()}` `"
                   f"{choice(nouns).lower()}s`!\n\nReports of loose `{choice(nouns).lower()}s` are flooding in today. "
                   f"Keep your `{choice(nouns).lower()}` `"
                   f"{choice(['inside', 'outside', 'locked away', 'sealed in the dark realm', 'on your roof'])}` this "
                   f"evening to prevent any trouble, as they're said to be `{choice(adjectives).lower()}` in their "
                   f"hunt for `{choice(nouns).lower()}`.\n\n")

    elif msgtype == 4:

        bnnmsg += (f"Today is an excellent day to praise the Almighty {ED.BARREL_EMOJI}! Great "
                   f"`{choice(nouns).lower()}s` have fallen upon our `{choice(nouns).lower()}s` and upon our "
                   f"`{choice(nouns).lower()}s`. Reports are saying that people who `{choice(verbs).lower()}` their "
                   f"`{choice(nouns).lower()}` to the {ED.BARREL_EMOJI} begin to feel `{choice(emotions).lower()}`! "
                   f"However, common side effects include feeling `{choice(emotions).lower()}`, "
                   f"`{choice(emotions).lower()}`, and `{choice(emotions).lower()}`. Please consult your `"
                   f"{choice(relationalterms)}` before attempting. `{choice(adjectives).capitalize()}` `"
                   f"{choice(nouns).lower()}s` may prevent you from the {ED.BARREL_EMOJI}'s grace.\n\n")

    elif msgtype == 5:

        place = choice([
            'Flavortown',
            'Modesto, CA',
            'South British Caltexico',
            'Siberia',
            'Wisconsahoma',
            'Upper Minneganderlis',
            'Funkytown',
            'The Kingdom of ' + choice(adjectives).capitalize() + ' ' + choice(nouns).capitalize() + 's',
            'The Soviet Union',
            'The Grand Duchy of Flandrensis',
            'The United Territories of the Sovereign Nation of The People\'s Republic of Slowjamastan',
            f'The {choice(adjectives).capitalize()} Empire'])
        criminal = choice(nouns).lower()
        ch1 = [
            'a',
            'b',
            'c',
            'x',
            'q',
            'f',
            'hm',
            '',
            'a93f',
            'f0',
            '#EF2B7C',
            'z',
            'zz',
            'zzz',
            'maj',
            'e',
            'y',
            'c',
            'b',
            'm'
        ]
        ch2 = [
            '5 years in prison',
            '10 years of community service',
            '1 night in the INFINITY ROOM',
            'a 30¢ fine'
        ]
        ch3 = ['mile', 'kilometer', 'millimeter', 'yard', 'parsec', 'nautical mile', 'furlong', 'cubit']

        bnnmsg += (f"A `{choice(adjectives).lower()} {criminal}` in `{place}` was arrested this morning after it was "
                   f"caught trying to `{choice(verbs).lower()}` in front of its `{choice(relationalterms)}`. Such an "
                   f"action is clearly prohibited under section `{randint(1, 99)}-{randint(1, 15)}"
                   f"{choice(ch1)}-{randint(100, 9999)}` of `{place}'s` criminal law. As such the `{criminal}` "
                   f"will face charges of up to `{choice(ch2)}` and all of their `{choice(nouns).lower()}s` will be "
                   f"sold and the money donated to `{choice(adjectives).capitalize()} {choice(nouns).capitalize()} "
                   f"{choice(nouns).capitalize()}` Enterprises, a for-profit charity benefitting the `"
                   f"{choice(adjectives).lower()}` ones in our community.\n\nToday is International `"
                   f"{choice(relationalterms).capitalize()}'s` Day. Show them you're thinking of them and `"
                   f"{choice(verbs).lower()}` a `{choice(nouns).lower()}` for them. Trust us, they'll love it! If you "
                   f"want to go the extra `{choice(ch3)}`, `{choice(verbs).lower()}` them a `{choice(nouns).lower()}` "
                   f"as well. They're sure to show `{choice(emotions).lower()}` at your gesture!\n\n")

    elif msgtype == 6:

        place = choice([
            'Flavortown',
            'Modesto, CA',
            'South British Caltexico',
            'Siberia',
            'Wisconsahoma',
            'Upper Minneganderlis',
            'Funkytown',
            'The Kingdom of ' + choice(adjectives).capitalize() + ' ' + choice(nouns).capitalize() + 's',
            'The Soviet Union',
            'The Grand Duchy of Flandrensis',
            'The United Territories of the Sovereign Nation of The People\'s Republic of Slowjamastan',
            f'The {choice(adjectives).capitalize()} Empire'
        ])
        boxstore = choice([
            'Wal-Mart',
            'Target',
            'IKEA',
            'Best Buy',
            'Costco',
            'LIDL hypermarket'
        ])
        attraction = choice([
            'pristine mountain valleys',
            'beautiful nature preserves',
            'ancient tar pits',
            'scorpion-infested rolling sand dunes',
            'idyllic pastures',
            'many vibrant hot springs',
            'amber waves of grain',
            'lush rainforests',
            'jaw-dropping waterfalls',
            'piranha-infested lakes',
            'towering sandstone arches'
        ])
        localquote = choice([
            f'I hate every single {boxstore} that has ever existed with every fiber of my being. I want nothing more '
            f'than to sabotage the personal and professional lives of every single executive and employee at '
            f'{boxstore}, then watch as their stock plummets into the ground, their lives fall apart, they lose every '
            f'loved one they ever had, and each and every one of them slowly descend into depression, madness, and '
            f'addiction.',
            'They\'re doing what now?? Darn, looks like I need to read the news more often.',
            f'I\'m actually the president of the local {attraction} fan club. We do a parade through town every year, '
            f'with the whole community getting involved. And I, for one, am on board with this change. {place} needs '
            f'some fresh views every once in a while, y\'know? An 18-lane superhighway would go so perfectly alongside '
            f'it, too.',
            f'Well, I can\'t say I\'m a huge fan of the notion. I do love wandering around those {attraction} every now and '
            f'then. But my {choice(relationalterms)} is an executive at the closest construction company, so I can\'t '
            f'say I want to keep him from that fat, gorgeous paycheck.',
            f'DEATH! TO! {boxstore.upper()}! DEATH! TO! {boxstore.upper()}! DEATH! TO! {boxstore.upper()}',
            f'I think it\'ll be great for our local economy. Prices have been getting up there, it\'s hard to '
            f'find good jobs, and I think a brand-new {boxstore} is going to fix all of those problems. I know some '
            f'folk are butthurt about it, but in my honest opinion? They\'re a bunch of weak, {choice(adjectives)} '
            f'losers who need to man up and get a real job. Then they\'ll understand.',
            f'YES I LOVE {boxstore.upper()}! I\'M A REAL ALPHA MALE AND ONLY BETAS HATE {boxstore.upper()}! THOSE WITH '
            f'REAL ALPHA ENERGY KNOW WE NEED TO ASSERT OUR DOMINANCE OVER NATURE AND EVERYTHING ELSE ALL THE TIME!!! '
            f'FOLLOW MY PODCAST ON INSTAGRAM!!!!!!!',
            f'HIIIIII OMG ARE YOU A REAL NEWSPERSON??????? YES I\'D LOVE TO TALK!!!!!! HIIII PEOPLE IN THE NEWS!!!!!!! '
            f'(✧ω✧) Oh the thing about the {boxstore}?? I don\'t know.... I love nature so much!!!! ❀.(*´◡`*)❀ But I '
            f'also love shopping so much...... (❁ᴗ͈ˬᴗ͈) OMG I can\'t decide!!!!! (*≧ω≦)',
            f'.........are you talking to me? Go away. I don\'t care.'
        ])
        person = choice([
            "man",
            "woman",
            "non-binary person",
            "shriveled old grandma",
            "newborn infant",
            "strapping young man",
            "humanoid eldritch being",
            "girl in the skate park",
            "disgustingly dirty, filthy, wretched old man"
        ])

        bnnmsg += (f"Certain `{choice(adjectives).lower()}` lobbyists are currently pushing for the construction of a "
                   f"`{boxstore}` in `{place}`. Tourists and locals alike enjoy `{place}` for its `{attraction}`, but "
                   f"this new construction would bulldoze over all of it and replace it with a `{randint(100, 1000)},"
                   f"000` `{choice(['sq. ft.', 'm2', 'sq. mile', 'acre', 'hectare'])}` `{boxstore}` full of `"
                   f"{choice(nouns).lower()}s`, `{choice(nouns).lower()}s`, and `{choice(nouns).lower()}s`.\n\nTo "
                   f"understand the situation better, we interviewed the locals. One `{person}` said, "
                   f"\"`{localquote}`\"\n\n")

    ch1 = [
        'polar bears',
        'steel hail',
        'severe sharknadoes',
        'chemtrails',
        'frozen cats',
        'plagues caused by advanced bioweapons',
        'astronaut suits falling from space',
        'occasional stray muon beams',
        'elves that escaped from Santa\'s workshop',
        'ice dragons',
        'liquid ammonia rain',
        'adorable cat smiles',
        'francophones',
        'neo-nazi zombies',
        'sentient crab rain',
        'SNAKES!',
        'freezing rain',
        'spontaneously-forming black holes',
        'giant tumbleweeds',
        'your mom',
        'the heat death of the universe',
        'impending doom',
        'tentacles',
        'cute anime catgirls',
        'arranged marriages',
        'pink fluffy unicorns dancing on rainbows',
        'bronies',
        'that one family member (yes, that one)',
        'stray mitochondria (the powerhouse of the cell!)',
        'Larry the Cucumber from VeggieTales'
    ]
    ch2 = [
        'along the east coast',
        'along the west coast',
        'near the entrance to Anubis\' realm',
        'around Olympus Mons',
        'at the beaches in France',
        'in any part of the world with bacteria',
        'off the Arctic coast',
        'on the Bridge to Asgard',
        'along the outskirts of Detroit',
        'where the sidewalk ends',
        'where your great aunt Marge broke her coccyx',
        'wherever you last ate chocolate ice cream',
        'in your bathroom',
        'in your mind',
        'at your local grocery store!',
        'hiding in your lasagna',
        'in places where the sun don\'t shine']

    bnnmsg += (f"The weather today on earth will be `{choice(adjectives).lower()}`, with a high of `{rand_temp()}`°C "
               f"and a low of `{rand_temp()}`°F. Watch out for `{choice(ch1)}` `{choice(ch2)}`. The "
               f"`{choice(nouns).capitalize()}` also predicts the weather is going to `"
               f"{choice(verbs).lower()}` even more tonight than yesterday. `"
               f"{choice(interjections).capitalize()}`!\n\nThat's all for today! Barrelbot, signing off. \n"
               f"{days_since_reveal} days since PS reveal \n<@&{env.BBGLOBALS.BARREL_SUB_ROLE_ID}>")

    return bnnmsg


reminders = [
    env.BBGLOBALS.BARREL_REP_MENTION + " don't forget to do daily " + ED.BARREL_EMOJI +
    " news! If you haven't done it <t:{}:R> I'll have to do it myself.",
    env.BBGLOBALS.BARREL_REP_MENTION + "! News! Soon! You have until <t:{}:t>!",
    "Hey " + env.BBGLOBALS.BARREL_REP_MENTION +
    "! Don't forget about the news today! The deadline is the same as it always is: <t:{}:t>",
    "Once upon a time, our beloved " + env.BBGLOBALS.BARREL_REP_MENTION + " would forget to do daily " +
    ED.BARREL_EMOJI +
    " news. But then I came along and prevented such a horrible tragedy. Hopefully that doesn't happen today...",
    env.BBGLOBALS.BARREL_REP_MENTION + ": <t:{}:t>",
    env.BBGLOBALS.BARREL_REP_MENTION +
    "\nG-guys can someone p-lease do the news for meeeeee? 🤓 I-it would really m-make my d-day...",
    "Hewwo my deawest " + env.BBGLOBALS.BARREL_REP_MENTION +
    "! I would weally wove it if you did youw news wepowt :3 Nofing would make me happiew! Would you do it fow me??? "
    ":pleading_face:",
    "Greetings loyal " + ED.BARREL_EMOJI + " cultists. May the " + ED.BARREL_EMOJI +
    " smile upon you. We are currently awaiting the blessed deliverance of news from our esteemed " +
    env.BBGLOBALS.BARREL_REP_MENTION + ". Until then, please refrain from rioting in the streets. Good day.",
    env.BBGLOBALS.BARREL_REP_MENTION + "\n" + ED.BARREL_EMOJI * 20,
    env.BBGLOBALS.BARREL_REP_MENTION + "\n" + ED.BARREL_EMOJI * 50,
    env.BBGLOBALS.BARREL_REP_MENTION + " more like @Barrel news reporters! Am I right? No? Ok, I'll show myself out...",
    "Glory be to the " + ED.BARREL_EMOJI + "! May all the earth shout for joy! May today's " + ED.BARREL_EMOJI +
    " news be plentiful and great! May this day that ends <t:{}:R> see incredible " + ED.BARREL_EMOJI +
    " news! May the " + ED.BARREL_EMOJI + " be praised! May the " + env.BBGLOBALS.BARREL_REP_MENTION +
    " not forget to grant us our daily blessings!",
    ED.BARREL_EMOJI + " " + env.BBGLOBALS.BARREL_REP_MENTION + " " + ED.BARREL_EMOJI + "\n" + ED.BARREL_EMOJI +
    " <t:{}:F> " + ED.BARREL_EMOJI,
    "Our " + ED.BARREL_EMOJI + " who art in " + ED.BARREL_EMOJI + ". Hallowed be thy " + ED.BARREL_EMOJI + ". Thy " +
    ED.BARREL_EMOJI + "come. Thy will be done on earth, as it is in " + ED.BARREL_EMOJI +
    ". Give us this day our daily " + ED.BARREL_EMOJI + " news. Amen. \n" + env.BBGLOBALS.BARREL_REP_MENTION,
    "Me when the " + env.BBGLOBALS.BARREL_REP_MENTION + " do the daily " + ED.BARREL_EMOJI +
    " news: <:barrelconfetti:1316102028253991003>\nMe when they forget: <:agonybarrel:1313267644933083296>",
    "TODAY ON BNN: The " + ED.BARREL_EMOJI + " created the heaven and the earth. Wait, that was forever ago... " +
    env.BBGLOBALS.BARREL_REP_MENTION + " can you update it?",
    ED.BARREL_EMOJI * 20 + "\n" + env.BBGLOBALS.BARREL_REP_MENTION + "\n" + ED.BARREL_EMOJI * 20,
    "<t:{}:R> the day will be over and we shall be left alone, without the guiding light of daily " +
    ED.BARREL_EMOJI + " news. That is, unless the " + env.BBGLOBALS.BARREL_REP_MENTION +
    " deign us worthy of such a blessing.",
    "Hewwo!!! :3 I am bawwewbot and I am hewe to wemind da " + env.BBGLOBALS.BARREL_REP_MENTION +
    " to do deiw daiwy bawwew news!!! :heart_eyes_cat: :blush: <3 <3 uwu ^w^",
    env.BBGLOBALS.BARREL_REP_MENTION +
    "\n中國早上好！現在我有冰淇淋。我真的很喜歡冰淇淋，但是，速度與激情 9，與速度與激情 9 相比，我最喜歡。所以，現在是音樂時間。準備好。 1, 2, "
    "3.整整兩週後，速度與激情9，整整兩週後，速度與激情9，整整兩週後，速度與激情9。不要忘記，不要錯過它。去電影院看《速度與激情9》，"
    "這是一部很棒的電影！動作很棒，比如“我會尖叫”。再見。",
]
