import discord


async def try_delete(message):
    try:
        await message.delete()
    except discord.HTTPException:
        pass


def change_text(text):
    return f"```ini\n[{text}]\n```"
