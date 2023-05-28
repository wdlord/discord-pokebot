# Code by https://github.com/wdlord

import discord
from discord.ext import commands
from pokeapi import get_pokemon
from database import POKEMON_DB
import constants


class PokemonSearchCard(discord.ui.View):
    """
    View that appears when searching a Pokémon.
    Also shows some stats about how many of this Pokémon the user owns.
    """

    def __init__(self, pokemon: dict, pokemon_data: dict):
        super().__init__()
        self.is_shiny = False
        self.message: discord.Message = None
        self.pokemon = pokemon
        self.pokemon_data = pokemon_data

    def make_embed(self) -> discord.Embed:
        """
        Generates an embed object showing a Pokémon and the user's stats for that Pokémon.
        """

        # Get the color corresponding to the first type of this Pokémon to use as the embed color.
        first_type_name = self.pokemon['types'][0]['type']['name']
        type_color = constants.TYPE_TO_COLOR[first_type_name]

        # Set the embed description.
        # Here we add custom discord emotes corresponding to the Pokémon's types.
        # We also show whether the user has any of this Pokémon.
        desc = (
            f"{''.join(constants.TYPE_TO_ICON[t['type']['name']] for t in self.pokemon['types'])}"
            f"\nNormals Owned: {self.pokemon_data['normal']}"
            f"\nShinies Owned: {self.pokemon_data['shiny']}"
        )

        embed = discord.Embed(description=desc, color=type_color, title=f"{self.pokemon['name'].title()}")

        # Set the embed image to the sprite for this Pokémon.
        sprite_url = constants.get_sprite(self.pokemon, self.is_shiny)
        embed.set_image(url=sprite_url)

        return embed

    async def send_card(self, interaction: discord.Interaction):
        """
        Sends original message that shows the view. Done from within the class to save the message locally.

        :param interaction: An active interaction that we can use to send a response.
        """

        await interaction.response.send_message(embed=self.make_embed(), view=self)
        self.message = await interaction.original_response()

    @discord.ui.button(label='View Shiny', style=discord.ButtonStyle.green)
    async def toggle_shiny_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        A Button that toggles between the default and shiny sprites for the Pokémon.
        """

        self.is_shiny = not self.is_shiny
        button.label = 'View Normal' if self.is_shiny else 'View Shiny'

        # Remake the embed with the alternate sprite, and update the message.
        await self.message.edit(embed=self.make_embed(), view=self)

        # We must acknowledge the interaction in some way.
        await interaction.response.defer()


class SearchPokemon(commands.Cog):
    """
    Functionality for searching Pokémon.
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

    @discord.app_commands.command()
    async def search(self, interaction: discord.Interaction, name: str):
        """
        Search a Pokémon by name.
        """

        name = name.lower().strip()
        pokemon = get_pokemon(name)

        if not pokemon:
            await interaction.response.send_message("We couldn't find that pokemon.", ephemeral=True)

        else:
            pokemon_data = POKEMON_DB.get_pokemon_data(interaction.user, pokemon['name'])
            search_card = PokemonSearchCard(pokemon, pokemon_data)
            await search_card.send_card(interaction)


async def setup(bot):
    """
    Triggered when we load this class as an extension of the bot in main.py.
    """

    if bot.testing:
        await bot.add_cog(SearchPokemon(bot), guilds=[discord.Object(id=864728010132947015)])
    else:
        await bot.add_cog(SearchPokemon(bot))
