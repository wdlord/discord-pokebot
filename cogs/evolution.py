# Code by https://github.com/wdlord

import discord
from discord.ext import commands
import constants
from pokeapi import get_pokemon, get_evolution_chain
import random
from database import POKEMON_DB
from typing import List


class EvolutionTree:

    def __init__(self, chain_item, evolves_from):
        self.name = chain_item['species']['name']
        self.evolves_from = evolves_from
        self.evolves_to = [EvolutionTree(sub_item, self) for sub_item in chain_item['evolves_to']]

    def __repr__(self) -> str:
        """This defines how the class is printed."""
        return f"Tree Item: {self.name}"


def find_in_tree(chain_item: EvolutionTree, pokemon: str):

    # Base case: return this item if it is our target Pokémon.
    if chain_item.name == pokemon:
        return chain_item

    # Else, recursively search through this Pokémon's evolutions.
    for branch in chain_item.evolves_to:
        next_item = find_in_tree(branch, pokemon)
        if next_item:
            return next_item

    # If it was not found in that section of the tree, return None.
    return None


class PickEvolution(discord.ui.View):

    def __init__(self, old_pokemon: str, is_shiny: bool, evolutions: List[EvolutionTree]):
        super().__init__()
        self.old_pokemon = old_pokemon
        self.is_shiny = is_shiny
        self.used = False
        self.evolutions = evolutions
        self.make_select()

    def make_select(self):
        """
        Constructs the dropdown menu and defines its behavior.
        """

        def make_option(name: str):
            """Makes a discord.SelectOption from a given Pokémon name."""

            return discord.SelectOption(label=name.title(), value=name)

        async def callback(interaction: discord.Interaction):
            """Defines what happens when a select option is chosen."""

            if not self.used:
                await evolve_pokemon(interaction, self.old_pokemon, select.values[0], self.is_shiny)
                self.used = True

            # For some reason setting select.disabled = True does not work, so I'm doing this instead.
            else:
                await interaction.response.defer()

        # This is the actual select menu that will appear.
        select = discord.ui.Select(
            placeholder="Choose evolution...",
            options=[make_option(evolution.name) for evolution in self.evolutions]
        )

        select.callback = callback

        self.add_item(select)


class NormalOrShiny(discord.ui.View):

    def __init__(self, pokemon_name):
        super().__init__()
        self.pokemon_name = pokemon_name

    @discord.ui.button(label='Normal', style=discord.ButtonStyle.grey)
    async def normal(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Choose to evolve the normal variant of the Pokémon.
        """

        await continue_evolve_dialog(interaction, self.pokemon_name, False)

    @discord.ui.button(label='Shiny', style=discord.ButtonStyle.grey)
    async def shiny(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Choose to evolve the shiny variant of the Pokémon.
        """

        await continue_evolve_dialog(interaction, self.pokemon_name, True)


def get_evolutions(pokemon: dict):
    """
    Gets the next evolution(s) of this Pokémon (returns None if it can't evolve).
    """

    evolution_chain = get_evolution_chain(pokemon['name'])

    evolution_tree = EvolutionTree(evolution_chain['chain'], None)

    target_pokemon = find_in_tree(evolution_tree, pokemon['name'])

    return target_pokemon.evolves_to if target_pokemon else None


async def evolve_pokemon(interaction: discord.Interaction, old, new, is_shiny):

    # Evolve Pokémon and consume Bluk Berry.
    POKEMON_DB.evolve(interaction.user, old, new, is_shiny)

    favorite = POKEMON_DB.get_favorite(interaction.user)

    # Update favorite Pokémon if necessary.
    if favorite['name'] == old and favorite['is_shiny'] == is_shiny:
        POKEMON_DB.set_favorite(interaction.user, new, is_shiny)

    await interaction.response.send_message(f"You evolved **{old.title()}** into **{new.title()}**!")


async def continue_evolve_dialog(interaction: discord.Interaction, pokemon_name, is_shiny):

    # Check that this Pokémon can evolve, and what it evolves into.
    evolutions = get_evolutions(get_pokemon(pokemon_name))

    if not evolutions:
        await interaction.response.send_message("This Pokémon cannot evolve further.", ephemeral=True)

    elif len(evolutions) == 1:
        await evolve_pokemon(interaction, pokemon_name, evolutions[0].name, is_shiny)

    # If this Pokémon has multiple possible evolutions, the user needs to select one.
    else:
        view = PickEvolution(pokemon_name, is_shiny, evolutions)
        message = "Choose the evolution: Careful! Once you select an option your choice is final!"
        await interaction.response.send_message(message, view=view, ephemeral=True)


class Evolution(commands.Cog):
    """
    Contains functionality to evolve Pokémon.
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

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Has a small chance to give the user a Bluk Berry.
        This berry can be consumed to evolve a Pokémon in the user's Pokédex.
        """

        # This first keeps the bot from triggering a drop before running the random function.
        if message.author.id != self.bot.user.id and random.random() < constants.BERRY_CHANCE:
            msg_content = (
                f"You just received a **Bluk Berry**! {constants.BLUK_BERRY} "
                "*You can consume this to evolve one of your Pokémon with /evolve <pokemon>.*"
            )

            POKEMON_DB.give_berry(message.author)

            await message.reply(msg_content)

    @discord.app_commands.command()
    async def evolve(self, interaction: discord.Interaction, pokemon_name: str):
        """
        Consumes a Bluk Berry to evolve one of your Pokémon.
        """

        pokemon_name = pokemon_name.strip().lower()

        # Ensure that the user has Bluk Berries.
        if not POKEMON_DB.has_berries(interaction.user):
            await interaction.response.send_message("You don't have enough Bluk Berries.", ephemeral=True)
            return

        pokemon = POKEMON_DB.get_pokemon_data(interaction.user, pokemon_name)

        # Ensure that the user has that Pokémon.
        if not pokemon['normal'] and not pokemon['shiny']:
            await interaction.response.send_message("You don't have that Pokémon.", ephemeral=True)

        # Determine which (normal or shiny) to evolve if necessary.
        elif pokemon['normal'] and pokemon['shiny']:
            view = NormalOrShiny(pokemon_name)
            message = f"Would you like to evolve the normal or shiny {pokemon_name.title()}?"
            await interaction.response.send_message(message, view=view, ephemeral=True)

        # We don't need to determine which to evolve if they don't have both.
        elif pokemon['normal'] or pokemon['shiny']:
            is_shiny = pokemon['shiny'] > 0
            await continue_evolve_dialog(interaction, pokemon_name, is_shiny)

    @discord.app_commands.command()
    async def test(self, interaction: discord.Interaction, pokemon_name: str):
        evolutions = get_evolutions(get_pokemon(pokemon_name))
        print(evolutions)
        view = PickEvolution(evolutions)
        await interaction.response.send_message(f"{evolutions}", view=view, ephemeral=True)


async def setup(bot):
    """
    Triggered when we load this class as an extension of the bot in main.py.
    """

    if bot.testing:
        await bot.add_cog(Evolution(bot), guilds=[discord.Object(id=864728010132947015)])
    else:
        await bot.add_cog(Evolution(bot))
