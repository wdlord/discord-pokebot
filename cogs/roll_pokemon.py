# Code by https://github.com/wdlord

import discord
from discord.ext import commands, tasks
from pokeapi import get_pokemon, type_to_color, type_to_icon
from database import POKEMON_DB
import random
import datetime


class PokemonRollCard(discord.ui.View):
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

    # Adjust the remaining rolls.
    POKEMON_DB.use_roll(interaction.user)
    remaining_rolls -= 1

    # If the user still has more cards to open, we recursively create another card.
    if remaining_rolls > 0:
        view = PokemonRollCard(remaining_rolls)
        await interaction.response.send_message(embed=embed, view=view)

    # Else we only have to send this card without a 'Next' button.
    else:
        await interaction.response.send_message(embed=embed)


def get_reset_time() -> str:
    """
    Calculates how long until the rolls reset.
    Returned as a simple string such as: "23 hours and 3 minutes."
    """

    now = datetime.datetime.now(datetime.timezone.utc)
    tomorrow = now + datetime.timedelta(days=1)
    reset_time = datetime.datetime.combine(tomorrow, datetime.time.min, datetime.timezone.utc) - now
    return f" {reset_time.seconds // 3600} hours and {(reset_time.seconds // 60) % 60} minutes"


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

    @tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=datetime.timezone.utc))
    async def reset_rolls(self):
        """
        This task resets the Pokémon rolls every day at midnight UTC.
        """

        POKEMON_DB.reset_all_rolls()

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
        remaining_rolls = POKEMON_DB.get_remaining_rolls(interaction.user)

        # rolls one Pokémon at a time, click the next button to continue.
        if remaining_rolls > 0:
            await roll_pokemon(interaction, remaining_rolls)

        else:
            message = f"You've used all your rolls. Rolls reset in **{get_reset_time()}**."
            await interaction.response.send_message(message, ephemeral=True)

    @discord.app_commands.command()
    async def reset(self, interaction: discord.Interaction):
        """
        Test command to reset all the rolls.
        """

        await self.reset_rolls()
        await interaction.response.send_message("Reset :)", ephemeral=True)


async def setup(bot):
    """
    Triggered when we load this class as an extension of the bot in main.py.
    """

    if bot.testing:
        await bot.add_cog(PokerollCommands(bot), guilds=[discord.Object(id=864728010132947015)])
    else:
        await bot.add_cog(PokerollCommands(bot))
