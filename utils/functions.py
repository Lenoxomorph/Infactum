import discord


async def try_delete(message):
    try:
        await message.delete()
    except discord.HTTPException:
        pass


def change_text(text):
    return f"```ini\n[{text}]\n```"


def search_list(term, s_list):
    exact_matches = [(index, a) for index, a in enumerate(s_list) if term.lower() == a.lower()]
    if exact_matches:
        return exact_matches[0]
    partial_matches = [(index, a) for index, a in enumerate(s_list) if term.lower() in a.lower()]
    if partial_matches:
        return partial_matches[0]
