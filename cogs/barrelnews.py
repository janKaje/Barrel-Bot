import os
import datetime as dt
from random import choice, randint

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
BARREL_REP_MENTION = f"<@&{BARREL_REP_ROLE_ID}>"
BARREL_SUB_MENTION = f"<@&{BARREL_SUB_ROLE_ID}>"

remind_time = dt.time(hour=REMINDER_TIME[0], minute=REMINDER_TIME[1], tzinfo=dt.timezone.utc)
deadline_time = dt.time(hour=DEADLINE_TIME[0], minute=DEADLINE_TIME[1], tzinfo=dt.timezone.utc)


reminders = [
    BARREL_REP_MENTION + " don't forget to do daily " + BARREL_EMOJI + " news! If you haven't done it <t:{}:R> I'll have to do it myself.",
    BARREL_REP_MENTION + "! News! Soon! You have until <t:{}:t>!",
    "Hey " + BARREL_REP_MENTION + "! Don't forget about the news today! The deadline is the same as it always is: <t:{}:t>",
    "Once upon a time, our beloved " + BARREL_REP_MENTION + " would forget to do daily " + BARREL_EMOJI + " news. But then I came along and prevented such a horrible tragedy. Hopefully that doesn't happen today...",
    BARREL_REP_MENTION + ": <t:{}:t>",
    BARREL_REP_MENTION + "\nG-guys can someone p-lease do the news for meeeeee? 🤓 I-it would really m-make my d-day...",
    "Hewwo my deawest " + BARREL_REP_MENTION + "! I would weally wove it if you did youw news wepowt :3 Nofing would make me happiew! Would you do it fow me??? :pleading_face:",
    "Greetings loyal " + BARREL_EMOJI + " cultists. May the " + BARREL_EMOJI + " smile upon you. We are currently awaiting the blessed deliverance of news from our esteemed " + BARREL_REP_MENTION + ". Until then, please refrain from rioting or making fart noises with your armpits. Good day.",
    BARREL_REP_MENTION + "\n" + BARREL_EMOJI*20,
    BARREL_REP_MENTION + "\n" + BARREL_EMOJI*50,
    BARREL_REP_MENTION + " more like @Barrel news reporters! Am I right? No? Ok, I'll show myself out...",
    "Glory be to the " + BARREL_EMOJI + "! May all the earth shout for joy! May today's " + BARREL_EMOJI + " news be plentiful and great! May this day that ends <t:{}:R> see incredible " + BARREL_EMOJI + " news! May the " + BARREL_EMOJI + " be praised! May the " + BARREL_REP_MENTION + " not forget to grant us our daily blessings!",
    BARREL_EMOJI + " " + BARREL_REP_MENTION + " " + BARREL_EMOJI + "\n" + BARREL_EMOJI + " <t:{}:F> " + BARREL_EMOJI,
    "Our " + BARREL_EMOJI + " who art in " + BARREL_EMOJI + ". Hallowed be thy " + BARREL_EMOJI + ". Thy " + BARREL_EMOJI + "come. Thy will be done on earth, as it is in " + BARREL_EMOJI + ". Give us this day our daily " + BARREL_EMOJI + " news. Amen. \n" + BARREL_REP_MENTION,
    "Me when the " + BARREL_REP_MENTION + " do the daily " + BARREL_EMOJI + " news: <:barrelconfetti:1316102028253991003>\nMe when they forget: <:agonybarrel:1313267644933083296>",
    "TODAY ON BNN: The " + BARREL_EMOJI + " created the heaven and the earth. Wait, that was forever ago... " + BARREL_REP_MENTION + " can you update it?",
    BARREL_EMOJI*20 + "\n" + BARREL_REP_MENTION + "\n" + BARREL_EMOJI*20,
    "<t:{}:R> the day will be over and we shall be left alone, without the guiding light of daily " + BARREL_EMOJI + " news. That is, unless the " + BARREL_REP_MENTION + " deign us worthy of such a blessing.",
    "Hewwo!!! :3 I am bawwewbot and I am hewe to wemind da " + BARREL_REP_MENTION + " to do deiw daiwy bawwew news!!! :heart_eyes_cat: :blush: <3 <3 uwu ^w^",
    BARREL_REP_MENTION,
    BARREL_REP_MENTION + "\n中國早上好！現在我有冰淇淋。我真的很喜歡冰淇淋，但是，速度與激情 9，與速度與激情 9 相比，我最喜歡。所以，現在是音樂時間。準備好。 1, 2, 3.整整兩週後，速度與激情9，整整兩週後，速度與激情9，整整兩週後，速度與激情9。不要忘記，不要錯過它。去電影院看《速度與激情9》，這是一部很棒的電影！動作很棒，比如“我會尖叫”。再見。",
]

emotions = [
    "Acceptance",    "Acedia",    "Adoration",    "Affect labeling",
    "Affect regulation",    "Affection",    "Ambivalence",    "Anger",
    "Angst",    "Anguish",    "Annoyance",    "Anticipation",
    "Antipathy",    "Anxiety",    "Apathy",    "Arousal",
    "Aversion to happiness",    "Awe",    "Boredom",    "Broken heart",
    "Calmness",    "Compassion",    "Complaining",    "Condescension",
    "Confidence",    "Confusion",    "Contempt",    "Contentment",
    "Contrition",    "Courage",    "Creepiness",    "Cute aggression",
    "Defeatism",    "Depression",    "Desire",    "Despair",
    "Disappointment",    "Disgust",    "Doubt",    "Dysphoria",
    "Ecstasy",    "Embarrassment",    "Empathy",    "Emptiness",
    "Enthusiasm",    "Envy",    "Escapism",    "Euphoria",
    "Exhilaration",    "Fear",    "Forgiveness",    "Frustration",
    "Gloom",    "Gratitude",    "Grief",    "Guilt",
    "Happiness",    "Hatred",    "Homesickness",    "Hope",
    "Hostility",    "Humiliation",    "Hysteria",    "Indignation",
    "Infatuation",    "Insecurity",    "Insignificance",    "Insult",
    "Interest",    "Invidia",    "Irritability",    "Isolation",
    "Jealousy",    "Joy",    "Kama muta",    "Kindness",
    "Limerence",    "Loneliness",    "Love",    "Loyalty",
    "Lust",    "Malaise",    "Melancholia",    "Mimpathy",
    "Mono no aware",    "Mudita",    "Museum fatigue",    "Nostalgia",
    "Outrage",    "Panic",    "Passion",    "Passionate and companionate love",
    "Pathological jealousy",    "Patience",    "Pessimism",    "Pity",
    "Pleasure",    "Pride",    "Quixotism",    "Rage",
    "Regret",    "Relaxation",    "Relief",    "Remorse",
    "Resentment",    "Reverence",    "Ridiculous",    "Righteous indignation",
    "Rock fever",    "Romance",    "Runner's high",    "Sadness",
    "Saudade",    "Sehnsucht",    "Self-pity",    "Sense of wonder",
    "Sentimentality",    "Seriousness",    "Shame",    "Shyness",
    "Silliness",    "Sincerity",    "Solitude",    "Sorrow",
    "Spite",    "Surprise",    "Suspense",    "Suspicion",
    "Sympathy",    "The ick",    "Trust",    "Valence",
    "Vicarious embarrassment",    "Won",    "Wonder",    "Worry",
    "Zest",
]

verbs = [
    "be", "keep", "understand",
    "have", "let", "watch",
    "do", "begin", "follow",
    "say", "seem", "stop",
    "go", "help", "create",
    "can", "talk", "speak",
    "get", "turn", "read",
    "would", "start", "allow",
    "make", "might", "add",
    "know", "show", "spend",
    "will", "hear", "grow",
    "think", "play", "open",
    "take", "run", "walk",
    "see", "move", "win",
    "come", "like", "offer",
    "could", "live", "remember",
    "want", "believe", "love",
    "look", "hold", "consider",
    "use", "bring", "appear",
    "find", "happen", "buy",
    "give", "must", "wait",
    "tell", "write", "serve",
    "work", "provide", "die",
    "may", "sit", "send",
    "should", "stand", "expect",
    "call", "lose", "build",
    "try", "pay", "stay",
    "ask", "meet", "fall",
    "need", "include", "cut",
    "feel", "continue", "reach",
    "become", "set", "kill",
    "leave", "learn", "remain",
    "put", "change",
    "mean", "lead",
]

adjectives = [
    "other", "major", "natural",
    "new", "better", "significant",
    "good", "economic", "similar",
    "high", "strong", "hot",
    "old", "possible", "dead",
    "great", "whole", "central",
    "big", "free", "happy",
    "American", "military", "serious",
    "small", "true", "ready",
    "large", "federal", "simple",
    "national", "international", "left",
    "young", "full", "physical",
    "different", "special", "general",
    "black", "easy", "environmental",
    "long", "clear", "financial",
    "little", "recent", "blue",
    "important", "certain", "democratic",
    "political", "personal", "dark",
    "bad", "open", "various",
    "white", "red", "entire",
    "real", "difficult", "close",
    "best", "available", "legal",
    "right", "likely", "religious",
    "social", "short", "cold",
    "only", "single", "final",
    "public", "medical", "main",
    "sure", "current", "green",
    "low", "wrong", "nice",
    "early", "private", "huge",
    "able", "past", "popular",
    "human", "foreign", "traditional",
    "local", "fine", "cultural",
    "late", "common",
    "hard", "poor",
]

nouns = [
    "time", "room", "president",
    "year", "mother", "team",
    "people", "area", "minute",
    "way", "money", "idea",
    "day", "story", "kid",
    "man", "fact", "body",
    "thing", "month", "information",
    "woman", "lot", "back",
    "life", "right", "parent",
    "child", "study", "face",
    "world", "book", "others",
    "school", "eye", "level",
    "state", "job", "office",
    "family", "word", "door",
    "student", "business", "health",
    "group", "issue", "person",
    "country", "side", "art",
    "problem", "kind", "war",
    "hand", "head", "history",
    "part", "house", "party",
    "place", "service", "result",
    "case", "friend", "change",
    "week", "father", "morning",
    "company", "power", "reason",
    "system", "hour", "research",
    "program", "game", "girl",
    "question", "line", "guy",
    "work", "end", "moment",
    "government", "member", "air",
    "number", "law", "teacher",
    "night", "car", "force",
    "point", "city", "Education",
    "home", "community",
    "water", "name",
]


interjections = [
    "ah", "ah", "er", "ew", "ha", "ho", "oh", "oi", "ow", "oy",
    "aha", "aww", "aya" 'boo' "eek", "gee", "hey", "huh", "mmm", "shh", "tut", "ugh", "wow", "yay", "yuk",
    "ahem", "darn", "d'oh", "egad", "gosh", "hmmm", "hmph", "oops", "ouch", "phew", "psst", "shoo", "sigh", "well", "whee", "whoa", "woah", "yeah", "yuck",
    "aargh", "blast", "bravo", "golly", "ha ha", "howdy", "lordy", "oh my", "oh no", "scram", "ta-da", "uh-ho", "yahoo", "yikes", "zowie",
    "cheers", "crikey", "eureka", "ho hum", "hooray", "hurrah", "indeed", "my bad", "no way", "oh boy", "please", "really", "thanks", "yippee",
    "hang on", "hee hee", "hot dog" 'jeepers' "jinkies", "oh dear", "oh well", "so long", "tee hee", "tsk tsk", "tsk tsk", "woo-hoo", "you bet",
    "gadzooks", "gee whiz", "hi there", "holy cow", "let's go", "look out", "mercy me", "oh goody", "silly me", "time out",
    "bless you", "not again", "pardon me", "take that", "that's it", "well done", "wonderful",
    "good grief", "hallelujah", "oh my gosh",
    "great scott", "holy smokes", "holy toledo", "my goodness",
    "fiddlesticks",
    "holy mackerel",
    "jiminy cricket", "thank goodness",
    "congratulations",
]


relationalterms = [
    "mother", "father", "parent", "grandmother", "grandfather", "grandparent", "uncle", "aunt",
    "brother", "sister", "sibling", "son", "daughter", "child", "children", "cousin",
    "husband", "wife", "spouse", "fiancé", "fiancée", "father-in-law", "mother-in-law",
    "brother-in-law", "sister-in-law", "son-in-law", "daughter-in-law", "stepmother", "stepfather", "stepsister", "stepbrother",
    "half-sister", "half-brother", "godfather", "godmother", "legal guardian", "acquaintance", "friend", "partner",
    "buddy", "mate", "best friend", "frenemy", "BFF", "enemy", "adversary", "stranger", "associate", "colleague",
    "ally", "comrade", "companion", "pal"
]


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
        days_since_reveal = (dt.date.today() - dt.date(year=2024, month=1, day=25)).days - 1
        days_of_bnn = days_since_reveal - 266 - 6 #6 days missed?

        outstr = f"Previous deadline: <t:{int(prev_d.timestamp())}>, or <t:{int(prev_d.timestamp())}:R>\n" +\
                 f"Next deadline: <t:{int(next_d.timestamp())}>, or <t:{int(next_d.timestamp())}:R>\n" +\
                 f"Already done for today: {already}\n" +\
                 f"Days since PS reveal: {days_since_reveal}\n" +\
                 f"Day of BNN: {days_of_bnn}"

        await ctx.send(outstr)

    @commands.command()
    @commands.is_owner()
    async def test_reminder(self, ctx: commands.Context):

        remindmsg = self.get_reminder()

        await ctx.send(remindmsg)

    @commands.command()
    @commands.is_owner()
    async def test_bnnmsg(self, ctx: commands.Context):

        for i in [1,2,3,4]:

            bnnmsg = self.get_bnnmsg(i)

            await ctx.send(bnnmsg)

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

        msgtype = randint(1, 4)

        bnnmsg = self.get_bnnmsg(msgtype)

        await self.news_channel.send(bnnmsg)

    async def cog_load(self):

        self.news_channel:discord.TextChannel = await self.bot.fetch_channel(BARREL_NEWS_CHANNEL_ID)

        self.remind_loop.start()
        self.post_loop.start()

    async def check_if_already_posted(self) -> bool:

        # get previous deadline
        prev_deadline = self.get_deadline(prev=True) + dt.timedelta(hours=1) # one hour grace period between one deadline and start of next day

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
        
    def get_reminder(self):

        next_deadline = self.get_deadline(prev=False)

        remindmsg = choice(reminders)

        try:
            remindmsg = remindmsg.format(int(next_deadline.timestamp()))
        except:
            pass

        return remindmsg
    
    def get_bnnmsg(self, msgtype):
        
        days_since_reveal = (dt.date.today() - dt.date(year=2024, month=1, day=25)).days - 1
        days_of_bnn = days_since_reveal - 266 - 6 #6 days missed?

        bnnmsg = f"# TODAY\n## ON BNN\nWelcome to day {days_of_bnn} of bringing you your daily {BARREL_EMOJI} news! I'm your host, Barrelbot, "\
                 f"here to bring you your randomly-generated news for today.\n\n"

        if msgtype == 1:

            bnnmsg += f"Today the {BARREL_EMOJI} is feeling some `{choice(emotions).lower()}`, so please take that into account when you `{choice(verbs)}` your `{choice(nouns)}` today. "\
                      f"It may also affect the way that you choose to `{choice(verbs)}`. \n\n"\
                      f"New research shows that `{choice(adjectives)}` `{choice(nouns)}` is `{choice(adjectives)}` to some `{choice(nouns)}`s! So be sure to `{choice(verbs)}` as much as you can today.\n\n"
            
        elif msgtype == 2:

            bnnmsg += f"Signs in the sky show that every human is required to feel `{choice(emotions).lower()}` today! Otherwise the {BARREL_EMOJI} might not like your style of `{choice(nouns)}`. "\
                      f"Life is short, so tell your `{choice(relationalterms)}` you `{choice(verbs)}` them. `{choice(interjections).capitalize()}`!\n\n"\
                      f"In other news, the Intergalactic Badminton Tournament is going great! The `{choice(adjectives)}` players are winning, and the `{choice(adjectives)}` players are losing. "\
                      f"Only `{randint(1, 1000)}` people have died so far today, and the fans are eating it up!\n\n"
            
        elif msgtype == 3:

            bnnmsg += f"We have some very special news for you today! Mr. `{choice(adjectives).capitalize()}` has decided he no longer wants his `{choice(nouns)}`! Anybody who wants to `{choice(verbs)}` it "\
                      f"is welcome to come claim it. Offer valid for the next `{randint(0, 300)}` `{choice(['years', 'minutes', 'months', 'seconds', 'nanoseconds'])}`. "\
                      f"Be warned, though, as it is rumored to `{choice(verbs)}` the curse of `{choice(adjectives)} {choice(nouns)}`s!\n\n"
            
        else:

            bnnmsg += f"Today is an excellent day to praise the Almighty {BARREL_EMOJI}! Great blessings have fallen upon our `{choice(nouns)}`s and upon our `{choice(nouns)}`s. "\
                      f"Reports are saying that people who `{choice(verbs)}` their `{choice(nouns)}` to the {BARREL_EMOJI} begin to feel `{choice(emotions).lower()}`! "\
                      f"However, common side effects include feeling `{choice(emotions).lower()}`, `{choice(emotions).lower()}`, and `{choice(emotions).lower()}`. "\
                      f"Please consult your `{choice(nouns)}` before attempting. `{choice(adjectives).capitalize()} {choice(nouns)}` may prevent you from the {BARREL_EMOJI}'s grace.\n\n"

        bnnmsg += f"The weather today on earth will be `{choice(adjectives)}`, with a high of `{randint(0, 1000)}`°C and a low of `{randint(-1000, 1000)}`°F. Watch out for "\
                  f"`{choice(['polar bears', 'steel hail', 'severe sharknadoes', 'chemtrails', 'frozen cats', 'plagues caused by advanced bioweapons', 'astronaut suits falling from space', 'occasional stray muon beams', 'elves that escaped from Santa'+chr(39)+'s workshop', 'ice dragons', 'liquid ammonia rain', 'adorable cat smiles', 'francophones', 'neo-nazi zombies', 'sentient crab rain', 'SNAKES!', 'freezing rain', 'spontaneously-forming black holes', 'giant tumbleweeds', 'your mom', 'the heat death of the universe', 'impending doom', 'tentacles', 'cute anime catgirls', 'arranged marriages', 'pink fluffy unicorns dancing on rainbows', 'bronies', 'that one family member (yes, that one)', 'stray mitochondria (the powerhouse of the cell!)', 'Larry the Cucumber from VeggieTales'])}` "\
                  f"`{choice(['along the east coast', 'along the west coast', 'near the entrance to Anubis'+chr(39)+' realm', 'around Olympus Mons', 'at the beaches in France', 'in any part of the world with bacteria', 'off the Arctic coast', 'on the Bridge to Asgard', 'along the outskirts of Detroit', 'where the sidewalk ends', 'where your great aunt Marge broke her coccyx', 'wherever you last ate chocolate ice cream', 'in your bathroom', 'in your mind', 'at your local grocery store!', 'hiding in your lasagna', 'in places where the sun don'+chr(39)+'t shine'])}`. "\
                  f"Stay safe out there, folks, because the weather is about to `{choice(verbs)}` even more tonight than yesterday. `{choice(interjections).capitalize()}`!\n\n"\
                  f"That's all for today! Barrelbot, signing off. \n{days_since_reveal} days since PS reveal \n<@&{BARREL_SUB_ROLE_ID}>"
        
        return bnnmsg
