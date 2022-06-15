from utils.errors import GuildPermissionError


def is_admin(author):
    if not author.guild_permissions.administrator:
        raise GuildPermissionError("YOU CAN NOT CHANGE GUILD PREFIX WITHOUT ADMINISTRATOR PRIVILEGES")
