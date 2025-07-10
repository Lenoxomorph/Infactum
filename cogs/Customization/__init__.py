from .cog import Customization


async def setup(bot):
    await bot.add_cog(Customization(bot))
