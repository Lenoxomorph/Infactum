import os

import d20
import discord
from discord.ext import commands
from discord.ext.commands import CommandInvokeError

from utils import config
from utils import functions


# TODO Init Command, Prefix, Help Command, Emoji, Character Stuff

async def get_prefix(the_bot, message):
    return ">"


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
        self.muted = set()


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
    elif isinstance(error, CommandInvokeError):
        original = error.original
        if isinstance(original, d20.RollError):
            return await ctx.send(make_error(f"ROLL ERROR - {original}"))

    await ctx.send(
        make_error(f"UNEXPECTED ERROR!", True)  # TODO Add unexpected error text
        #  discord.Embed(title="You've Found Bug!", url="https://discord.gg/GzawEqQ",
        #  description="Join the dev discord server to report what happened!")
    )


@bot.event
async def on_message(message):
    if message.author.id in bot.muted:
        return

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
    bot.run(os.environ.get("BOT_TOKEN", ""))
