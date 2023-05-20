# Code by https://github.com/wdlord

import discord
from discord.ext import commands
from pokeapi import get_pokemon, type_to_color


class PokerollCard(discord.ui.View):

    def __init__(self, remaining_rolls):
        super().__init__()
        self.remaining_rolls = remaining_rolls

    @discord.ui.button(label='Next', style=discord.ButtonStyle.green)
    async def card_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Defines the interaction when the Next button is clicked during pokeroll.
        """

        await new_card(interaction, self.remaining_rolls)
        self.stop()


async def new_card(interaction: discord.Interaction, remaining_rolls: int):
    """
    Generates new cards until the user is out of rolls.
    The interaction arg is either the interaction from the initial command, or from the Next buttons.
    """

    # Fetches a random Pokémon from the pokeapi.
    pokemon = get_pokemon()
    type_color = type_to_color[pokemon['types'][0]['type']['name']]

    desc = (
        f"Types: {', '.join(t['type']['name'] for t in pokemon['types'])}"
    )

    embed = discord.Embed(description=desc, color=type_color, title=f"{pokemon['name'].title()}")
    embed.set_image(url=pokemon['sprites']['front_default'])

    # If the user still has more cards to open, we have to recursively create another card.
    if remaining_rolls > 0:
        view = PokerollCard(remaining_rolls - 1)
        await interaction.response.send_message(embed=embed, view=view)

    # Else we only have to send this card.
    else:
        await interaction.response.send_message(embed=embed)


class PokerollCommands(commands.Cog):
    """
    Contains commands that are used to participate in the pokeroll.
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
        await new_card(interaction, 2)


async def setup(bot):
    """
    Triggered when we load this class as an extension of the bot in main.py.
    """

    if bot.testing:
        await bot.add_cog(PokerollCommands(bot), guilds=[discord.Object(id=864728010132947015)])
    else:
        await bot.add_cog(PokerollCommands(bot))
