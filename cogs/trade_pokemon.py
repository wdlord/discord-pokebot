# Code by https://github.com/wdlord

import discord
from discord.ext import commands
from database import POKEMON_DB, TradeablePokemon


class SendRequestView(discord.ui.View):
    """
    This class manages the view to confirm sending a trade request.
    """

    def __init__(self, calling_user: discord.User, target_user: discord.User, your_pokemon: str, their_pokemon: str):
        super().__init__()
        self.calling_user = calling_user
        self.target_user = target_user
        self.your_pokemon = your_pokemon
        self.their_pokemon = their_pokemon
        self.make_dropdown(True)
        self.make_dropdown(False)

    def make_dropdown(self, toggle: bool):
        """
        Makes the dropdowns to select Pokémon that we are trading.
        """

        async def callback(interaction: discord.Interaction):
            """Allows us to ignore the callback function on the dropdowns."""
            await interaction.response.defer()

        # Changes the data depending on which user this dropdown represents.
        if toggle:
            user = self.calling_user
            pokemon = self.your_pokemon
        else:
            user = self.target_user
            pokemon = self.their_pokemon

        # Get the user's data for given Pokémon.
        pokemon_data = POKEMON_DB.get_pokemon_data(user, pokemon)

        # Makes the options list.
        options = []

        if pokemon_data['normal'] > 0:
            options.append(discord.SelectOption(label=pokemon.title(), value='normal'))

        if pokemon_data['shiny'] > 0:
            options.append(discord.SelectOption(label=f"✨shiny✨ {pokemon.title()}", value='shiny'))

        # Makes and adds the select.
        select = discord.ui.Select(
            placeholder=f"{'your' if toggle else 'their'} Pokémon",
            options=options
        )
        select.callback = callback
        self.add_item(select)

    @discord.ui.button(label='Send', style=discord.ButtonStyle.green)
    async def send(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Sends the trade request.
        """

        selects = [child for child in self.children if isinstance(child, discord.ui.Select)]

        # The user must have made a selection for both options.
        if len(selects[0].values) == 0 or len(selects[1].values) == 0:
            return

        # Make sure AGAIN that caller has specified Pokémon.
        caller_pokemon_data = POKEMON_DB.get_pokemon_data(self.calling_user, self.your_pokemon)
        if not caller_pokemon_data['normal'] and not caller_pokemon_data['shiny']:
            await interaction.response.send_message("You do not have any of that Pokémon.", ephemeral=True)
            self.stop()
            return

        # Make sure AGAIN that target has specified Pokémon.
        target_pokemon_data = POKEMON_DB.get_pokemon_data(self.target_user, self.their_pokemon)
        if not target_pokemon_data['normal'] and not target_pokemon_data['shiny']:
            await interaction.response.send_message(f"{self.target_user.name} does not have any of that Pokémon.", ephemeral=True)
            self.stop()
            return

        your_pokemon = TradeablePokemon(self.your_pokemon, selects[0].values[0] == 'shiny', self.calling_user)
        their_pokemon = TradeablePokemon(self.their_pokemon, selects[1].values[0] == 'shiny', self.target_user)

        # Ping target to confirm or deny request.
        message = (
            f"{their_pokemon.owner.mention} trade request from {your_pokemon.owner.name}:\n"
            f"{your_pokemon.owner.name}'s {'✨shiny✨ ' if your_pokemon.is_shiny else ''}**{your_pokemon.name.title()}** "
            f"for {their_pokemon.owner.name}'s {'✨shiny✨ ' if their_pokemon.is_shiny else ''}**{their_pokemon.name.title()}**."
        )
        view = ConfirmationView(your_pokemon, their_pokemon)
        await interaction.response.send_message(message, view=view)
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Cancels sending the trade request.
        """

        await interaction.response.send_message("Trade request has been canceled.", ephemeral=True)
        self.stop()


class ConfirmationView(discord.ui.View):
    """
    Lets the target user accept or decline the trade request.
    """

    def __init__(self, your_pokemon: TradeablePokemon, their_pokemon: TradeablePokemon):
        super().__init__()
        self.your_pokemon = your_pokemon
        self.their_pokemon = their_pokemon

    @discord.ui.button(label='Accept', style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Accepts the trade request.
        """

        if interaction.user != self.their_pokemon.owner:
            return

        self.stop()
        await interaction.response.defer()

        POKEMON_DB.trade(self.your_pokemon, self.their_pokemon)

        await interaction.followup.send(f"Trade completed!")

    @discord.ui.button(label='Decline', style=discord.ButtonStyle.grey)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Declines the trade request.
        """

        if interaction.user == self.their_pokemon.owner:
            await interaction.response.send_message(f"{self.their_pokemon.owner} has declined the request.")
            self.stop()


class Trade(commands.Cog):
    """
    Functionality for viewing captured Pokémon.
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
    async def trade(self, interaction: discord.Interaction, user: discord.User, your_pokemon: str, their_pokemon: str):
        """
        Trade one of your Pokémon for someone else's.
        """

        your_pokemon = your_pokemon.lower().strip()
        their_pokemon = their_pokemon.lower().strip()

        # User cannot trade with themselves.
        if interaction.user.id == user.id:
            await interaction.response.send_message("You cannot trade with yourself.", ephemeral=True)
            return

        # Make sure caller has specified Pokémon.
        caller_pokemon_data = POKEMON_DB.get_pokemon_data(interaction.user, your_pokemon)
        if not caller_pokemon_data['normal'] and not caller_pokemon_data['shiny']:
            await interaction.response.send_message("You do not have any of that Pokémon.", ephemeral=True)
            return

        # Make sure target has specified Pokémon.
        target_pokemon_data = POKEMON_DB.get_pokemon_data(user, their_pokemon)
        if not target_pokemon_data['normal'] and not target_pokemon_data['shiny']:
            await interaction.response.send_message(f"{user.name} does not have any of that Pokémon.", ephemeral=True)
            return

        message = "Select which pokemon to trade."
        view = SendRequestView(interaction.user, user, your_pokemon, their_pokemon)
        await interaction.response.send_message(message, view=view, ephemeral=True)


async def setup(bot):
    """
    Triggered when we load this class as an extension of the bot in main.py.
    """

    if bot.testing:
        await bot.add_cog(Trade(bot), guilds=[discord.Object(id=864728010132947015)])
    else:
        await bot.add_cog(Trade(bot))
