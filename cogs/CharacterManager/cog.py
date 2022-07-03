import re

from discord.ext import commands

from cogs.Roller.utils import roll_many
from utils.config import SYSTEM_ABV
from utils.csvUtils import search_csv, edit_csv
from utils.errors import ExternalImportError, ArgumentError
from utils.functions import try_delete
from .utils import PointBuyer
from .utils import STAT_LIST

LOWERED_STAT_LIST = [stat.lower() for stat in STAT_LIST]

URL_KEY_V1_RE = re.compile(r"key=([^&#]+)")
URL_KEY_V2_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9-_]+)")

MAIN_POINT_BUYER = PointBuyer(SYSTEM_ABV, 10, (6, 18), (14, 16), 16)
DND_POINT_BUYER = PointBuyer("D&D", 8, (8, 15), (13,), 27)

POINT_BUY_EMOJIS = ["⬆", "⬇", "<:str:986970474087088138>", "<:dex:986970473210449960>", "<:con:986970468840005672>",
                    "<:int:986970471616634900>", "<:wis:986970470563844106>", "<:cha:986970469733400668>"]


def extract_gsheet_id_from_url(url):
    m2 = URL_KEY_V2_RE.search(url)
    if m2:
        return m2.group(1)
    m1 = URL_KEY_V1_RE.search(url)
    if m1:
        return m1.group(1)
    raise ExternalImportError("LINK ERROR - THIS IS NOT A VALID GOOGLE SHEETS LINK")


class CharacterManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="gsheet", aliases=["gs"])
    async def gsheet(self, ctx, url: str):
        """"""  # TODO Add Description
        key = extract_gsheet_id_from_url(url)
        await ctx.send(f"Key is: {key}")

    @commands.command(name="randchar", aliases=["randomcharacter"])
    async def randchar(self, ctx):
        """"""  # TODO Add Description
        await roll_many(ctx, 6, "4d6kh3")

    @commands.command()
    async def pointbuy(self, ctx, *args):
        """"""  # TODO Add Description
        if "-dnd" in args:
            buyer = DND_POINT_BUYER
        else:
            buyer = MAIN_POINT_BUYER
        points = buyer.points
        for arg in args:
            if arg.startswith("-points"):
                try:
                    points = int(arg[7:])
                except ValueError:
                    raise ArgumentError("YOU MUST PUT A NUMBER AFTER THE ARGUMENT '-points'")
        await try_delete(ctx.message)
        test = await buyer.embed(ctx, points)
        [await test.add_reaction(emoji) for emoji in POINT_BUY_EMOJIS]

    @commands.Cog.listener()  # TODO: Make DM's Work, Make Other PPl adding it work
    async def on_raw_reaction_add(self, payload):
        if payload.user_id != self.bot.user.id:
            if data := search_csv(str(payload.message_id), "db/pointBuyMessages.csv"):
                if data[0] == "D&D":
                    buyer = DND_POINT_BUYER
                else:
                    buyer = MAIN_POINT_BUYER
                remove_emoji = payload.emoji
                name = payload.emoji.name
                if "⬆" == name:
                    data = buyer.change_score(data, 1)
                elif "⬇" == name:
                    data = buyer.change_score(data, -1)
                elif name in LOWERED_STAT_LIST:
                    if int(data[2]) >= 0:
                        remove_emoji = POINT_BUY_EMOJIS[int(data[2]) + 2]
                    else:
                        remove_emoji = None
                    data[2] = str(LOWERED_STAT_LIST.index(name))
                else:
                    return
                edit_csv([str(payload.message_id)] + data, "db/pointBuyMessages.csv")
                message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                embed = message.embeds[0]
                embed = buyer.update_description(data, embed)
                await message.edit(embed=embed)
                if remove_emoji:
                    await message.remove_reaction(remove_emoji, (await self.bot.fetch_user(int(data[9]))))
                if int(data[9]) != payload.user_id:
                    data[9] = str(payload.user_id)
                    edit_csv([str(payload.message_id)] + data, "db/pointBuyMessages.csv")
