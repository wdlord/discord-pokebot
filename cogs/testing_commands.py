# Code by https://github.com/wdlord

import discord
from discord.ext import commands
from cogs.encounters import run_encounter
from database import POKEMON_DB
from pokeapi import get_pokemon


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
        Test command to reset a user's rolls.
        """

        POKEMON_DB.reset_user_rolls(interaction.user)
        await interaction.response.send_message("Your rolls have been reset.", ephemeral=True)

    @discord.app_commands.command()
    async def give(self, interaction: discord.Interaction, pokemon_name: str, is_shiny: bool):
        """
        Gives the user one of the specified Pokémon.
        """

        pokemon_name = pokemon_name.lower().strip()
        pokemon = get_pokemon(pokemon_name)

        if not pokemon:
            await interaction.response.send_message("Could not find that Pokémon.", ephemeral=True)

        else:
            POKEMON_DB.add_pokemon(interaction.user, pokemon_name, is_shiny)
            await interaction.response.send_message(f"{pokemon_name} was added to your Pokédex.", ephemeral=True)

    # TODO: /berries

    # TODO: /tree <pokemon> ?


async def setup(bot):
    """
    Triggered when we load this class as an extension of the bot in main.py.
    """

    # This cog should only sync its commands to the testing server.
    await bot.add_cog(TestingCommands(bot), guilds=[discord.Object(id=864728010132947015)])
