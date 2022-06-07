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
            # help_command=help_command,
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
    "Play D&D over Discord! Featuring advanced dice, initiative tracking, D&D Beyond integration, and more, you'll"
    " never need another D&D bot.\nView the full list of commands [here](https://avrae.io/commands)!\nInvite Avrae to"
    " your server [here](https://invite.avrae.io)!\nJoin the official development server"
    " [here](https://support.avrae.io)!\n[Privacy"
    " Policy](https://company.wizards.com/en/legal/wizards-coasts-privacy-policy) | [Terms of"
    " Use](https://company.wizards.com/en/legal/terms)"
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
    # intents=intents,
    # status
    # chunk_guilds_at_startup=False,
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


@bot.command()
async def get_profile_pic(ctx):
    await ctx.send(ctx.guild.icon_url)


if __name__ == '__main__':
    # bot.state = "run"
    # bot.loop.create_task(compendium.reload_task(bot.mdb))
    bot.run(os.environ.get("MAIN_TOKEN", ""))

