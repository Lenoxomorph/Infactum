from discord.ext import commands

from utils.csvUtils import edit_csv
from utils.dice import get_emoji
from utils.functions import change_text
from .utils import is_admin


class Customization(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    async def prefix(self, ctx, prefix: str = None):
        """"""  # TODO Add Description

        guild_id = str(ctx.guild.id)
        if prefix is None:
            return await ctx.send(f"CURRENT PREFIX - {ctx.prefix}")

        is_admin(ctx.author)

        self.bot.prefixes[guild_id] = prefix

        edit_csv((guild_id, prefix), "db/prefixes.csv")

        await ctx.send(change_text(f"CHANGED SERVER PREFIX TO: {prefix}"))

    @commands.command()
    async def emoji(self, ctx, emoji: str = None):
        """"""  # TODO Add Description

        author_id = str(ctx.author.id)
        if emoji is None:
            return await ctx.send(f"CURRENT EMOJI - {get_emoji(author_id)}")

        edit_csv((author_id, emoji), "db/emojis.csv")

        await ctx.send(change_text(f"CHANGED USER'S EMOJI TO: {emoji}"))
