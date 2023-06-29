# Code by https://github.com/wdlord

import discord
from discord.ext import commands
from database import POKEMON_DB, TradeablePokemon
from dataclasses import dataclass
from typing import Optional, List
from pokeapi import pokemon_names


@dataclass
class PartyMember:
    name: str
    is_shiny: bool
    success: bool
    error_reason: Optional[str] = None


class SetPartyModal(discord.ui.Modal, title="Set Your Battle Party!"):
    """
    Manages the modal to set the user's battle party.
    """

    def __init__(self, user: discord.User, current_battle_party: list):
        super().__init__()
        self.user = user
        self.current_battle_party = current_battle_party

        self.party_fields = []

        label = "Use # before the name for shiny: ie #seel"

        # Sets all the fields in the modal.
        for i in range(5):

            # Uses current battle party member when possible.
            if len(self.current_battle_party) >= i + 1:

                party_member = self.current_battle_party[i]

                new_field = discord.ui.TextInput(
                    label=label,
                    default=f"{'*' if party_member['is_shiny'] else ''}{party_member['name']}",
                    required=False
                )

            # Otherwise shows a placeholder.
            else:
                new_field = discord.ui.TextInput(
                    label=label,
                    placeholder=f"Enter the name of a Pokemon here!",
                    required=False
                )

            self.party_fields.append(new_field)
            self.add_item(new_field)

    async def on_submit(self, interaction: discord.Interaction, successful=None):

        party_state = []
        passing = True

        # Examines all the fields to check for potential errors.
        for field in self.party_fields:

            name = field.value.strip().lower()

            is_shiny = name.startswith('#')

            name = name.lstrip('#')

            # Skips empty fields.
            if name == "":
                continue

            # Marks entries that are Pokémon that do not exist.
            if name.title() not in pokemon_names:
                party_member = PartyMember(name, is_shiny, False, "Pokemon does not exist.")
                party_state.append(party_member)
                passing = False

            # For Pokémon that do exist...
            else:
                pokemon_data = POKEMON_DB.get_pokemon_data(self.user, name)

                count = sum([1 for member in party_state if member.name == name and member.is_shiny == is_shiny])

                # Marks entries that exceed the number of this Pokémon owned.
                if count + 1 > pokemon_data['normal' if not is_shiny else 'shiny']:
                    party_member = PartyMember(name, is_shiny, False, "You don't have enough of this pokemon.")
                    party_state.append(party_member)
                    passing = False

                # Pokémon that are accepted.
                else:
                    party_member = PartyMember(name, is_shiny, True)
                    party_state.append(party_member)

        # Once all the fields have been checked for errors...

        if passing:
            await self.successful_run(interaction, party_state)

        else:
            await self.failed_run(interaction, party_state)

    async def successful_run(self, interaction: discord.Interaction, party_state):
        """
        Continues with setting the party.
        """

        await interaction.response.send_message("Lets gooooo!", ephemeral=True)

    async def failed_run(self, interaction: discord.Interaction, party_state: List[PartyMember]):
        """
        Explains to the user what went wrong.
        """

        message = "The following went wrong when trying to set your party:\n"

        for party_member in party_state:
            icon = '✅ ' if party_member.success else '❌ '
            reason = "Valid" if party_member.success else party_member.error_reason
            status = f"{icon} **{party_member.name.title()}**: {reason}\n"

            message += status

        await interaction.response.send_message(message, ephemeral=True)


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

        POKEMON_DB.trade(self.your_pokemon, self.their_pokemon)

        await interaction.response.send_message(f"Trade completed!")
        self.stop()

    @discord.ui.button(label='Decline', style=discord.ButtonStyle.grey)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Declines the trade request.
        """

        if interaction.user == self.their_pokemon.owner:
            await interaction.response.send_message(f"{self.their_pokemon.owner} has declined the request.")
            self.stop()


class BattleParty(commands.Cog):
    """
    Functionality for Pokémon battle party.
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
    async def setparty(self, interaction: discord.Interaction):
        """
        Set your battle party of 5 Pokémon.
        """

        current_battle_party = POKEMON_DB.get_battle_party(interaction.user)

        # This happens when the user is not in our database.
        if current_battle_party is None:
            await interaction.response.send_message("You do not have any Pokémon.", ephemeral=True)

        # This handles everything else.
        else:
            await interaction.response.send_modal(SetPartyModal(interaction.user, current_battle_party))

    @discord.app_commands.command()
    async def battleparty(self, interaction: discord.Interaction, user: discord.User = None):
        """
        View your Pokémon battle party.
        """
        pass


async def setup(bot):
    """
    Triggered when we load this class as an extension of the bot in main.py.
    """

    if bot.testing:
        await bot.add_cog(BattleParty(bot), guilds=[discord.Object(id=864728010132947015)])
    else:
        await bot.add_cog(BattleParty(bot))
