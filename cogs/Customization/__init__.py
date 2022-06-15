from .cog import Customization


def setup(bot):
    bot.add_cog(Customization(bot))
