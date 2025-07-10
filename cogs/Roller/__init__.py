from .cog import Roller


async def setup(bot):
    await bot.add_cog(Roller(bot))
