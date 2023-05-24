# Code by https://github.com/wdlord

import discord
from discord.ext import commands
from pokeapi import get_pokemon, type_to_color, type_to_icon
from database import POKEMON_DB
import random


class PokerollCard(discord.ui.View):
    """
    This is the view for a card (including Next button) in the pokéroll.
    """

    def __init__(self, remaining_rolls):
        super().__init__()
        self.remaining_rolls = remaining_rolls

    @discord.ui.button(label='Next', style=discord.ButtonStyle.green)
    async def card_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Defines the interaction when the Next button is clicked during pokéroll.
        """

        await roll_pokemon(interaction, self.remaining_rolls)
        self.stop()


class PokemonSearchCard(discord.ui.View):
    """
    View for a card that appears when searching a Pokémon.
    """

    def __init__(self, pokemon: dict, pokemon_data: dict):
        super().__init__()
        self.is_shiny = False
        self.message: discord.Message = None
        self.pokemon = pokemon
        self.pokemon_data = pokemon_data

    def make_card(self) -> discord.Embed:
        """
        Generates an embed object showing a Pokémon and the user's stats for that Pokémon.
        """

        # Gathers/formats some data to include in the embed.
        type_color = type_to_color[self.pokemon['types'][0]['type']['name']]
        desc = (
            f"{''.join(type_to_icon[t['type']['name']] for t in self.pokemon['types'])}"
            f"\nNormals Owned: {self.pokemon_data['normal']}"
            f"\nShinies Owned: {self.pokemon_data['shiny']}"
        )
        embed = discord.Embed(description=desc, color=type_color, title=f"{self.pokemon['name'].title()}")

        # Try to use an animated version of the sprite, but one may not exist.
        sprite_url = (
                self.pokemon['sprites']['versions']['generation-v']['black-white']['animated']['front_shiny' if self.is_shiny else 'front_default']
                or
                self.pokemon['sprites']['front_shiny' if self.is_shiny else 'front_default']
        )

        embed.set_image(url=sprite_url)

        return embed

    async def send_card(self, interaction: discord.Interaction):
        """
        Sends original message that shows the view. We do it within the class to save the message locally.

        :param interaction: The interaction of the command used.
        :return:
        """

        await interaction.response.send_message(embed=self.make_card(), view=self)
        self.message = await interaction.original_response()

    @discord.ui.button(label='View Shiny', style=discord.ButtonStyle.green)
    async def toggle_shiny_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        A Button that toggles between the default and shiny sprites for the Pokémon.
        """

        self.is_shiny = not self.is_shiny
        button.label = 'View Normal' if self.is_shiny else 'View Shiny'

        await self.message.edit(embed=self.make_card(), view=self)
        await interaction.response.defer()


async def roll_pokemon(interaction: discord.Interaction, remaining_rolls: int):
    """
    Generates new cards until the user is out of rolls.
    The interaction arg is either the interaction from the initial command, or from the Next buttons.
    """

    # Fetches a random Pokémon from the pokeapi.
    pokemon = get_pokemon()

    # Determine if Pokémon is shiny.
    is_shiny = random.random() < 0.01

    # Gathers/formats some data to include in the embed.
    type_color = type_to_color[pokemon['types'][0]['type']['name']]
    desc = (
        f"{''.join(type_to_icon[t['type']['name']] for t in pokemon['types'])}"
    )
    desc += "\n✨Shiny✨" if is_shiny else ""

    embed = discord.Embed(description=desc, color=type_color, title=f"{pokemon['name'].title()}")

    # Try to use an animated version of the sprite, but one may not exist.
    sprite_url = (
            pokemon['sprites']['versions']['generation-v']['black-white']['animated']['front_shiny' if is_shiny else 'front_default']
            or
            pokemon['sprites']['front_shiny' if is_shiny else 'front_default']
    )

    embed.set_image(url=sprite_url)

    # Add the Pokémon to the user's Pokédex.
    POKEMON_DB.add_pokemon(interaction.user, pokemon['name'], shiny=is_shiny)

    # If the user still has more cards to open, we recursively create another card.
    if remaining_rolls > 0:
        view = PokerollCard(remaining_rolls - 1)
        await interaction.response.send_message(embed=embed, view=view)

    # Else we only have to send this card without a 'Next' button.
    else:
        await interaction.response.send_message(embed=embed)


class PokerollCommands(commands.Cog):
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
    async def roll(self, interaction: discord.Interaction):
        """
        Roll a set of Pokémon to add to your Pokédex.
        """

        # rolls one Pokémon at a time, click the next button to continue.
        await roll_pokemon(interaction, 2)

    @discord.app_commands.command()
    async def search(self, interaction: discord.Interaction, name: str):
        """
        Search a Pokémon by name.
        """

        name = name.lower().strip()
        pokemon = get_pokemon(name)

        # Behavior if the lookup failed.
        if not pokemon:
            await interaction.response.send_message("We couldn't find that pokemon.", ephemeral=True)

        # Behavior if the lookup succeeded.
        else:
            pokemon_data = POKEMON_DB.get_pokemon_data(interaction.user, pokemon['name'])
            search_card = PokemonSearchCard(pokemon, pokemon_data)
            await search_card.send_card(interaction)


async def setup(bot):
    """
    Triggered when we load this class as an extension of the bot in main.py.
    """

    if bot.testing:
        await bot.add_cog(PokerollCommands(bot), guilds=[discord.Object(id=864728010132947015)])
    else:
        await bot.add_cog(PokerollCommands(bot))
