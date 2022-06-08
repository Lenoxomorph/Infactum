from .cog import Roller


def setup(bot):
    bot.add_cog(Roller(bot))
