# Code by https://github.com/wdlord

import discord
from discord.ext import commands, tasks
from pokeapi import get_pokemon
from database import POKEMON_DB
import constants
import random
import datetime


class PokemonRollCard(discord.ui.View):
    """
    Represents a Pokémon from the /roll command.
    """

    def __init__(self, remaining_rolls, user):
        super().__init__()
        self.remaining_rolls = remaining_rolls
        self.user = user

    @discord.ui.button(label='Next', style=discord.ButtonStyle.green)
    async def card_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Defines the interaction when the Next button is clicked when rolling Pokémon.
        """

        if interaction.user != self.user:
            return

        await roll_pokemon(interaction, self.remaining_rolls, self.user)
        self.stop()


def make_embed(pokemon: dict, is_shiny: bool) -> discord.Embed:
    """
    Creates the embed for a Pokémon roll card.
    """

    # Get the color corresponding to the first type of this Pokémon to use as the embed color.
    first_type_name = pokemon['types'][0]['type']['name']
    type_color = constants.TYPE_TO_COLOR[first_type_name]

    # Here we add custom discord emotes corresponding to the Pokémon's types to the embed.
    # We also add an extra indicator only if the Pokémon is shiny.
    desc = f"{''.join(constants.TYPE_TO_ICON[t['type']['name']] for t in pokemon['types'])}"
    desc += "\n✨Shiny✨" if is_shiny else ""

    embed = discord.Embed(description=desc, color=type_color, title=f"{pokemon['name'].title()}")

    # Set the embed image to the Pokémon's sprite.
    sprite_url = constants.get_sprite(pokemon, is_shiny)
    embed.set_image(url=sprite_url)

    return embed


async def roll_pokemon(interaction: discord.Interaction, remaining_rolls: int, user: discord.User):
    """
    Recursively generates new cards until the user is out of rolls.

    :param interaction: Either the interaction from the command, or from the 'Next' button.
    :param remaining_rolls: How many more rolls the user has available.
    """

    # Create a new random Pokémon.
    pokemon = get_pokemon()
    is_shiny = random.random() < constants.SHINY_CHANCE

    # Add the Pokémon to the user's Pokédex.
    POKEMON_DB.add_pokemon(interaction.user, pokemon['name'], is_shiny=is_shiny)

    # Adjust the user's remaining rolls.
    POKEMON_DB.use_roll(interaction.user)
    remaining_rolls -= 1    # this avoids unnecessary database access.

    # If the user still has more cards to open, we recursively create another card WITH a 'Next' button.
    if remaining_rolls > 0:
        view = PokemonRollCard(remaining_rolls, user)
        await interaction.response.send_message(embed=make_embed(pokemon, is_shiny), view=view)

    # Else we can send the card without a 'Next' button.
    else:
        await interaction.response.send_message(embed=make_embed(pokemon, is_shiny))


def get_reset_time() -> str:
    """
    Calculates how long until the next rolls reset.
    Returned as a string such as "4 hours and 3 minutes".
    """

    now = datetime.datetime.now(datetime.timezone.utc)

    times = [datetime.datetime.combine(now, t) for t in constants.RESET_TIMES]
    differences = [t - now for t in times if (t - now).total_seconds() > 0]
    closest = min(differences)

    return f" {closest.seconds // 3600} hours and {(closest.seconds // 60) % 60} minutes"


class RollPokemon(commands.Cog):
    """
    Contains commands that are used to participate in the pokéroll.
    """

    def __init__(self, bot):
        self.bot = bot
        self.reset_rolls.start()

    async def load(self):
        """
        Called in on_ready() event.
        """

        await self.bot.wait_until_ready()

    @tasks.loop(time=constants.RESET_TIMES)
    async def reset_rolls(self):
        """
        This task resets the Pokémon rolls every day at midnight UTC.
        """

        print("Resetting all rolls...")
        POKEMON_DB.reset_all_rolls()
        print("Reset complete.")

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
        Rolls one Pokémon at a time, click the next button to continue.
        """

        remaining_rolls = POKEMON_DB.get_remaining_rolls(interaction.user)

        if remaining_rolls > 0:
            await roll_pokemon(interaction, remaining_rolls, interaction.user)

        else:
            message = f"You've used all your rolls. Rolls reset in **{get_reset_time()}**."
            await interaction.response.send_message(message, ephemeral=True)


async def setup(bot):
    """
    Triggered when we load this class as an extension of the bot in main.py.
    """

    if bot.testing:
        await bot.add_cog(RollPokemon(bot), guilds=[discord.Object(id=864728010132947015)])
    else:
        await bot.add_cog(RollPokemon(bot))
