# Code by https://github.com/wdlord

import discord
from discord.ext import commands


class PokerollCommands(commands.Cog):
    """
    Contains commands that are used to participate in the pokeroll.
    """

    def __init__(self, bot):
        self.bot = bot

    async def load(self):
        """
        Utility function for initializing our cache of guild configs.
        Called in on_ready() event.
        """

        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Triggers when this cog is connected and ready.
        """

        print(f"{__name__} is connected!")
        await self.load()


async def setup(bot):
    """
    Triggered when we load this class as an extension of the bot in main.py.
    """

    if bot.testing:
        await bot.add_cog(PokerollCommands(bot), guilds=[discord.Object(id=864728010132947015)])
    else:
        await bot.add_cog(PokerollCommands(bot))
