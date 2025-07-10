from .cog import CharacterManager


async def setup(bot):
    await bot.add_cog(CharacterManager(bot))
