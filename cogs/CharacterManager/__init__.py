from .cog import CharacterManager


def setup(bot):
    bot.add_cog(CharacterManager(bot))
