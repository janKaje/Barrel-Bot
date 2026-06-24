import os
import sys
import re
import time
import json
from PIL import Image, ImageDraw
from io import BytesIO

import discord
from discord.ext import commands, tasks

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.join(dir_path, "base"))

from extra_exceptions import *
from player import (
    Player, 
    work_multiplier, 
    shopitem_saleprice_multiplier, 
    fish_saleprice_multiplier, 
    rent_multiplier
)
from checks import Checks
from emojis import EmojiDefs as ED


async def setup(bot):
    await bot.add_cog(Research(bot))

async def temp_bot_send(ctx: commands.Context, content: str = None, embed: discord.Embed = None, file: discord.File = None):
    pass

class Research(commands.Cog, name="Research"):
    """Research module"""

    with open(os.path.join(dir_path, "data/tech_tree_map.json")) as file:
        TECH_TREE_LOCATIONS = json.load(file)

    TREE_BACKGROUND_COLOR = (0,0,0,0)
    BRIGHT_GREEN = (8,179,59,255)
    DARK_GRAY = (30,33,36,255)
    DARK_GREEN = (50,65,48,255)
    CYAN = (98,211,245,255)

    IMAGE_SIZE = (1366, 768)
    CIRCLE_RADIUS = 75
    ARC_WIDTH = 9
    LINE_WIDTH = 7

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot_send = temp_bot_send

    def set_bot_send(self, bot_send):
        self.bot_send = bot_send

    def cog_load(self):

        # print loaded
        print(f"cog: {self.qualified_name} loaded")

        # start loop
        self.update_all_research_queues.start()

    @tasks.loop(minutes=10)
    async def update_all_research_queues(self):
        Player.update_all_research_queues()

    @commands.command()
    @commands.is_owner()
    async def forceendqueue(self, ctx: commands.Context, usr: discord.Member = None):
        if usr is None:
            player = Player(ctx.author)
        else:
            player = Player(usr)
        player.force_end_queue()
        await self.bot_send(ctx, "Done!")

    @commands.command()
    @commands.is_owner()
    async def getresearch(self, ctx: commands.Context, usr: discord.Member = None):
        if usr is None:
            player = Player(ctx.author)
        else:
            player = Player(usr)
        await self.bot_send(ctx, str(player.get_research_data()))

    @commands.command()
    @commands.is_owner()
    async def deleteresearch(self, ctx: commands.Context, usr: discord.Member = None):
        if usr is None:
            player = Player(ctx.author)
        else:
            player = Player(usr)
        player.remove_all_research()
        await self.bot_send(ctx, "Done!")

    @commands.command(aliases=["rs"])
    @Checks.in_bb_channel()
    async def research_shop(self, ctx: commands.Context, code: str = None):
        """
        See what tech you can research. 
        Use `bb research_shop <code>` to see more about a specific item.
        """
        player = Player(ctx.author)
        embed = discord.Embed(color=discord.Color.dark_gold())

        available = player.get_available_research()
        icon = None

        if code is None:

            embed.title = "Research Workstation"

            embed.description = f"You have {len(available)} research options open"
        
            queue = player.get_research_queue()
            if queue[0] is not None:
                embed.description += ", but your queue is currently full"
            
            embed.description += ".\nUse `bb research_shop <code>` to see "+\
                "details, or `bb research <code>` to begin research."

            for techid, level in available.items():
                tech = Player.RESEARCH_CONFIG[techid]
                embed.add_field(
                    name = tech["name"] + f" - Code: `{tech['short_code']}`",
                    value = f"**Time:** {tech['time'][level-1]} hours" +\
                        f"\n**Cost:** {tech['costs'][level-1]}{ED.BARREL_COIN}\n" +\
                        f"**Level:** {level-1} -> {level}"
                )

        else:

            techid = Player.get_tech_from_short_code(code)
            tech = Player.RESEARCH_CONFIG[techid]
            embed.title = tech["name"] + f" - Code: `{tech['short_code']}`"
            cur_lvl = player.get_current_level(techid)

            icon = discord.File(os.path.join(dir_path, tech["icon"]), filename="icon.png")
            embed.set_thumbnail(url="attachment://icon.png")

            if techid in available.keys():
                level = available[techid]
                embed.description = f"**Time:** {tech['time'][level-1]} hours" +\
                    f"\n**Cost:** {tech['costs'][level-1]}{ED.BARREL_COIN}\n" +\
                    f"**Level:** {level-1} -> {level} (maximum " +\
                    f"{len(tech['prereqs'])})\n**Description:** " + tech['info']
            else:
                embed.description = f"**Level:** {cur_lvl} / " +\
                    f"{len(tech['prereqs'])}\n**Description:** " + tech['info']

            match techid:
                case "work_multiplier":
                    embed.description += f"\n**Current Multiplier:** {work_multiplier(cur_lvl):.2f}"
                case "shop_sale_increase":
                    embed.description += f"\n**Current Multiplier:** {shopitem_saleprice_multiplier(cur_lvl):.2f}"
                case "fish_sale_increase":
                    embed.description += f"\n**Current Multiplier:** {fish_saleprice_multiplier(cur_lvl):.2f}"
                case "rent_multiplier":
                    embed.description += f"\n**Current Multiplier:** {rent_multiplier(cur_lvl):.2f}"
                case "rent_time_increase":
                    embed.description += f"\n**Current Maximum:** {1 + cur_lvl} " + str("day" if cur_lvl == 0 else "days")
                case "rod_limit_increase":
                    embed.description += f"\n**Current Limit:** {3 + cur_lvl}"

        bal = player.balance
        bank_bal = player.bank_balance
        emoji = self.bot.get_emoji(int(re.search(r"(\d+)>", ED.BARREL_COIN).group(1)))
        embed.set_footer(text=f"Balance: {bal}, In bank: {bank_bal}", icon_url=emoji.url)
        await self.bot_send(ctx, embed=embed, file=icon)

    @commands.command()
    @Checks.in_bb_channel()
    async def research(self, ctx: commands.Context, code: str):
        """
        Begin research on the next level of a given technology.
        See `bb research_shop` for appropriate codes.
        """
        player = Player(ctx.author)
        try:
            player.begin_research(code)
            await self.bot_send(ctx, "Done! Use `bb research_queue` to see progress.")
        except KeyError:
            await self.bot_send(ctx, "Not a valid tech id. Check the shop again")
        except ResearchQueueFull:
            await self.bot_send(ctx, "Research queue full. "
                "You'll need to wait until your current research is finished.")
        except MissingPrerequisites as e:
            await self.bot_send(ctx, str(e))
        except NotEnoughCoins:
            await self.bot_send(ctx, "Not enough coins. You might need to withdraw from the bank.")
        except IndexError:
            await self.bot_send(ctx, "You've reached the max level of that technology.")
        except Exception as e:
            await self.bot_send(ctx, str(e.with_traceback(None)))

    @commands.command(aliases=["rq"])
    @Checks.in_bb_channel()
    async def research_queue(self, ctx: commands.Context):
        """
        See what's in your research queue.
        """

        player = Player(ctx.author)
        queue = player.get_research_queue()

        if queue[0] is None:
            await self.bot_send(ctx, "Your queue is currently empty.")
            return
        
        tech_id = Player.get_tech_from_short_code(queue[0])
        tech_name = Player.RESEARCH_CONFIG[tech_id]["name"]
        done = queue[1]
        now = time.time()
        diff = done-now

        current_level = player.get_current_level(tech_id)
        progress = min(1, 1-diff/Player.RESEARCH_CONFIG[tech_id]["time"][current_level]/3600)

        embed = discord.Embed(color=discord.Color.dark_gold())
        embed.title = "Research Queue"
        embed.description = f"{tech_name}\nLevel {current_level+1}\nDone at "+\
            f"<t:{int(done)}:f> - <t:{int(done)}:R>"
        
        # basic image
        im_size = (512, 32)
        im = Image.new("RGBA", im_size, (0,0,0,0))
        draw = ImageDraw.Draw(im)
        
        # use circles and flood fill to create background
        color = Research.DARK_GRAY
        diam = im_size[1]-1
        x, y = 0, 0
        draw.ellipse([x,y,x+diam,y+diam], fill=color)
        x += int(im_size[0] - im_size[1])
        draw.ellipse([x,y,x+diam,y+diam], fill=color)
        ImageDraw.floodfill(im, xy=(im_size[0]//2, im_size[1]//2), value=color, thresh=40)

        # same technique to create progress bar
        color = Research.CYAN
        diam = im_size[1]-1
        x, y = 0, 0
        draw.ellipse([x,y,x+diam,y+diam], fill=color, width=0)
        x += int((im_size[0] - diam)*progress)
        draw.ellipse([x,y,x+diam,y+diam], fill=color, width=0)

        if x != 0:
            ImageDraw.floodfill(im, xy=(diam//2+x//2, 1), value=color, thresh=40)
            ImageDraw.floodfill(im, xy=(diam//2+x//2, im_size[1]-1), value=color, thresh=40)

        image_stream = BytesIO()
        im.save(image_stream, format="PNG")
        image_stream.seek(0)

        image = discord.File(image_stream, filename="progress_bar.png")
        embed.set_image(url="attachment://progress_bar.png")

        embed.set_footer(text="Note that research queues may take up to 10 minutes to update.")

        await self.bot_send(ctx, embed=embed, file=image)

    @commands.command(aliases=["techtree", "tt"])
    @Checks.in_bb_channel()
    async def view_tech_tree(self, ctx:commands.Context):
        """
        View your current tech tree.
        """
        player = Player(ctx.author)

        image_stream = get_tech_tree(player)

        image = discord.File(image_stream, filename="tech_tree.png")
        emb = discord.Embed(color=discord.Colour.dark_gold(), title=f"{ctx.author.display_name}'s Tech Tree")
        emb.set_image(url="attachment://tech_tree.png")

        await self.bot_send(ctx, embed=emb, file=image)
        
    @commands.command(aliases=["techtreedetails", "ttd"])
    @Checks.in_bb_channel()
    async def view_tech_tree_details(self, ctx:commands.Context):
        """
        View the details of your current tech tree.
        """
        player = Player(ctx.author)

        emb = discord.Embed(color=discord.Colour.dark_gold(), title=f"{ctx.author.display_name}'s Tech Tree",
                            description="")

        research_data = player.get_research_data()
        available = player.get_available_research()
        
        to_show = {k: 0 for k in available.keys()}
        to_show.update(
            {k: v for k, v in research_data.items() if  k not in [
                "in_progress_id", "in_progress_ts"
            ] and v > 0}
        )
        
        for k, v in to_show.items():
            emb.description += f"\n`{Player.RESEARCH_CONFIG[k]['short_code']}` "+\
                f"{Player.RESEARCH_CONFIG[k]['name']}: "+\
                f"Level {v}/{len(Player.RESEARCH_CONFIG[k]['prereqs'])}"
            match k:
                case "work_multiplier":
                    emb.description += f" - Current Multiplier: {work_multiplier(v):.2f}"
                case "shop_sale_increase":
                    emb.description += f" - Current Multiplier: {shopitem_saleprice_multiplier(v):.2f}"
                case "fish_sale_increase":
                    emb.description += f" - Current Multiplier: {fish_saleprice_multiplier(v):.2f}"
                case "rent_multiplier":
                    emb.description += f" - Current Multiplier: {rent_multiplier(v):.2f}"
                case "rent_time_increase":
                    emb.description += f" - Current Maximum: {1 + v} " + str("day" if v == 0 else "days")
                case "rod_limit_increase":
                    emb.description += f" - Current Limit: {3 + v}"
            if Player.RESEARCH_CONFIG[k]["short_code"] == research_data["in_progress_id"]:
                emb.description += " - UPGRADE IN PROGRESS"

        await self.bot_send(ctx, embed=emb)

def get_tech_tree(player:Player) -> BytesIO:

    research_data = player.get_research_data()
    available = player.get_available_research()

    im = Image.new("RGBA", Research.IMAGE_SIZE, Research.TREE_BACKGROUND_COLOR)
    draw = ImageDraw.Draw(im)

    prereq_connections = {
        "bl": [],
        "fl": ["bl"],
        "wl": ["bl"],
        "wm": ["wl"],
        "rl": ["bl"],
        "ssi": [],
        "fsi": ["ssi"],
        "rli": ["fsi", "fl"],
        "rti": [],
        "rm": ["rti"]
    }

    drawn = []

    for tech_id, _ in reversed(available.items()):
        cur_lvl = research_data[tech_id]
        tech = Player.RESEARCH_CONFIG[tech_id]
        tech_code = tech['short_code']
        position = Research.TECH_TREE_LOCATIONS[tech_code]
        for conn in prereq_connections[tech_code]:
            draw_line(draw, position, Research.TECH_TREE_LOCATIONS[conn], 
                      Research.BRIGHT_GREEN)
        draw_arc(draw, position, cur_lvl/len(tech['prereqs']), 
                 Research.DARK_GRAY, Research.BRIGHT_GREEN, 
                 Research.DARK_GREEN, tech_id, im)
        drawn.append(tech_id)

    for tech_id, cur_lvl in reversed(research_data.items()):
        if tech_id not in Player.RESEARCH_CONFIG.keys() or cur_lvl == 0 or tech_id in drawn:
            continue
        tech = Player.RESEARCH_CONFIG[tech_id]
        tech_code = tech['short_code']
        position = Research.TECH_TREE_LOCATIONS[tech_code]
        for conn in prereq_connections[tech_code]:
            draw_line(draw, position, Research.TECH_TREE_LOCATIONS[conn], 
                      Research.BRIGHT_GREEN)
        draw_arc(draw, position, cur_lvl/len(tech['prereqs']), 
                 Research.DARK_GRAY, Research.BRIGHT_GREEN, 
                 Research.DARK_GREEN, tech_id, im)

    if research_data["in_progress_id"] is not None:
        tech_id = Player.get_tech_from_short_code(research_data["in_progress_id"])
        cur_lvl = research_data[tech_id]

        done = research_data["in_progress_ts"]
        now = time.time()
        diff = done-now
        progress = min(1, 1-diff/Player.RESEARCH_CONFIG[tech_id]["time"][cur_lvl]/3600)

        new_lvl = cur_lvl+progress
        max_lvl = len(Player.RESEARCH_CONFIG[tech_id]["prereqs"])
        pos = Research.TECH_TREE_LOCATIONS[research_data["in_progress_id"]]
        draw.arc(
            [pos[0], pos[1], pos[0]+2*Research.CIRCLE_RADIUS, 
             pos[1]+2*Research.CIRCLE_RADIUS], 
            start=cur_lvl/max_lvl*360-90, 
            end=new_lvl/max_lvl*360-90,
            fill=Research.CYAN,
            width=Research.ARC_WIDTH
        ) 

    image_stream = BytesIO()
    im.save(image_stream, format="PNG")
    image_stream.seek(0)

    return image_stream

def draw_arc(draw:ImageDraw.ImageDraw, xy, fraction, ol_color1, ol_color2, fill_color, name=None, img:Image.Image=None):
    draw.ellipse(
        [xy[0], xy[1], xy[0]+2*Research.CIRCLE_RADIUS, 
         xy[1]+2*Research.CIRCLE_RADIUS], 
        fill=fill_color, 
        outline=ol_color1, 
        width=Research.ARC_WIDTH
    )
    draw.arc(
        [xy[0], xy[1], xy[0]+2*Research.CIRCLE_RADIUS, 
         xy[1]+2*Research.CIRCLE_RADIUS], 
        start=-90, 
        end=fraction*360-90,
        fill=ol_color2,
        width=Research.ARC_WIDTH
    )    
    if name is not None and img is not None:
        path = os.path.join(dir_path, Player.RESEARCH_CONFIG[name]["icon"])
        icon = Image.open(path)
        icon = icon.convert("RGBA")
        center = [i+Research.CIRCLE_RADIUS for i in xy]
        bounding_box = [int(round(c+Research.CIRCLE_RADIUS*i)) for i in [-0.6, 0.6] for c in center]
        new_size = (bounding_box[2]-bounding_box[0], bounding_box[3]-bounding_box[1])
        icon = icon.resize(new_size)
        img.paste(icon, bounding_box, mask=icon)

def draw_line(draw:ImageDraw.ImageDraw, xy, xy2, color):
    draw.line([xy[0]+Research.CIRCLE_RADIUS,xy[1]+Research.CIRCLE_RADIUS,
               xy2[0]+Research.CIRCLE_RADIUS,xy2[1]+Research.CIRCLE_RADIUS], 
               fill=color, width=Research.LINE_WIDTH)