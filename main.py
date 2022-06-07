import os

import d20
import discord
from discord.ext import commands


async def get_prefix(the_bot, message):
    return ">"


class Infactum(commands.Bot):
    def __init__(self, prefix, description=None, **options):
        super().__init__(
            prefix,
            # help_command=help_command, # TODO: Help Command
            description=description,
            **options,
        )
        self.muted = set()


# for cog in COGS:
#     bot.load_extension(cog)

# def main(name):
#     try:
#         test = d20.roll("1d")
#     except d20.RollSyntaxError as e:
#         print(f"Error: {e}")
#     print(test)

desc = (
    "A Funny Good Description"  # TODO: Write said funny and good description
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


for filename in os.listdir('cogs'):
    print(filename)
    if filename.startswith('.'):
        bot.load_extension(f'cogs.{filename}')

if __name__ == '__main__':
    bot.run(os.environ.get("NIGHTLY_TOKEN", ""))
