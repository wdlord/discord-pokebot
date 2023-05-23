# Code by https://github.com/wdlord

import discord
from discord.ext import commands
from pokeapi import get_pokemon
import random
from database import POKEMON_DB


class EncounterView(discord.ui.View):
    """
    This is the view for a card (including Next button) in the pokéroll.
    """

    def __init__(self, pokemon: dict, is_shiny: bool):
        super().__init__()
        self.pokemon = pokemon
        self.is_shiny = is_shiny
        self.claimed_by = []

    @discord.ui.button(label='Catch', style=discord.ButtonStyle.green)
    async def catch(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Defines the interaction when the Next button is clicked during pokéroll.
        """

        # Users can only claim this Pokémon once.
        if interaction.user.id in self.claimed_by:
            await interaction.response.send_message("You've already claimed this Pokémon.", ephemeral=True)

        # Behavior if the user has not yet claimed the Pokémon.
        else:
            POKEMON_DB.add_pokemon(interaction.user, self.pokemon['name'], self.is_shiny)
            self.claimed_by.append(interaction.user.id)
            await interaction.response.send_message(f"{interaction.user.name} claimed {self.pokemon['name'].title()}!")


async def make_file(pokemon: dict, is_shiny: bool) -> discord.File:

    import io
    import aiohttp

    sprite_url = pokemon['sprites']['versions']['generation-v']['black-white']['animated']['front_shiny' if is_shiny else 'front_default']

    if sprite_url:
        extension = "gif"

    else:
        sprite_url = pokemon['sprites']['front_shiny' if is_shiny else 'front_default']
        extension = "png"

    async with aiohttp.ClientSession() as session:
        async with session.get(sprite_url) as resp:
            if resp.status != 200:
                print('Could not download file...')

            else:
                data = io.BytesIO(await resp.read())
                return discord.File(data, f"{pokemon['name']}.{extension}")


class Encounters(commands.Cog):
    """
    Contains commands that are used to participate in the pokéroll.
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
        """

        pokemon = get_pokemon()

        # Determine if Pokémon is shiny.
        is_shiny = random.random() < 0.01

        message = f"A wild **{pokemon['name'].title()}** appeared!"

        pokemon_sprite = await make_file(pokemon, is_shiny)
        grass_sprite = discord.File("./grass_small.png")

        view = EncounterView(pokemon, is_shiny)

        await interaction.response.send_message(message, file=pokemon_sprite)
        await interaction.channel.send(file=grass_sprite, view=view)


async def setup(bot):
    """
    Triggered when we load this class as an extension of the bot in main.py.
    """

    if bot.testing:
        await bot.add_cog(Encounters(bot), guilds=[discord.Object(id=864728010132947015)])
    else:
        await bot.add_cog(Encounters(bot))
