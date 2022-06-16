import discord
from discord.ext import commands

import re
from utils.errors import ExternalImportError
from cogs.Roller.utils import roll_many

URL_KEY_V1_RE = re.compile(r"key=([^&#]+)")
URL_KEY_V2_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9-_]+)")


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
    async def randchar(self, ctx):  # TODO Add Leveled Rand Char
        """"""  # TODO Add Description
        await roll_many(ctx, 6, "4d6kh3")

    @commands.command()
    async def pointbuy(self, ctx, points: int = 16):  # TODO Add Leveled Rand Char
        """"""  # TODO Add Description
        test = await ctx.send(f"Point BUy Time: {points}")
        await test.add_reaction("✅")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        print("Amogus")
