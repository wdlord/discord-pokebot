# Code by https://github.com/wdlord

import discord
from discord.ext import commands
import constants
from pokeapi import get_pokemon, get_evolution_chain
import random
from database import POKEMON_DB
from typing import List, Optional


class EvolutionTree:
    """
    Represents a species' evolution tree.
    Some Pokémon can evolve into multiple things, this structure handles that branching potential.
    An example of a species with branching evolutions is 'Ralts' -> 'Kirlia' -> ('Gardevoir' or 'Gallade').
    """

    def __init__(self, chain_link: dict):
        """
        Recursively constructs the evolution tree from a chain-link.
        https://pokeapi.co/docs/v2#evolution-section

        :param chain_link: A chain-link from the pokeapi 'evolution' endpoint.
        """

        self.name = chain_link['species']['name']
        self.evolves_to = [EvolutionTree(next_link) for next_link in chain_link['evolves_to']]

    def __repr__(self) -> str:
        """
        This defines how the class is printed.
        Here we only print the name of the Pokémon represented by this link.
        """

        return f"TREE: {self.name}"


def find_in_tree(chain_link: EvolutionTree, pokemon: str) -> Optional[EvolutionTree]:
    """
    Recursively finds the node representing the given Pokémon in a species evolution tree.

    :param chain_link: The root of the evolution tree.
    :param pokemon: The name of the Pokémon to find.
    :return: The node representing the target Pokémon, or None.
    """

    # Base case: return this item if it is our target Pokémon.
    if chain_link.name == pokemon:
        return chain_link

    # Else, recursively search through this Pokémon's evolutions.
    for branch in chain_link.evolves_to:
        next_link = find_in_tree(branch, pokemon)
        if next_link:
            return next_link

    # If it was not found in those branches, return None.
    return None


def get_evolutions(pokemon: dict) -> List[EvolutionTree]:
    """
    Gets the next evolution(s) of this Pokémon as a list (empty if it can't evolve).
    """

    evolution_chain = get_evolution_chain(pokemon['name'])

    evolution_tree = EvolutionTree(evolution_chain['chain'])

    target_pokemon = find_in_tree(evolution_tree, pokemon['name'])

    return target_pokemon.evolves_to


class EvolutionDropdown(discord.ui.View):
    """
    Dropdown view that allows users to select which Pokémon to evolve to if several are available.
    """

    def __init__(self, pokemon_name: str, is_shiny: bool, evolutions: List[EvolutionTree]):
        super().__init__()
        self.pokemon_name = pokemon_name
        self.is_shiny = is_shiny
        self.evolutions = evolutions
        self.used = False   # Having trouble disabling the select after an option is chosen, so using this instead.
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
                await evolve_pokemon(interaction, self.pokemon_name, select.values[0], self.is_shiny)
                self.used = True

            # For some reason setting select.disabled = True does not work, so I'm doing this instead.
            else:
                await interaction.response.defer()

        # This is the select menu that will appear.
        select = discord.ui.Select(
            placeholder="Choose evolution...",
            options=[make_option(evolution.name) for evolution in self.evolutions]
        )

        # This sets the callback behavior when an option is chosen to the 'callback' func we just defined.
        select.callback = callback

        self.add_item(select)


class NormalOrShiny(discord.ui.View):
    """
    If the user has both variants of a Pokémon, we request they choose which they want to evolve.
    """

    def __init__(self, pokemon_name: str):
        super().__init__()
        self.pokemon_name = pokemon_name

    @discord.ui.button(label='Normal', style=discord.ButtonStyle.grey)
    async def normal(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Choose to evolve the normal variant of the Pokémon.
        """

        await continue_evolve_dialog(interaction, self.pokemon_name, False)
        self.stop()

    @discord.ui.button(label='Shiny', style=discord.ButtonStyle.grey)
    async def shiny(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Choose to evolve the shiny variant of the Pokémon.
        """

        await continue_evolve_dialog(interaction, self.pokemon_name, True)
        self.stop()


async def evolve_pokemon(interaction: discord.Interaction, old: str, new: str, is_shiny: bool):
    """
    Evolves one Pokémon into another once all ambiguity has been dealt with.

    :param interaction: An active interaction we can use to send a response.
    :param old: The name of the Pokémon that we are evolving.
    :param new: The name of the new Pokémon after the evolution.
    :param is_shiny: Whether we are consuming & creating a normal or shiny Pokémon.
    """

    # Evolve Pokémon and consume Bluk Berry.
    POKEMON_DB.evolve(interaction.user, old, new, is_shiny)

    favorite = POKEMON_DB.get_favorite(interaction.user)

    # Update favorite Pokémon if necessary.
    if favorite['name'] == old and favorite['is_shiny'] == is_shiny:
        POKEMON_DB.set_favorite(interaction.user, new, is_shiny)

    await interaction.response.send_message(f"You evolved **{old.title()}** into **{new.title()}**!")


async def continue_evolve_dialog(interaction: discord.Interaction, pokemon_name, is_shiny):
    """
    Once we have determined if we are evolving a normal or shiny Pokémon,
    we may need to determine which Pokémon to evolve into (ex: Eevee can evolve into 9 different Pokémon).
    We encapsulate this behavior because so far in the dialog we may have consumed an interaction and created a new one.

    :param interaction: An active interaction we can use to send a response.
    :param pokemon_name: The name of the Pokémon we are evolving.
    :param is_shiny: Whether this Pokémon is shiny or not.
    """

    # Check that this Pokémon can evolve, and what it evolves into.
    evolutions = get_evolutions(get_pokemon(pokemon_name))

    if not evolutions:
        await interaction.response.send_message("This Pokémon cannot evolve further.", ephemeral=True)

    elif len(evolutions) == 1:
        await evolve_pokemon(interaction, pokemon_name, evolutions[0].name, is_shiny)

    # If this Pokémon has multiple possible evolutions, the user needs to select one.
    else:
        view = EvolutionDropdown(pokemon_name, is_shiny, evolutions)
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

        # Ignores messages from bots.
        if message.author.bot:
            return

        # Each message has a percentage chance to reward a Bluk Berry.
        if random.random() < constants.BERRY_CHANCE:

            msg_content = (
                f"You just received a **Bluk Berry**! {constants.BLUK_BERRY} "
                "*You can consume this to evolve one of your Pokémon with `/evolve <pokemon>`.*"
            )

            POKEMON_DB.give_berry(message.author)

            await message.reply(msg_content)

    @discord.app_commands.command()
    async def evolve(self, interaction: discord.Interaction, pokemon_name: str):
        """
        Consumes a Bluk Berry to evolve one of your Pokémon.
        """

        pokemon_name = pokemon_name.strip().lower()

        # The user needs at least one Bluk Berry.
        if not POKEMON_DB.num_berries(interaction.user):
            await interaction.response.send_message("You don't have enough Bluk Berries.", ephemeral=True)
            return

        pokemon = POKEMON_DB.get_pokemon_data(interaction.user, pokemon_name)

        if not pokemon['normal'] and not pokemon['shiny']:
            await interaction.response.send_message("You don't have that Pokémon.", ephemeral=True)

        elif pokemon['normal'] and pokemon['shiny']:
            prompt = f"Would you like to evolve the normal or shiny **{pokemon_name.title()}**?"
            await interaction.response.send_message(prompt, view=NormalOrShiny(pokemon_name), ephemeral=True)

        # If the user only has a normal OR shiny version, we don't need to ask them which to set.
        elif pokemon['normal'] or pokemon['shiny']:
            await continue_evolve_dialog(interaction, pokemon_name, pokemon['shiny'] > 0)


async def setup(bot):
    """
    Triggered when we load this class as an extension of the bot in main.py.
    """

    if bot.testing:
        await bot.add_cog(Evolution(bot), guilds=[discord.Object(id=864728010132947015)])
    else:
        await bot.add_cog(Evolution(bot))
