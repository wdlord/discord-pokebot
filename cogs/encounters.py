# Code by https://github.com/wdlord

import discord
from discord.ext import commands
import constants
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
        Defines the interaction when the Next button is clicked when rolling Pokémon.
        """

        # Each user can only claim once during this encounter.
        if interaction.user.id in self.claimed_by:
            await interaction.response.send_message("You've already claimed this Pokémon.", ephemeral=True)

        # Add the Pokémon to the user's Pokédex if they have not already claimed it.
        else:
            POKEMON_DB.add_pokemon(interaction.user, self.pokemon['name'], self.is_shiny)
            self.claimed_by.append(interaction.user.id)
            await interaction.response.send_message(f"{interaction.user.name} claimed **{self.pokemon['name'].title()}**!")


async def make_file(pokemon: dict, is_shiny: bool) -> discord.File:
    """
    Makes a discord.File object for a Pokémon's image sprite.
    Externally hosted images must be downloaded to a discord.File object to be sent directly to a channel.
    (This is not necessary if the image is being sent in an embed.)
    https://discordpy.readthedocs.io/en/stable/faq.html#how-do-i-upload-an-image
    """

    import io
    import aiohttp

    sprite_url = constants.get_sprite(pokemon, is_shiny)
    extension = "gif" if sprite_url.endswith(".gif") else "png"

    async with aiohttp.ClientSession() as session:
        async with session.get(sprite_url) as resp:
            if resp.status != 200:
                print("Could not download file...")

            else:
                data = io.BytesIO(await resp.read())
                return discord.File(data, f"{pokemon['name']}.{extension}")


async def run_encounter(channel: discord.TextChannel):
    """
    In an encounter, a random Pokémon appears, and the user can click a button to capture it.
    This code is encapsulated in its own function so that it can be run separately from a testing command.

    :param channel: The text channel where the encounter will occur.
    :return:
    """

    pokemon = get_pokemon()
    is_shiny = random.random() < constants.SHINY_CHANCE

    alert = f"A wild **{pokemon['name'].title()}** appeared!"

    pokemon_sprite = await make_file(pokemon, is_shiny)
    grass_sprite = discord.File("./grass_small.png")

    # This view displays our Pokémon and a 'Catch' button.
    # The code that handles the button interaction is also in this class.
    view = EncounterView(pokemon, is_shiny)

    # The encounter is sent in two separate messages:
    # The first is the alert and the Pokémon sprite.
    # The second is the grass sprite with the 'Catch' button view attached.
    # It's sent in separate messages because the images won't display properly in the same message.
    await channel.send(alert, file=pokemon_sprite)
    await channel.send(file=grass_sprite, view=view)


class Encounters(commands.Cog):
    """
    Contains commands that are used to participate in the pokéroll.
    """

    def __init__(self, bot):
        self.bot = bot

    async def load(self):
        """
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

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Has a small chance to trigger a random Pokémon encounter.
        In an encounter, a random Pokémon appears, and the user can click a button to capture it.
        """

        # Ignores messages from bots.
        if message.author.bot:
            return

        # Each message has a percentage chance to trigger an encounter.
        if random.random() < constants.ENCOUNTER_CHANCE:
            await run_encounter(message.channel)


async def setup(bot):
    """
    Triggered when we load this class as an extension of the bot in main.py.
    """

    if bot.testing:
        await bot.add_cog(Encounters(bot), guilds=[discord.Object(id=864728010132947015)])
    else:
        await bot.add_cog(Encounters(bot))
