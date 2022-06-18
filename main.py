import os
import traceback

import d20
import discord
from discord.ext import commands
from discord.ext.commands import CommandInvokeError

from utils import config
from utils import csvUtils
from utils.errors import InfactumException


# TODO Emoji, Init Command, Help Command, Character Stuff, Iteroll

async def get_prefix(the_bot, message):
    if not message.guild:
        return commands.when_mentioned_or(config.DEFAULT_PREFIX)(the_bot, message)
    gp = await the_bot.get_guild_prefix(message.guild)
    return commands.when_mentioned_or(gp)(the_bot, message)
    pass


def make_error(message, error: bool = False):
    return f"```{'css' if error else 'fix'}\n[ERROR: {message}]\n```"


class Infactum(commands.Bot):
    def __init__(self, prefix, description=None, **options):
        super().__init__(
            prefix,
            # help_command=help_command,  # TODO: Help Command
            description=description,
            **options,
        )
        self.prefixes = dict()

    async def get_guild_prefix(self, guild: discord.Guild) -> str:
        guild_id = str(guild.id)
        if guild_id in self.prefixes:
            return self.prefixes.get(guild_id, config.DEFAULT_PREFIX)

        gp = csvUtils.search_csv(guild_id, "db/prefixes.csv")
        if gp is None:
            gp = config.DEFAULT_PREFIX
        self.prefixes[guild_id] = gp
        return gp

    async def close(self):
        print("Close")


desc = (
    "A bot for managing rolls and characters for [Insert System Here]"  # TODO: Write said funny and good description
)

intents = discord.Intents(
    guilds=True,
    members=True,
    messages=True,
    reactions=True,
    bans=False,
    emojis=False,
    integrations=False,
    webhooks=False,
    invites=False,
    voice_states=False,
    presences=False,
    typing=False,
)  # https://discord.com/developers/docs/topics/gateway#gateway-intents
bot = Infactum(
    prefix=get_prefix,
    description=desc,
    activity=discord.Activity(type=discord.ActivityType.listening, name='eldritch screams'),
    allowed_mentions=discord.AllowedMentions.none(),
    intents=intents,
    chunk_guilds_at_startup=False,
)


@bot.event
async def on_ready():
    print(f"Logged in as - \"{bot.user.name}\" - {bot.user.id}")
    print(f'Infactum has awoken in {len(bot.guilds)} servers')


@bot.event
async def on_resumed():
    print("Resumed")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, InfactumException):
        return await ctx.send(make_error(error))
    elif isinstance(error, (commands.UserInputError, commands.NoPrivateMessage, ValueError)):
        return await ctx.send(make_error(f"COMMAND ERROR: {str(error)}\n"
                                         f"Use \"{ctx.prefix}help " + ctx.command.qualified_name + "\" for help."))
    elif isinstance(error, CommandInvokeError):
        original = error.original
        if isinstance(original, d20.RollError):
            return await ctx.send(make_error(f"ROLL ERROR - {original}"))
        elif isinstance(original, InfactumException):
            return await ctx.send(make_error(original))

    await ctx.send(
        make_error(f"UNEXPECTED ERROR!", True)  # TODO Add unexpected error text
        #  discord.Embed(title="You've Found Bug!", url="https://discord.gg/GzawEqQ",
        #  description="Join the dev discord server to report what happened!")
    )
    print(traceback.print_exception(type(error), error, error.__traceback__))


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    ctx = await bot.get_context(message)
    if ctx.valid:
        await bot.invoke(ctx)
    elif ctx.invoked_with:
        pass  # TODO: Add Aliases


for dir_name in os.listdir('cogs'):
    if dir_name != "__pycache__":
        bot.load_extension(f'cogs.{dir_name}')

if __name__ == '__main__':
    bot.run(config.BOT_TOKEN)
