# Code by https://github.com/wdlord

import discord
from discord.ext import commands
from database import POKEMON_DB
from pokeapi import get_pokemon
import constants
from math import ceil


class PokemonList(discord.ui.View):

    def __init__(self, user: discord.User):
        super().__init__()
        self.user = user
        self.berry_count = POKEMON_DB.num_berries(user)
        self.remaining_rolls = POKEMON_DB.get_remaining_rolls(user)
        self.message: discord.Message = None
        self.pokemon_total = 0
        self.pokemon_list = self.make_pokemon_list()
        self.page = 0
        self.total_pages = ceil(len(self.pokemon_list) / 10)

    def make_pokemon_list(self):
        """
        Converts the Pokémon from the database into a list of formatted lines we will show in the embed.
        """

        user_pokemon = POKEMON_DB.get_all_pokemon(self.user)

        pokemon_list = []

        # Edge case for users who are not in the database.
        if not user_pokemon:
            return pokemon_list

        for name in sorted(user_pokemon.keys()):

            # Show normal versions of this Pokémon.
            normal_total = int(user_pokemon[name]['normal'])
            self.pokemon_total += normal_total

            if normal_total > 0:
                multiplier = f"x{normal_total}" if normal_total > 1 else ""
                pokemon_list.append(f"{name.title()} {multiplier}")

            # Show shiny versions of this Pokémon (if any exist).
            shiny_total = int(user_pokemon[name]['shiny'])
            self.pokemon_total += shiny_total

            if shiny_total > 0:
                multiplier = f"x{shiny_total}" if shiny_total > 1 else ""

                pokemon_list.append(f"{name.title()}✨ {multiplier}")

        return pokemon_list

    def make_embed(self):
        """
        Creates the embed that shows a given page of the user's Pokédex.
        """

        favorite = POKEMON_DB.get_favorite(self.user)
        pokemon = get_pokemon(favorite['name'])

        # Get the color corresponding to the first type of this Pokémon to use as the embed color.
        first_type_name = pokemon['types'][0]['type']['name']
        type_color = constants.TYPE_TO_COLOR[first_type_name]

        # Display some basic information that will show up on every page.
        desc = f"\n{constants.BLUK_BERRY} x{self.berry_count} | 🎲 x{self.remaining_rolls}"

        embed = discord.Embed(description=desc, color=type_color, title=f"{self.user.name}'s Pokédex")

        # Set the embed thumbnail to the user's favorite Pokémon.
        favorite_sprite = (
                pokemon['sprites']['versions']['generation-v']['black-white']['animated']['front_shiny' if favorite['is_shiny'] else 'front_default']
                or
                pokemon['sprites']['front_shiny' if favorite['is_shiny'] else 'front_default']
        )
        embed.set_thumbnail(url=favorite_sprite)

        # Get the slice of the Pokédex to show.
        lower_bound = self.page * 10

        if len(self.pokemon_list) < lower_bound + 10:
            pokedex_slice = self.pokemon_list[lower_bound:]

        else:
            pokedex_slice = self.pokemon_list[lower_bound:lower_bound + 10]

        value = '\n'.join(pokedex_slice)

        embed.add_field(name="", value=value)

        embed.set_footer(text=f"Total: {self.pokemon_total} - Page {self.page + 1} of {self.total_pages}")

        return embed

    def empty_embed(self):
        """
        This embed only appears when a user does not exist in our database.
        """

        desc = "This user does not have any Pokémon."
        embed = discord.Embed(description=desc, color=0x000000, title=f"{self.user.name}'s Pokédex")
        embed.set_footer(text="Total: 0 - Page 0 of 0")

        return embed

    async def send(self, interaction: discord.Interaction):
        """
        Sends original message that shows the view. We do it within the class to save the message locally.

        :param interaction: The interaction of the command used.
        :return:
        """

        embed = self.make_embed() if self.pokemon_list else self.empty_embed()
        await interaction.response.send_message(embed=embed, view=self)
        self.message = await interaction.original_response()

    @discord.ui.button(label='◀', style=discord.ButtonStyle.grey)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Show the previous page when clicked.
        """

        # Special case for users that are not in the database.
        if not self.pokemon_list:
            button.disabled = True
            await interaction.response.defer()
            return

        # Loop around to the end if necessary.
        self.page = self.page - 1 if self.page != 0 else self.total_pages - 1

        # Remake the embed with the next group of Pokémon, and update the message.
        await self.message.edit(embed=self.make_embed(), view=self)

        # We must acknowledge the interaction in some way.
        await interaction.response.defer()

    @discord.ui.button(label='▶', style=discord.ButtonStyle.grey)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Show the next page when clicked.
        """

        # Special case for users that are not in the database.
        if not self.pokemon_list:
            button.disabled = True
            await interaction.response.defer()
            return

        # Loop around to the beginning if necessary.
        self.page = self.page + 1 if self.page != self.total_pages - 1 else 0

        # Remake the embed with the next group of Pokémon, and update the message.
        await self.message.edit(embed=self.make_embed(), view=self)

        # We must acknowledge the interaction in some way.
        await interaction.response.defer()


class NormalOrShiny(discord.ui.View):

    def __init__(self, pokemon_name):
        super().__init__()
        self.pokemon_name = pokemon_name

    @discord.ui.button(label='Normal', style=discord.ButtonStyle.grey)
    async def normal(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Set the normal variant of the Pokémon as the favorite.
        """

        POKEMON_DB.set_favorite(interaction.user, self.pokemon_name, False)
        await interaction.response.send_message(f"{self.pokemon_name.title()} has been set as your favorite Pokémon.", ephemeral=True)
        self.stop()

    @discord.ui.button(label='Shiny', style=discord.ButtonStyle.grey)
    async def shiny(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Set the shiny variant of the Pokémon as the favorite.
        """

        POKEMON_DB.set_favorite(interaction.user, self.pokemon_name, True)
        await interaction.response.send_message(f"{self.pokemon_name.title()} has been set as your favorite Pokémon.", ephemeral=True)
        self.stop()


class Pokedex(commands.Cog):
    """
    Functionality for viewing captured Pokémon.
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
    async def pokedex(self, interaction: discord.Interaction, user: discord.User = None):
        """
        View your captured Pokémon.
        """

        pokedex_view = PokemonList(user or interaction.user)
        await pokedex_view.send(interaction)

    @discord.app_commands.command()
    async def favorite(self, interaction: discord.Interaction, name: str):
        """
        Set the Pokémon that appears in your Pokédex thumbnail.
        """

        name = name.lower().strip()

        pokemon_data = POKEMON_DB.get_pokemon_data(interaction.user, name)

        if not pokemon_data['normal'] and not pokemon_data['shiny']:
            await interaction.response.send_message("You do not own any of that Pokémon.", ephemeral=True)

        elif pokemon_data['normal'] and pokemon_data['shiny']:
            prompt = "Would you like to set the normal or shiny Pokémon as your favorite?"
            await interaction.response.send_message(prompt, view=NormalOrShiny(name), ephemeral=True)

        # if the user only owns a normal OR shiny variant, we don't need to ask them which version to set.
        elif pokemon_data['normal'] or pokemon_data['shiny']:
            POKEMON_DB.set_favorite(interaction.user, name, pokemon_data['shiny'] > 0)
            await interaction.response.send_message(f"**{name.title()}** has been set as your favorite Pokémon.", ephemeral=True)


async def setup(bot):
    """
    Triggered when we load this class as an extension of the bot in main.py.
    """

    if bot.testing:
        await bot.add_cog(Pokedex(bot), guilds=[discord.Object(id=864728010132947015)])
    else:
        await bot.add_cog(Pokedex(bot))
