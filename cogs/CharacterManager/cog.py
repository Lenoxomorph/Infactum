import re

from discord.ext import commands

from cogs.CharacterManager.utils import PointBuyer
from cogs.Roller.utils import roll_many
from utils.csvUtils import search_csv
from utils.errors import ExternalImportError, ArgumentError
from utils.config import SYSTEM_ABV
from utils.functions import try_delete

URL_KEY_V1_RE = re.compile(r"key=([^&#]+)")
URL_KEY_V2_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9-_]+)")

MAIN_POINT_BUYER = PointBuyer(SYSTEM_ABV, 10, (6, 18), (14, 16), 16)
DND_POINT_BUYER = PointBuyer("D&D", 8, (8, 15), (13,), 27)


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
        await ctx.send(key)

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
                    points = int(arg[6:])
                except ValueError:
                    raise ArgumentError("YOU MUST PUT A NUMBER AFTER THE ARGUMENT '-points'")
        await try_delete(ctx.message)
        test = await buyer.embed(ctx, points)
        await test.add_reaction("✅")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id != self.bot.user.id:
            if data := search_csv(str(payload.message_id), "db/pointBuyMessages.csv"):
                print(f"HERE! - {data}")
        # test = (await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)).embeds
        # print(test[0].description)
