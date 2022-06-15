from .cog import GSheet


def setup(bot):
    bot.add_cog(GSheet(bot))
