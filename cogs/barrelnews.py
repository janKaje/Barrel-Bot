import os
import datetime as dt
from random import choice, randint, random
from math import floor

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
    async def test_bnnmsg(self, ctx: commands.Context, msgtype: str):

        try:
            await ctx.send(self.get_bnnmsg(int(msgtype)))
        except:
            msgtype = randint(1, 5)
            await ctx.send(self.get_bnnmsg(msgtype))


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

        msgtype = randint(1, 5)

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
            if not message.author.bot and str(BARREL_SUB_MENTION) in message.content:
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
                 f"here to bring you your randomly-generated, `{choice(adjectives).lower()}` news for today.\n\n"

        if msgtype == 1:

            bnnmsg += f"Today the {BARREL_EMOJI} is feeling some `{choice(emotions).lower()}`, so please take that into account when you `{choice(verbs).lower()}` your `{choice(nouns).lower()}` today. "\
                      f"It may also affect the way that you choose to `{choice(verbs).lower()}`. \n\n"\
                      f"New research shows that a `{choice(adjectives).lower()}` `{choice(nouns).lower()}` is `{choice(adjectives).lower()}` to some `{choice(nouns).lower()}s`! So be sure to `{choice(verbs).lower()}` as much as you can today. "\
                      f"That way you can be sure `{choice(['this week'+chr(39)+'s episode of', 'your mom'+chr(39)+'s favorite', 'every single', 'Benadryl Cucumberpatch'+chr(39)+'s', 'the warm, toasty', 'the wretched', 'my'])}` "\
                      f"`{choice(['eye patch', 'Reddit account', 'vtuber alter ego', 'butler', 'exploding beach ball', 'weapons-grade plutonium', 'oil refinery', 'sled pulled by rabid opossoms', '3-inch tungsten cube', 'antique chandelier', 'T6 Series 1000W AC Servo Motor Kit', 'LORELEI S9 Wired Headphones with Microphone for School，On-Ear Kids Headphones for Girls Boys，Folding Lightweight and 3.5mm Audio Jack Headset for Phone, Ipad，Tablet, PC, Chromebook (Pearl Pink)'])}` "\
                      f"stays `{choice(adjectives).lower()}` and `{choice(adjectives).lower()}`!\n\n"
            
        elif msgtype == 2:

            bnnmsg += f"Signs in the `{choice(['sky', 'tea leaves', 'WalMart parking lot', 'heavens', 'attic', 'depths of Tartarus'])}` show that every human is required to feel `{choice(emotions).lower()}` today! Otherwise the {BARREL_EMOJI} might not like your style of `{choice(nouns).lower()}`. "\
                      f"Life is short, so tell your `{choice(relationalterms)}` you `{choice(verbs).lower()}` them. `{choice(interjections).capitalize()}`!\n\n"\
                      f"In other news, the Intergalactic Badminton Tournament is going great! The `{choice(adjectives).lower()}` players are winning, and the `{choice(adjectives).lower()}` players are losing. "\
                      f"Only `{randint(1, 1000)}` people have died so far today, and the fans are `{choice(['eating it up', 'vomiting profusely', 'singing silly songs with Larry', 'going wild', 'sending death threats to their enemies', 'cheering so loud the arena is caving in', 'blackout drunk'])}`!\n\n"
            
        elif msgtype == 3:

            bnnmsg += f"We have some very special news for you today! Mr. `{choice(adjectives).capitalize()}` has decided he no longer wants his `{choice(nouns).lower()}`! Anybody who wants to `{choice(verbs).lower()}` it "\
                      f"is welcome to come claim it. Offer valid for the next `{randint(0, 300)}` `{choice(['years', 'minutes', 'months', 'seconds', 'nanoseconds'])}`. "\
                      f"Be warned, though, as it is rumored to hold the curse of `{choice(adjectives).lower()}` `{choice(nouns).lower()}s`!\n\n"\
                      f"Reports of loose `{choice(nouns).lower()}s` are flooding in today. Keep your `{choice(nouns).lower()}` `{choice(['inside', 'outside', 'locked away', 'sealed in the dark realm', 'on your roof'])}` this evening to prevent any trouble, "\
                      f"as they're said to be `{choice(adjectives).lower()}` in their hunt for `{choice(nouns).lower()}`.\n\n"
            
        elif msgtype == 4:

            bnnmsg += f"Today is an excellent day to praise the Almighty {BARREL_EMOJI}! Great `{choice(nouns).lower()}s` have fallen upon our `{choice(nouns).lower()}s` and upon our `{choice(nouns).lower()}s`. "\
                      f"Reports are saying that people who `{choice(verbs).lower()}` their `{choice(nouns).lower()}` to the {BARREL_EMOJI} begin to feel `{choice(emotions).lower()}`! "\
                      f"However, common side effects include feeling `{choice(emotions).lower()}`, `{choice(emotions).lower()}`, and `{choice(emotions).lower()}`. "\
                      f"Please consult your `{choice(relationalterms)}` before attempting. `{choice(adjectives).capitalize()}` `{choice(nouns).lower()}s` may prevent you from the {BARREL_EMOJI}'s grace.\n\n"

        elif msgtype == 5:

            place = choice(['Flavortown', 'Modesto, CA', 'South British Caltexico', 'Siberia', 'Wisconsahoma', 'Upper Minneganderlis', 'Funkytown', 'The Kingdom of ' + choice(adjectives).capitalize() + ' ' + choice(nouns).capitalize() + 's', 'The Soviet Union', 'The Grand Duchy of Flandrensis', 'The United Territories of the Sovereign Nation of The People\'s Republic of Slowjamastan', f'The {choice(adjectives).capitalize()} Empire'])
            criminal = choice(nouns).lower()

            bnnmsg += f"A `{choice(adjectives).lower()} {criminal}` in `{place}` was arrested this morning after it was caught trying to `{choice(verbs).lower()}` "\
                      f"in front of its `{choice(relationalterms)}`. Such an action is clearly prohibited under section `{randint(1,99)}-{randint(1,15)}{choice(['a','b','c','x','q','f','hm','','a93f','f0','#EF2B7C','z','zz','zzz','maj','e','y','c','b','m'])}-{randint(100,9999)}` of `{place}'s` criminal law. "\
                      f"As such the `{criminal}` will face charges of up to `{choice(['5 years in prison', '10 years of community service', '1 night in the _**I N F I N I T Y   R O O M**_', 'a 30¢ fine'])}` and all of their `{choice(nouns).lower()}s` will be sold and the money donated to `{choice(adjectives).capitalize()} {choice(nouns).capitalize()} {choice(nouns).capitalize()}` Enterprises, "\
                      f"a for-profit charity benefitting the `{choice(adjectives).lower()}` ones in our community.\n\n"\
                      f"Today is International `{choice(relationalterms).capitalize()}'s` Day. Show them you're thinking of them and `{choice(verbs).lower()}` a `{choice(nouns).lower()}` for them. Trust us, they'll love it! "\
                      f"If you want to go the extra `{choice(['mile', 'kilometer', 'millimeter', 'yard', 'parsec', 'nautical mile', 'furlong', 'cubit'])}`, `{choice(verbs).lower()}` them a `{choice(nouns).lower()}` as well. They're sure to show `{choice(emotions).lower()}` at your gesture!\n\n"

        bnnmsg += f"The weather today on earth will be `{choice(adjectives).lower()}`, with a high of `{rand_temp()}`°C and a low of `{rand_temp()}`°F. Watch out for "\
                  f"`{choice(['polar bears', 'steel hail', 'severe sharknadoes', 'chemtrails', 'frozen cats', 'plagues caused by advanced bioweapons', 'astronaut suits falling from space', 'occasional stray muon beams', 'elves that escaped from Santa'+chr(39)+'s workshop', 'ice dragons', 'liquid ammonia rain', 'adorable cat smiles', 'francophones', 'neo-nazi zombies', 'sentient crab rain', 'SNAKES!', 'freezing rain', 'spontaneously-forming black holes', 'giant tumbleweeds', 'your mom', 'the heat death of the universe', 'impending doom', 'tentacles', 'cute anime catgirls', 'arranged marriages', 'pink fluffy unicorns dancing on rainbows', 'bronies', 'that one family member (yes, that one)', 'stray mitochondria (the powerhouse of the cell!)', 'Larry the Cucumber from VeggieTales'])}` "\
                  f"`{choice(['along the east coast', 'along the west coast', 'near the entrance to Anubis'+chr(39)+' realm', 'around Olympus Mons', 'at the beaches in France', 'in any part of the world with bacteria', 'off the Arctic coast', 'on the Bridge to Asgard', 'along the outskirts of Detroit', 'where the sidewalk ends', 'where your great aunt Marge broke her coccyx', 'wherever you last ate chocolate ice cream', 'in your bathroom', 'in your mind', 'at your local grocery store!', 'hiding in your lasagna', 'in places where the sun don'+chr(39)+'t shine'])}`. "\
                  f"The `{choice(nouns).capitalize()}` also predicts the weather is going to `{choice(verbs).lower()}` even more tonight than yesterday. `{choice(interjections).capitalize()}`!\n\n"\
                  f"That's all for today! Barrelbot, signing off. \n{days_since_reveal} days since PS reveal \n<@&{BARREL_SUB_ROLE_ID}>"
        
        return bnnmsg


def rand_temp():
    rand = random()*3.5
    return floor(10**rand)

reminders = [
    BARREL_REP_MENTION + " don't forget to do daily " + BARREL_EMOJI + " news! If you haven't done it <t:{}:R> I'll have to do it myself.",
    BARREL_REP_MENTION + "! News! Soon! You have until <t:{}:t>!",
    "Hey " + BARREL_REP_MENTION + "! Don't forget about the news today! The deadline is the same as it always is: <t:{}:t>",
    "Once upon a time, our beloved " + BARREL_REP_MENTION + " would forget to do daily " + BARREL_EMOJI + " news. But then I came along and prevented such a horrible tragedy. Hopefully that doesn't happen today...",
    BARREL_REP_MENTION + ": <t:{}:t>",
    BARREL_REP_MENTION + "\nG-guys can someone p-lease do the news for meeeeee? 🤓 I-it would really m-make my d-day...",
    "Hewwo my deawest " + BARREL_REP_MENTION + "! I would weally wove it if you did youw news wepowt :3 Nofing would make me happiew! Would you do it fow me??? :pleading_face:",
    "Greetings loyal " + BARREL_EMOJI + " cultists. May the " + BARREL_EMOJI + " smile upon you. We are currently awaiting the blessed deliverance of news from our esteemed " + BARREL_REP_MENTION + ". Until then, please refrain from rioting in the streets. Good day.",
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
    BARREL_REP_MENTION + "\n中國早上好！現在我有冰淇淋。我真的很喜歡冰淇淋，但是，速度與激情 9，與速度與激情 9 相比，我最喜歡。所以，現在是音樂時間。準備好。 1, 2, 3.整整兩週後，速度與激情9，整整兩週後，速度與激情9，整整兩週後，速度與激情9。不要忘記，不要錯過它。去電影院看《速度與激情9》，這是一部很棒的電影！動作很棒，比如“我會尖叫”。再見。",
]

emotions = [
    "Acceptance", "Acedia", "Adoration", "Affect labeling", "Affect regulation", "Affection", "Ambivalence", "Anger", "Angst", "Anguish", "Annoyance", "Anticipation", "Antipathy", "Anxiety", "Apathy", "Arousal",
    "Aversion to happiness", "Awe", "Boredom", "Broken heart", "Calmness", "Compassion", "Complaining", "Condescension", "Confidence", "Confusion", "Contempt", "Contentment", "Contrition", "Courage", "Creepiness", "Cute aggression",
    "Defeatism", "Depression", "Desire", "Despair", "Disappointment", "Disgust", "Doubt", "Dysphoria", "Ecstasy", "Embarrassment", "Empathy", "Emptiness", "Enthusiasm", "Envy", "Escapism", "Euphoria",
    "Exhilaration", "Fear", "Forgiveness", "Frustration", "Gloom", "Gratitude", "Grief", "Guilt", "Happiness", "Hatred", "Homesickness", "Hope", "Hostility", "Humiliation", "Hysteria", "Indignation",
    "Infatuation", "Insecurity", "Insignificance", "Insult", "Interest", "Invidia", "Irritability", "Isolation", "Jealousy", "Joy", "Kama muta", "Kindness", "Limerence", "Loneliness", "Love", "Loyalty",
    "Lust", "Malaise", "Melancholia", "Mimpathy", "Mono no aware", "Mudita", "Museum fatigue", "Nostalgia", "Outrage", "Panic", "Passion", "Passionate and companionate love", "Pathological jealousy", "Patience", "Pessimism", "Pity",
    "Pleasure", "Pride", "Quixotism", "Rage", "Regret", "Relaxation", "Relief", "Remorse", "Resentment", "Reverence", "Ridiculous", "Righteous indignation", "Rock fever", "Romance", "Runner's high", "Sadness",
    "Saudade", "Sehnsucht", "Self-pity", "Sense of wonder", "Sentimentality", "Seriousness", "Shame", "Shyness", "Silliness", "Sincerity", "Solitude", "Sorrow", "Spite", "Surprise", "Suspense", "Suspicion",
    "Sympathy", "The ick", "Trust", "Valence", "Vicarious embarrassment", "Won", "Wonder", "Worry", "Zest",
]

verbs = [
    "Be", "have", "DO", "say", "get", "make", "go", "see", "know", "take", "think", "come", "give", "look", "use", "find",
    "want", "Tell", "put", "mean", "become", "leave", "work", "need", "feel", "seem", "ask", "show", "try", "Call", "keep", "provide",
    "hold", "turn", "follow", "Begin", "bring", "like", "going", "help", "start", "run", "write", "Set", "move", "play", "pay", "hear",
    "include", "believe", "allow", "meet", "lead", "live", "stand", "happen", "carry", "talk", "appear", "produce", "sit", "offer", "consider", "expect",
    "suggest", "LET", "read", "require", "continue", "lose", "ADD", "change", "Fall", "remain", "remember", "buy", "speak", "stop", "send", "receive",
    "decide", "win", "understand", "describe", "develop", "agree", "open", "reach", "build", "involve", "spend", "return", "draw", "die", "Hope", "create",
    "walk", "sell", "wait", "cause", "pass", "Lie", "accept", "watch", "raise", "Base", "apply", "break", "explain", "learn", "increase", "cover",
    "grow", "claim", "report", "support", "cut", "form", "stay", "contain", "reduce", "establish", "join", "wish", "achieve", "seek", "choose", "deal",
    "face", "fail", "serve", "end", "kill", "occur", "drive", "represent", "rise", "discuss", "love", "pick", "place", "argue", "prove", "wear",
    "catch", "enjoy", "eat", "introduce", "enter", "present", "arrive", "ensure", "point", "plan", "pull", "refer", "act", "relate", "affect", "close",
    "identify", "manage", "thank", "compare", "announce", "obtain", "note", "forget", "indicate", "wonder", "maintain", "publish", "suffer", "avoid", "express", "suppose",
    "finish", "determine", "design", "listen", "save", "tend", "treat", "control", "share", "remove", "throw", "visit", "exist", "encourage", "force", "reflect",
    "admit", "assume", "smile", "prepare", "replace", "fill", "improve", "mention", "fight", "intend", "Miss", "discover", "drop", "hit", "push", "prevent",
    "refuse", "regard", "lay", "reveal", "Teach", "answer", "operate", "State", "depend", "enable", "record", "check", "complete", "cost", "sound", "laugh",
    "realise", "extend", "arise", "notice", "define", "examine", "fit", "study", "bear", "hang", "recognise", "shake", "sign", "attend", "fly", "gain",
    "perform", "result", "travel", "adopt", "confirm", "protect", "demand", "stare", "imagine", "attempt", "beat", "Born", "associate", "care", "marry", "collect",
    "voice", "employ", "issue", "release", "emerge", "mind", "aim", "deny", "Mark", "shoot", "appoint", "Order", "supply", "drink", "observe", "reply",
    "ignore", "link", "propose", "ring", "settle", "strike", "press", "respond", "arrange", "survive", "concentrate", "lift", "approach", "Cross", "test", "charge",
    "experience", "touch", "acquire", "commit", "demonstrate", "Grant", "prefer", "repeat", "sleep", "threaten", "feed", "insist", "launch", "limit", "promote", "deliver",
    "measure", "own", "retain", "assess", "attract", "belong", "consist", "contribute", "hide", "promise", "reject", "cry", "impose", "invite", "sing", "vary",
    "warn", "address", "declare", "destroy", "worry", "divide", "head", "name", "stick", "nod", "recognize", "train", "attack", "clear", "combine", "handle",
    "influence", "realize", "recommend", "shout", "spread", "undertake", "account", "select", "climb", "contact", "recall", "secure", "step", "transfer", "welcome", "conclude",
    "disappear", "display", "dress", "illustrate", "imply", "organise", "direct", "escape", "generate", "investigate", "remind", "advise", "afford", "earn", "hand", "inform",
    "rely", "succeed", "approve", "burn", "fear", "vote", "conduct", "cope", "derive", "elect", "gather", "jump", "last", "match", "matter", "persuade",
    "ride", "shut", "blow", "estimate", "recover", "score", "slip", "count", "hate", "attach", "exercise", "house", "lean", "roll", "wash", "accompany",
    "accuse", "bind", "explore", "judge", "rest", "steal", "comment", "exclude", "focus", "hurt", "stretch", "withdraw", "back", "fix", "justify", "knock",
    "pursue", "switch", "appreciate", "benefit", "lack", "list", "occupy", "permit", "surround", "abandon", "blame", "complain", "connect", "construct", "dominate", "engage",
    "paint", "quote", "view", "acknowledge", "dismiss", "incorporate", "interpret", "proceed", "search", "separate", "stress", "alter", "analyse", "arrest", "bother", "defend",
    "expand", "implement", "possess", "review", "suit", "tie", "assist", "calculate", "glance", "mix", "question", "resolve", "rule", "suspect", "Wake", "appeal",
    "challenge", "clean", "damage", "guess", "reckon", "restore", "restrict", "specify", "constitute", "convert", "distinguish", "submit", "trust", "urge", "feature", "Land",
    "locate", "predict", "preserve", "solve", "sort", "struggle", "cast", "Cook", "dance", "invest", "lock", "owe", "pour", "shift", "kick", "kiss",
    "Light", "purchase", "race", "retire", "Bend", "breathe", "celebrate", "date", "fire", "Monitor", "print", "register", "resist", "behave", "comprise", "decline",
    "detect", "finance", "organize", "overcome", "range", "swing", "differ", "drag", "guarantee", "oppose", "pack", "pause", "relax", "resign", "Rush", "store",
    "waste", "compete", "expose", "found", "install", "mount", "negotiate", "sink", "Split", "whisper", "assure", "award", "borrow", "bury", "capture", "deserve",
    "distribute", "doubt", "enhance", "phone", "sweep", "tackle", "advance", "cease", "concern", "emphasise", "exceed", "qualify", "slide", "strengthen", "transform", "favour",
    "grab", "lend", "participate", "perceive", "pose", "practise", "satisfy", "scream", "smoke", "sustain", "tear", "adapt", "adjust", "BAN", "consult", "dig",
    "dry", "highlight", "outline", "reinforce", "shrug", "snap", "absorb", "amount", "block", "confine", "delay", "encounter", "entitle", "plant", "pretend", "request",
    "rid", "sail", "trace", "trade", "Wave", "cite", "dream", "flow", "fulfil", "lower", "process", "react", "seize", "allocate", "burst", "communicate",
    "defeat", "double", "exploit", "fund", "govern", "hurry", "injure", "pray", "protest", "sigh", "smell", "stir", "swim", "undergo", "wander", "anticipate",
    "collapse", "compose", "confront", "ease", "eliminate", "evaluate", "grin", "interview", "remark", "suspend", "weigh", "wipe", "wrap", "attribute", "Balance", "bet",
    "bound", "cancel", "condemn", "convince", "correspond", "dare", "devise", "free", "gaze", "guide", "inspire", "modify", "murder", "prompt", "reverse", "rub",
    "slow", "spot", "swear", "telephone", "wind", "admire", "bite", "crash", "disturb", "greet", "hesitate", "induce", "integrate", "knit", "line", "load",
    "murmur", "render", "shine", "swallow", "tap", "translate", "yield", "accommodate", "age", "assert", "await", "Book", "brush", "Chase", "comply", "copy",
    "criticise", "devote", "evolve", "flee", "forgive", "initiate", "interrupt", "leap", "mutter", "overlook", "risk", "SHAPE", "spell", "squeeze", "trap", "undermine",
    "witness", "beg", "drift", "Echo", "emphasize", "enforce", "exchange", "fade", "float", "freeze", "hire", "IN", "object", "pop", "provoke", "recruit",
    "research", "sense", "situate", "stimulate", "abolish", "administer", "allege", "command", "consume", "convey", "correct", "educate", "equip", "execute", "fetch", "frown",
    "invent", "MArch", "Park", "progress", "reserve", "respect", "twist", "unite", "value", "assign", "cater", "concede", "conceive", "disclose", "envisage", "exhibit",
    "export", "extract", "fancy", "inherit", "insert", "instruct", "interfere", "isolate", "opt", "peer", "persist", "plead", "Price", "regret", "regulate", "repair",
    "resemble", "resume", "speed", "spin", "spring", "update", "advocate", "assemble", "boost", "breed", "cling", "commission", "conceal", "contemplate", "criticize", "decorate",
    "descend", "drain", "edit", "embrace", "excuse", "explode", "facilitate", "flash", "fold", "function", "grasp", "incur", "intervene", "label", "please", "rescue",
    "strip", "tip", "upset", "advertise", "aid", "Centre", "classify", "coincide", "confess", "contract", "crack", "creep", "decrease", "deem", "dispose", "dissolve",
    "dump", "endorse", "formulate", "import", "impress", "market", "reproduce", "scatter", "schedule", "ship", "shop", "spare", "sponsor", "stage", "suck", "Sue",
    "tempt", "vanish", "access", "commence", "contrast", "depict", "discharge", "draft", "enclose", "enquire", "erect", "file", "halt", "Hunt", "inspect", "omit",
    "originate", "praise", "precede", "relieve", "reward", "round", "SEAL", "signal", "smash", "spoil", "subject", "target", "taste", "tighten", "top", "tremble",
    "tuck", "warm", "activate", "amend", "arouse", "bang", "bid", "bow", "campaign", "characterise", "circulate", "clarify", "compensate", "compile", "cool", "couple",
    "depart", "deprive", "desire", "diminish", "drown", "embark", "entail", "entertain", "figure", "fling", "guard", "manufacture", "melt", "neglect", "plunge", "project",
    "rain", "reassure", "rent", "revive", "sentence", "shed", "slam", "spill", "stem", "sum", "summon", "supplement", "suppress", "surprise", "tax", "thrust",
    "tour", "transmit", "transport", "weaken", "widen", "bounce", "calm", "characterize", "chat", "clutch", "confer", "conform", "confuse", "convict", "counter", "debate",
    "dedicate", "dictate", "disagree", "effect", "flood", "forbid", "grip", "heat", "long", "manipulate", "merge", "part", "PIN", "position", "prescribe", "proclaim",
    "punish", "rebuild", "regain", "sack", "strain", "stroke", "substitute", "supervise", "term", "time", "toss", "underline", "abuse", "accumulate", "alert", "arm",
    "attain", "boast", "boil", "carve", "cheer", "colour", "compel", "crawl", "crush", "Curl", "deposit", "differentiate", "dip", "dislike", "divert", "embody",
    "exert", "exhaust", "fine", "frighten", "fuck", "gasp", "honour", "inhibit", "motivate", "multiply", "narrow", "obey", "penetrate", "picture", "presume", "prevail",
    "pronounce", "rate", "renew", "revise", "rip", "scan", "scratch", "shiver",
]

adjectives = [
    "Good", "New", "Old", "Great", "High", "Small", "Large", "Long", "Young", "Right", "Early", "Big", "Late", "Full", "FAR", "Low",
    "Bad", "Sure", "Clear", "Likely", "Real", "Black", "White", "Free", "Easy", "Short", "Strong", "TRUE", "Hard", "Poor", "Wide", "Simple",
    "Close", "Fine", "Wrong", "French", "Nice", "Happy", "Red", "Sorry", "Dead", "Heavy", "Cold", "Ready", "Green", "Deep", "Left", "Complete",
    "Hot", "Fair", "Huge", "Rich", "Safe", "Chief", "Light", "Warm", "Fresh", "Cheap", "United", "Strange", "Soft", "Quiet", "Quick", "Broad",
    "Very", "Lovely", "Joint", "Bright", "Average", "INC", "Unlikely", "Dry", "Thin", "Slow", "Tiny", "Wild", "Empty", "Alone", "Narrow", "Bloody",
    "Busy", "Tall", "Clean", "Thick", "Fast", "Rare", "Grand", "Brief", "Grey", "Funny", "Severe", "Vast", "Ill", "Weak", "Brown", "Sick",
    "Near", "Angry", "Well", "Guilty", "Lucky", "Tough", "Glad", "Yellow", "Net", "Dear", "Healthy", "Slight", "Friendly", "Flat", "Keen", "Pale",
    "Wet", "Firm", "Sad", "Pure", "Sweet", "Rough", "Absolute", "Mere", "Spanish", "Cool", "Fit", "Extreme", "Proud", "Mad", "Straight", "Pink",
    "Smooth", "Remote", "Pretty", "Holy", "Honest", "Silly", "Plain", "Still", "Round", "Fat", "Tight", "Dirty", "Pleasant", "Welcome", "Deaf", "Mean",
    "Blind", "Steady", "Raw", "Clever", "Wise", "Strict", "Loud", "Gross", "Bare", "Modest", "Acute", "Curious", "Sole", "Urgent", "Sheer", "Nasty",
    "Unhappy", "Unfair", "Faint", "Hungry", "Just", "Spare", "Neat", "Crazy", "Brave", "Damp", "Secure", "Steep", "Dull", "Lonely", "Mild", "Casual",
    "Harsh", "Fierce", "Handsome", "Mature", "Gay", "Boring", "Smart", "Wealthy", "Lively", "Stiff", "Drunk", "Kind", "Blank", "Mid", "Profound", "Shallow",
    "Bold", "Crude", "Cruel", "Rear", "Compact", "Ugly", "Calm", "Slim", "Divine", "Worthy", "Unpleasant", "Sound", "Costly", "Lengthy", "Polite", "Fond",
    "OK", "Purple", "Shy", "Grim", "Noisy", "Grave", "Mighty", "Sunny", "Rude", "Deadly", "Handy", "Swift", "Sticky", "Bleak", "EST", "Shiny",
    "Dumb", "Sore", "Ample", "Dusty", "Petty", "Sandy", "Overnight", "Minute", "Tidy", "Lazy", "Wary", "Obscure", "Hollow", "Sexy", "Icy", "Scarce",
    "Glossy", "Naughty", "Lean", "Risky", "Robust", "Gloomy", "Fancy", "Weary", "Dim", "Tricky", "Foul", "Filthy", "Cosy", "Bald", "Coarse", "Daft",
    "Merry", "Frail", "Ripe", "Sour", "Frank", "Moist", "Muddy", "Corrupt", "Rocky", "Speedy", "Apt", "Discreet", "Sincere", "Plump", "Crisp", "Fiery",
    "Sturdy", "Fatty", "Dire", "Jolly", "Greedy", "Bland", "Blunt", "Split", "Prudent", "Clumsy", "Shrewd", "Unlucky", "Shaky", "Floppy", "Brisk", "Blond",
    "Stormy", "Creamy", "Stale", "Kindly", "Cunning", "Curly", "Stately", "Stout", "Wry", "Windy", "Void", "Witty", "Vain", "Untidy", "Messy", "Bulky",
    "Lush", "Cheeky", "Taut", "Posh", "Chilly", "Prompt", "Perverse", "Negligent", "Sparse", "Dizzy", "Shabby", "Greasy", "Sleepy", "Rusty", "Hardy", "Hairy",
    "Gold", "Tasty", "Ghastly", "Shadowy", "Thirsty", "Scant", "Sane", "Patchy", "Sleek", "Grubby", "Unkind", "Flash", "Tame", "Lowly", "Trendy", "Stony",
    "Flimsy", "Skinny", "Ghostly", "Baggy", "Shady", "Woolly", "Shrill", "Murky", "Nude", "Numb", "Oily", "Airy", "Silky", "Grassy", "Misty", "Scruffy",
    "Vile", "Needy", "Homely", "Cute", "Rosy", "Drab", "Heady", "Dreary", "Roast", "Smelly", "Down", "Sublime", "Hefty", "Lame", "Darling", "Cloudy",
    "Staunch", "Queer", "Dodgy", "Smug", "Lofty", "Hasty", "Rainy", "Weighty", "Snug", "Soggy", "Sickly", "Worldly", "Spiky", "Spicy", "Trim", "Steely",
    "Scary", "Sloppy", "Prickly", "Supple", "Slick", "Uncanny", "Slimy", "Salty", "Stuffy", "Unruly", "Unsold", "Smoky", "Snowy", "Quaint", "Stocky",
    "Snap", "Ruddy", "Hearty", "Dour", "Cheery", "Grimy", "Limp", "Hilly", "Cross", "Bust", "Drowsy", "Burly", "Lumpy", "Bumpy", "Crafty", "Leafy",
    "Dingy", "Hoarse", "Hazy", "Husky", "Cuddly", "Crap", "Juicy", "Gruesome", "Dainty", "Classy", "Chunky", "Gritty", "Glassy", "Slack", "Fussy", "Fruity",
    "Meek", "Fleshy", "Mellow", "Frosty", "Foggy", "Arty", "Fluffy", "Arch", "Lousy", "Brash", "Moody", "Fuzzy", "Gaudy", "Furry", "Gaunt", "Spooky",
    "Sporty", "Spoilt", "Sprightly", "Springy", "Stealthy", "Crusty", "Frilly", "Sketchy", "Snide", "Staid", "Squeaky", "Starry", "Skimpy", "Flashy", "Dank",
    "Sneaky", "Fizzy", "Snappy", "Fishy", "Princely", "Weedy", "Edgy", "Dusky", "Sleazy", "Dreamy", "Deft", "Dumpy", "Soy", "Dotty", "Dowdy",
    "Downtown", "Dozy", "Draughty", "Earthy", "Arcane", "Bonny", "Bossy", "Bouncy", "Brainy", "Breezy", "Bubbly", "Ungainly", "Zany", "Trusty", "Bushy", "Trite",
    "Canny", "Wacky", "Balmy",
]

nouns = [
    "Time", "Year", "People", "Way", "Man", "Day", "Thing", "Child", "Government", "Work", "Life", "Woman", "System", "Case", "Part", "Group",
    "Number", "World", "House", "Area", "Company", "Problem", "Service", "Place", "Hand", "Party", "School", "Country", "Point", "Week", "Member", "End",
    "State", "Word", "Family", "Fact", "Head", "Month", "Side", "Business", "Night", "Eye", "Home", "Question", "Information", "Power", "Change", "Interest",
    "Development", "Money", "Book", "Water", "Other", "Form", "Room", "Level", "Car", "Council", "Policy", "Market", "Court", "Effect", "Result", "Idea",
    "Use", "Study", "Job", "Name", "Body", "Report", "Line", "Law", "Face", "Friend", "Authority", "Road", "Minister", "Rate", "Door", "Hour",
    "Office", "Right", "War", "Mother", "Person", "Reason", "View", "Term", "Period", "Centre", "Figure", "Society", "Police", "City", "Need", "Community",
    "Million", "Kind", "Price", "Control", "Action", "Cost", "Issue", "Process", "Position", "Course", "Minute", "Education", "Type", "Research", "Subject", "Programme",
    "Girl", "Moment", "Age", "Father", "Force", "Order", "Value", "Act", "Matter", "Health", "Lot", "Decision", "Street", "Industry", "Patient", "Class",
    "Mind", "Church", "Condition", "Paper", "Bank", "Century", "Section", "Activity", "Hundred", "Table", "Death", "Building", "Sense", "Sort", "Staff", "Team",
    "Experience", "Student", "Language", "Town", "Plan", "Department", "Management", "Morning", "Committee", "Product", "Practice", "Evidence", "Ground", "Letter", "Meeting", "Foot",
    "Boy", "Back", "Game", "Food", "Union", "Role", "Event", "Land", "Art", "Support", "Range", "Stage", "Teacher", "Trade", "Voice", "Arm",
    "Club", "Field", "History", "Parent", "Account", "Material", "Care", "Situation", "Manager", "Project", "Record", "Example", "Training", "Window", "Air", "Difference",
    "Light", "University", "Wife", "Relationship", "Quality", "Rule", "Pound", "Story", "Tax", "Worker", "Data", "Model", "Nature", "Officer", "Structure", "Bed",
    "Hospital", "Method", "Unit", "Movement", "Detail", "Date", "Wall", "Computer", "Amount", "Approach", "Bit", "Award", "President", "Scheme", "Chapter", "Theory",
    "Property", "Son", "Director", "Leader", "South", "Application", "Firm", "Board", "King", "Production", "Secretary", "Chance", "Operation", "Opportunity", "Share", "Agreement",
    "Lord", "Contract", "Picture", "Test", "Security", "Thousand", "Election", "Source", "Colour", "Future", "Site", "Loss", "Shop", "Animal", "Evening", "Benefit",
    "Heart", "Purpose", "Standard", "Page", "Doctor", "Factor", "Hair", "Love", "Music", "Charge", "Pattern", "Design", "Piece", "Population", "Tree", "Knowledge",
    "Performance", "Plant", "Pressure", "Fire", "Environment", "Garden", "Size", "Analysis", "Rest", "Success", "Thought", "Region", "Attention", "List", "Relation", "Set",
    "Space", "Statement", "Demand", "Labour", "Principle", "Sea", "Step", "Capital", "Choice", "Couple", "Hotel", "Player", "Station", "Village", "Film", "Association",
    "Attempt", "Feature", "Income", "Individual", "Cup", "Effort", "Organisation", "Technology", "Difficulty", "Machine", "Cell", "Degree", "Energy", "Growth", "Treatment", "Lady",
    "Mile", "County", "Function", "Provision", "Risk", "Sound", "Task", "Top", "Behaviour", "Defence", "Resource", "Floor", "Science", "Style", "College", "Feeling",
    "Hall", "Horse", "Response", "Skill", "Character", "User", "Answer", "Army", "Dog", "Economy", "Investment", "Look", "Brother", "Husband", "Argument", "Responsibility",
    "Season", "Bill", "Concern", "Element", "Glass", "Duty", "Increase", "Claim", "Fund", "Leg", "Park", "Title", "Note", "Aspect", "Chairman", "Discussion",
    "Summer", "Baby", "Daughter", "Sun", "Box", "Customer", "Institution", "River", "Profit", "Conference", "Division", "Measure", "Stone", "Commission", "Post", "Procedure",
    "Proposal", "Circumstance", "Client", "Help", "Image", "Oil", "Sector", "Attack", "Direction", "Seat", "Attitude", "Disease", "Employment", "Goal", "Affair", "Appeal",
    "Sign", "Ability", "Campaign", "Fish", "Holiday", "Item", "Medium", "Pupil", "Show", "Technique", "Version", "Advice", "Drug", "Library", "Press", "Visit",
    "Advantage", "Surface", "Blood", "Culture", "Island", "Memory", "Return", "Television", "Variety", "BAR", "Competition", "Extent", "Majority", "Parliament", "Speaker", "Talk",
    "Access", "Deal", "Star", "Text", "Cause", "Mouth", "Payment", "Trouble", "Context", "Facility", "Reference", "Second", "Survey", "Article", "Chair", "Earth",
    "Importance", "Object", "Agency", "Card", "Collection", "Communication", "Possibility", "Public", "Document", "Sister", "Supply", "Budget", "Career", "Influence", "Solution", "Weight",
    "Bird", "Damage", "District", "Fear", "Opinion", "Organization", "Requirement", "Rock", "Call", "Edge", "Exchange", "Opposition", "Option", "Quarter", "Stock", "Whole",
    "Aid", "Arrangement", "Concept", "Executive", "Match", "Network", "Occasion", "Radio", "Railway", "Target", "Corner", "Finger", "Forest", "Mum", "Race", "Sex",
    "Afternoon", "Ball", "Crime", "Employee", "Equipment", "Kitchen", "Message", "Peace", "Review", "Scale", "Scene", "Speech", "Sport", "Strategy", "Band", "Expression",
    "Failure", "Hill", "Partner", "Reader", "Shoulder", "Tea", "Marriage", "Owner", "Trust", "Truth", "Turn", "Farm", "File", "Newspaper", "Past", "Safety",
    "Sentence", "Start", "Trial", "Balance", "Branch", "Copy", "League", "Length", "Nation", "Wind", "Accident", "Doubt", "Front", "Move", "Pain", "Spirit",
    "Studio", "Train", "Contact", "Official", "Strength", "Cash", "Contribution", "Debate", "Gas", "Museum", "Reform", "SHAPE", "Transport", "Agent", "Artist", "English",
    "Pair", "Presence", "Protection", "Rise", "Candidate", "Driver", "Hope", "Master", "Meaning", "Queen", "Vote", "Adult", "Consequence", "Exercise", "Play", "Assessment",
    "Beginning", "Consideration", "FIG", "Proportion", "Route", "Speed", "Credit", "Impact", "Understanding", "Danger", "Flower", "Half", "Path", "Reaction", "Track", "Video",
    "Aim", "Bag", "Belief", "Comment", "Conclusion", "Content", "Distance", "Gold", "Justice", "Link", "Skin", "Boat", "Dad", "Estate", "Prison", "Reality",
    "Sight", "Wine", "Winter", "Debt", "Employer", "Objective", "Offer", "Vehicle", "Weekend", "Writer", "Battle", "Colleague", "Expert", "Farmer", "Hole", "Injury",
    "Package", "Telephone", "Confidence", "Generation", "Insurance", "Key", "Painting", "Phone", "Sample", "Commitment", "Conflict", "Drink", "Judge", "Legislation", "Ship", "Threat",
    "Visitor", "Volume", "Administration", "Author", "Background", "Cabinet", "Engine", "Entry", "Introduction", "Manner", "Smile", "Stuff", "Victim", "Yard", "Bus", "Coffee",
    "Investigation", "Mountain", "Regulation", "Relief", "Row", "Song", "Wage", "Category", "Consumer", "Dinner", "Exhibition", "Football", "Interview", "Meal", "Tour", "Tradition",
    "Traffic", "Wood", "Appearance", "Bridge", "Construction", "Contrast", "Description", "Discipline", "Distribution", "Existence", "Flat", "Gentleman", "Housing", "Improvement", "Lip", "Session",
    "Sheet", "TV", "Audience", "Code", "Conversation", "Crisis", "Loan", "Prince", "Representative", "Theatre", "Asset", "Explanation", "Flight", "Freedom", "Limit", "Magazine",
    "Pension", "Plate", "Rain", "Respect", "Writing", "Capacity", "Challenge", "Dream", "Factory", "Finance", "Selection", "Spring", "Victory", "While", "Youth", "Aircraft",
    "Decade", "Definition", "Egg", "Examination", "Intention", "Mark", "Notice", "Output", "Offence", "Reduction", "Will", "Address", "Appointment", "Bedroom", "Bottom", "Concentration",
    "Enterprise", "Kid", "Middle", "Murder", "Neck", "Run", "Tape", "Weapon", "Absence", "Acid", "Assembly", "Birth", "Bottle", "Criticism", "Ear", "Error",
    "Instruction", "Module", "Settlement", "Store", "Teaching", "Transfer", "Wave", "Channel", "Component", "Cut", "Desire", "Fee", "Grant", "Implication", "Institute", "Lead",
    "Lunch", "Photograph", "Pleasure", "Recognition", "Republic", "Solicitor", "Temperature", "Waste", "Weather", "Block", "Brain", "Expenditure", "Experiment", "Guest", "Guide", "Household",
    "Nurse", "Program", "Publication", "Screen", "Silence", "Treaty", "Assumption", "Captain", "Congress", "Connection", "Cover", "Crowd", "Curriculum", "Initiative", "Journey", "Map",
    "Metal", "Noise", "Phase", "Pool", "Scientist", "Search", "Sequence", "Sky", "Sum", "Trip", "Violence", "CAT", "Display", "Gallery", "Gate", "Gun",
    "Heat", "Instrument", "Location", "Ministry", "Professor", "Reading", "Theme", "Combination", "Drive", "Faith", "Hell", "Interpretation", "Learning", "Opening", "Priority", "Prospect",
    "Soldier", "Spot", "Tool", "Tooth", "Troop", "Alternative", "Breath", "Castle", "Coal", "Corp", "Crown", "Flow", "Lane", "Literature", "Membership", "Mistake",
    "Motion", "Release", "Revenue", "Total", "Variation", "Wing", "Border", "Criterion", "Incident", "Index", "Passage", "Pocket", "Ring", "Suggestion", "Valley", "Winner",
    "Billion", "Characteristic", "Deputy", "Device", "Engineering", "Foundation", "Fruit", "Lake", "Leaf", "Pub", "Religion", "Representation", "Request", "Restaurant", "Specialist", "Square",
    "Surprise", "Tone", "Walk", "Chain", "Circle", "Creation", "Fall", "Observation", "Present", "Shot", "Strike", "Atmosphere", "Championship", "Clause", "Coast", "Defendant",
    "Desk", "Distinction", "Enemy", "Fashion", "God", "Impression", "Leadership", "Marketing", "Mass", "Mechanism", "Neighbour", "Panel", "Revolution", "Tear", "Advance", "Beach",
    "Drawing", "Dress", "Engineer", "Establishment", "Fan", "Iron", "Liability", "Milk", "Motor", "Negotiation", "Nose", "Origin", "Potential", "Servant", "Shoe", "Soil",
    "Tank", "Ticket", "Welfare", "Bone", "Cancer", "Champion", "Chief", "Citizen", "Convention", "Editor", "Expense", "Fuel", "General", "Gift", "Height", "Palace",
    "Prisoner", "Round", "Significance", "Trend", "Vision", "Warning", "Achievement", "Being", "CO", "Comparison", "Cross", "Democracy", "Diet", "Expectation", "Knee", "Lawyer",
    "Lesson", "Living", "Notion", "Outcome", "Parish", "Rail", "Signal", "Working", "Breakfast", "Charity", "Column", "Complaint", "Corporation", "Councillor", "Finding", "Gap",
    "Grass", "Inflation", "Manufacturer", "Passenger", "Plane", "Plastic", "Root", "Score", "Shadow", "Shock", "Tenant", "Territory", "Touch", "Accommodation", "Beauty", "Boundary",
    "Buyer", "Database", "Dispute", "Exception", "Formation", "Identity", "Inquiry", "Licence", "Male", "Politician", "Ref", "Resident", "Resolution", "Struggle", "Supporter", "Topic",
    "Transaction", "Assistance", "Break", "Camp", "Currency", "Emergency", "Fault", "Metre", "Minority", "Mirror", "Novel", "Phrase", "Pilot", "Preparation", "Proceeding", "Quantity",
    "Taste", "Tension", "Thinking", "Coat", "Constitution", "Extension", "Gene", "Involvement", "Mill", "Partnership", "Pollution", "Premise", "Prize", "Spokesman", "Stress", "Tower",
    "UNIX", "Boot", "Command", "Decline", "Delivery", "Depth", "Female", "Frame", "Framework", "German", "Holder", "ICE", "Inch", "Obligation", "Poem", "Port",
    "Protein", "Regime", "Rose", "Saving", "String", "Wheel", "Approval", "Bishop", "Boss", "Chest", "Cottage", "Crew", "Cycle", "Export", "Funding", "Governor",
    "Hat", "Load", "Mode", "Profession", "Protest", "Recommendation", "Restriction", "Setting", "Stairs", "Travel", "Agriculture", "Autumn", "Average", "Bomb", "Camera", "Creature",
    "Critic", "Empire", "Focus", "Green", "Guard", "Habit", "Input", "Inspector", "Landscape", "Layer", "Plaintiff", "Poll", "Purchase", "Recession", "Recovery", "Reputation",
    "Shareholder", "Silver", "Sleep", "Suit", "Trading", "Arrival", "Beer", "Bread", "Cake", "Drama", "Efficiency", "Electricity", "Illness", "Judgment", "Laboratory", "Meat",
    "Muscle", "Peak", "Penalty", "Perspective", "Presentation", "Resistance", "Self", "Soul", "Steel", "Sugar", "Uncle", "Abuse", "Alliance", "Angle", "Bay", "Bid",
    "Certificate", "Chancellor", "Cloud", "Coach", "Custom", "Dollar", "Expansion", "Lifespan", "Mood", "PC", "Personality", "Philosophy", "Possession", "Producer", "Promotion", "Ratio",
    "Spending", "Symptom", "Variable", "Zone", "Actor", "Awareness", "Bond", "Chamber", "Chip", "Cigarette", "CORE", "Deposit", "Dozen", "Estimate", "Festival", "Final",
    "Frequency", "Gain", "Guy", "Honour", "Intervention", "Jacket", "Phenomenon", "Qualification", "Relative", "Rent", "Reply", "Researcher", "Secret", "Shirt", "Tendency", "Wedding",
    "American", "Apple", "Breach", "Cheek", "Dance", "Dealer", "Discovery", "Duke", "Emotion", "Equation", "French", "Furniture", "Instance", "Intelligence", "Investor", "Lad",
    "Landlord", "Mixture", "Pipe", "Promise", "Recording", "Retirement", "Routine", "Substance", "Throat", "Tourist", "Allowance", "Anger", "Birthday", "Carpet", "Consent", "Cricket",
    "Curtain", "Curve", "Darkness", "Disaster", "Disk", "DNA", "Enquiry", "Entrance", "Fight", "Golf", "Guitar", "Hearing", "Hero", "Infection", "Interaction", "Journal",
    "Judgement", "Knife", "Left", "Mail", "Medicine", "Mortgage", "Pace", "Paragraph", "Permission", "Platform", "Policeman", "Print", "Rank", "Reserve", "Sand", "Scope",
    "Shift", "Stream", "Tale", "Witness", "Acquisition", "Adviser", "Airport", "Aunt", "Bath", "Chemical", "Circuit", "Clock", "Consumption", "Cream", "Defeat", "Delay",
    "Demonstration", "Edition", "Host", "Human", "Joke", "Peasant", "Perception", "Personnel", "Priest", "Province", "Sake", "SALT", "Anxiety", "Compensation", "Consultant", "Count",
    "Fishing", "Formula", "Journalist", "Lecture", "Luck", "Mission", "Occupation", "Pack", "Percentage", "Poet", "Remark", "Seed", "Supplier", "Survival", "Tail", "Tie",
    "Watch", "Workshop", "Alcohol", "Barrier", "Climate", "Conservative", "Crop", "Dark", "Fortune", "Heaven", "Hold", "Indication", "Measurement", "Mine", "Moon", "Net",
    "Observer", "Opponent", "Ownership", "Pitch", "Practitioner", "Prayer", "Preference", "Smell", "Snow", "Stomach", "Symbol", "Tip", "Architecture", "Bowl", "Burden", "Catalogue",
    "Cheese", "Confusion", "Democrat", "Dimension", "Dish", "Enthusiasm", "Evaluation", "Historian", "Implementation", "Interval", "Operator", "Princess", "Professional", "Publisher", "Satisfaction", "Schedule",
    "Sheep", "Shell", "Storage", "Summary", "Talent", "Tube", "Wish", "Admission", "Breast", "Cheque", "Childhood", "Conduct", "Consultation", "Designer", "Determination", "Drop",
    "Fabric", "Import", "Label", "Leisure", "Lover", "Merchant", "Percent", "Poetry", "Pot", "Proof", "Replacement", "Salary", "Shopping", "Smoke", "Squad", "Stake",
    "Steam", "Strain", "Tissue", "Tunnel", "Turnover", "Unity", "Vessel", "Win", "Wire", "Addition", "Amendment", "Announcement", "Bathroom", "Bell", "Brick", "Classroom",
    "Comfort", "Complex", "Conviction", "Corridor", "Draft", "Favour", "Grade", "Imagination", "Lift", "Magistrate", "Mouse", "Movie", "Mystery", "Participant", "Profile", "Refugee",
    "Reward", "Sergeant", "Standing", "Surgery", "Tongue", "Vegetable", "Acceptance", "Architect", "Assistant", "Belt", "Black", "Cathedral", "Ceiling", "Check", "Composition", "Constituency",
    "Deficit", "Departure", "Detective", "Discourse", "Excitement", "Gesture", "Joy", "Limitation", "Local", "Participation", "Pit", "Pride", "Red", "Register", "Storm", "Summit",
    "Transition", "Treasury", "Twin", "Universe", "Venture", "Weakness", "Album", "Assault", "BAN", "Bench", "Button", "Canal", "Cap", "Chart", "Clerk", "Coalition",
    "Coin", "Concert", "Consciousness", "Constraint", "Cow", "Diary", "Dust", "Expertise", "Fellow", "Folk", "Glance", "Grammar", "Guardian", "Guideline", "Horror", "Infant",
    "Leather", "Margin", "Mummy", "Objection", "Opera", "Paint", "Passion", "Pole", "Prosecution", "Psychology", "Reception", "Repair", "Shelf", "Stand", "Stick", "Timber",
    "Tin", "Uncertainty", "Virtue", "Ward", "Agenda", "Alarm", "Blue", "Cable", "Carbon", "Charter", "Chicken", "Closure", "Cold", "Companion", "Completion", "Conservation",
    "Cousin", "Craft", "Disorder", "Dividend", "Evolution", "Flesh", "Format", "Funeral", "Good", "Ideology", "Jury", "Kingdom", "Lease", "Mate", "Nerve", "Ocean",
    "Patch", "Pen", "Pig", "Portrait", "Potato", "Printer", "Privilege", "Punishment", "Rabbit", "Reflection", "Rival", "Specimen", "Taxation", "Traveller", "Van", "VAT",
    "Volunteer", "Ally", "Applicant", "Assurance", "Attraction", "Audit", "Blow", "Borough", "Carriage", "Chocolate", "Commander", "Commissioner", "Conversion", "Depression", "Destruction", "Disc",
    "Discount", "Earl", "Emperor", "Essay", "Exposure", "Favourite", "Friendship", "Garage", "Innovation", "Integration", "Junction", "Lock", "Machinery", "Maker", "Organ", "Particle",
    "Pass", "Petrol", "Planet", "Plot", "Purchaser", "Rat", "Registration", "Remedy", "Resignation", "Seller", "Silk", "Slope", "Stop", "Strip", "Sympathy", "Terrace",
    "Vendor", "Wonder", "Allocation", "Ambition", "Bike", "Calculation", "Chapel", "Collapse", "Conception", "Correspondent", "Cotton", "Crash", "Cry", "Darling", "Declaration", "Directive",
    "Disposal", "Dose", "Entertainment", "Excuse", "Fate", "Federation", "Fibre", "Flame", "Grain", "Harm", "Humour", "Hypothesis", "Identification", "Incentive", "Inspection", "Interface",
    "Invitation", "Logic", "Mayor", "Mineral", "Molecule", "Mortality", "Needle", "Pile", "Pop", "Resort", "Roll", "Rubbish", "Shade", "Stimulus", "Stranger", "Suspicion",
    "Trick", "Voter", "Withdrawal", "Youngster", "Accountant", "Acre", "Advertisement", "Angel", "Arrest", "Ceremony", "Cinema", "Clinic", "Cloth", "Competitor", "Complexity", "Constable",
    "Coverage", "Daddy", "Dictionary", "Disability", "Domain", "Equity", "Equivalent", "ERA", "Explosion", "Fence", "Fragment", "Guarantee", "Insight", "Interior", "Isle", "Jew",
    "Kit", "Lamp", "Leave", "Lie", "Miner", "Pond", "Processor", "Removal", "Rope", "Running", "Satellite", "Server", "Stability", "Statute", "Taxi", "Tide",
    "Tonne", "Adjustment", "Allegation", "Anniversary", "Banking", "Battery", "Bible", "Brand", "Bulk", "Butter", "Celebration", "Christian", "Clothing", "Colony", "Controversy", "Crystal",
    "Delight", "Desert", "Emission", "Episode", "Escape", "Fat", "Fiction", "Fighting", "Fleet", "Gaze", "Gear", "Grip", "Hardware", "Illustration", "Insect", "Invasion",
    "Jurisdiction", "Lion", "Merger", "Mess", "Minimum", "Monopoly", "Motive", "Myth", "Navy", "Necessity", "Nursery", "Photo", "Piano", "Raid", "Rebel", "Rhythm",
    "Shortage", "Specification", "Switch", "Temple", "Therapy", "Tory", "Tournament", "Toy", "Transformation", "Tribunal", "Trustee", "Villa", "White", "Worth", "Wound", "Abbey",
    "Adventure", "Airline", "Attendance", "Businessman", "Champagne", "Chap", "Cliff", "Clue", "Colonel", "Compound", "Counter", "Creditor", "Devil", "Disadvantage", "Discrimination", "Dock",
    "Doctrine", "Essence", "Filter", "Flag", "Flexibility", "Fraction", "Gang", "Gender", "Ghost", "Harbour", "Heel", "Heritage", "Hierarchy", "Hint", "Indicator", "Landing",
    "Launch", "Leaflet", "Lorry", "Loyalty", "Menu", "Mud", "Nail", "Outline", "Painter", "Pensioner", "Pope", "Productivity", "Proposition", "Receiver", "Refusal",
    "Restoration", "Ride", "Rumour", "Shore", "Singer", "Skirt", "Sociology", "Spectrum", "Successor", "Testing", "Theft", "Toilet", "Tragedy", "Triumph", "Uniform", "Verse",
    "Virus", "Warmth", "Widow", "Accent", "Analyst", "Apartment", "Appendix", "Availability", "Avenue", "Bastard", "Breed", "Builder", "Bureau", "Capitalism", "Carrier",
    "Classification", "Collector", "Compromise", "Continent", "Copper", "Crack", "Cupboard", "Defender", "Delegate", "Density", "Developer", "Diagnosis", "Dialogue", "Directory", "Discretion", "Doorway",
    "Duck", "Duration", "Envelope", "Fantasy", "Fluid", "Fool", "Forum", "Fraud", "Graduate", "Grave", "Heading", "Hip", "Installation", "Isolation", "Juice", "Justification",
    "Killer", "Kiss", "Laugh", "Liberty", "Lifetime", "Merit", "Midnight", "Missile", "Modification", "Musician", "Norm", "Oak", "Offender", "Oxygen", "Palm", "PET",
    "Polytechnic", "Portfolio", "Premium", "Probability", "Receipt", "Recipe", "Reporter", "Residence", "Rod", "Sandwich", "Sculpture", "Seminar", "Sensation", "Separation", "Shame", "Shit",
    "Shower", "Sin", "Speculation", "Stance", "Stroke", "Succession", "Suicide", "Sword", "Trace", "Truck", "Whisky", "Worry", "Ambulance", "Assignment", "Auditor", "Autonomy",
    "Basket", "Bean", "Bear", "Bonus", "Capability", "Clash", "Commonwealth", "Concession", "Correlation", "Coup", "Delegation", "Diagram", "Divorce", "Eagle", "Easter", "Entity",
    "Finish", "Glory", "Guilt", "Holding", "Horizon", "Hunting", "Incidence", "Ingredient", "Inn", "Instinct", "Jet", "Liberation", "Lung", "Motivation", "Nest", "Nightmare",
    "Organism", "Packet", "Panic", "Pause", "Pavement", "Pity", "Pregnancy", "Radiation", "Redundancy", "Reign", "Riot", "Scandal", "Scholar", "Spell", "Sphere", "Spread",
    "Subsidiary", "Subsidy", "Swimming", "Tactic", "Teenager", "Thesis", "Timing", "Trader", "Trainer", "Tray", "Tune", "Tutor", "Wool", "Accuracy", "Archbishop", "Beam",
    "Blade", "Blanket", "Boom", "Bronze", "Brush", "Bush", "Cab", "Casualty", "Clay", "Constituent", "Contest", "Counterpart", "Deck", "Diamond", "Disappointment", "Dismissal",
    "Engagement", "Exclusion", "Execution",
]


interjections = [
    "ah", "ah", "er", "ew", "ha", "ho", "oh", "oi", "ow", "oy",
    "aha", "aww", "aya", "boo", "eek", "gee", "hey", "huh", "mmm", "shh", "tut", "ugh", "wow", "yay", "yuk",
    "ahem", "darn", "d'oh", "egad", "gosh", "hmmm", "hmph", "oops", "ouch", "phew", "psst", "shoo", "sigh", "well", "whee", "whoa", "woah", "yeah", "yuck",
    "aargh", "blast", "bravo", "golly", "ha ha", "howdy", "lordy", "oh my", "oh no", "scram", "ta-da", "uh-ho", "yahoo", "yikes", "zowie",
    "cheers", "crikey", "eureka", "ho hum", "hooray", "hurrah", "indeed", "my bad", "no way", "oh boy", "please", "really", "thanks", "yippee",
    "hang on", "hee hee", "hot dog", 'jeepers', "jinkies", "oh dear", "oh well", "so long", "tee hee", "tsk tsk", "tsk tsk", "woo-hoo", "you bet",
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


