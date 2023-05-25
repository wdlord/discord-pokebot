# Code by https://github.com/wdlord

import discord
from discord.ext import commands
from cogs.encounters import run_encounter
from database import POKEMON_DB


class TestingCommands(commands.Cog):
    """
    Test commands that should not be available to normal users.
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

    @discord.app_commands.command()
    async def en(self, interaction: discord.Interaction):
        """
        Test command to trigger an encounter.
        In an encounter, a random Pokémon appears, and the user can click a button to capture it.
        """

        await run_encounter(interaction.channel)
        await interaction.response.defer()

    @discord.app_commands.command()
    async def reset(self, interaction: discord.Interaction):
        """
        Test command to reset all the rolls.
        """

        POKEMON_DB.reset_user_rolls(interaction.user)
        await interaction.response.send_message("Your rolls have been reset.", ephemeral=True)


async def setup(bot):
    """
    Triggered when we load this class as an extension of the bot in main.py.
    """

    # This class only syncs its commands to the specified guild.
    await bot.add_cog(TestingCommands(bot), guilds=[discord.Object(id=864728010132947015)])
