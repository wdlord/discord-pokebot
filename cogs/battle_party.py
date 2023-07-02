# Code by https://github.com/wdlord

import discord
from discord.ext import commands
from database import POKEMON_DB
from dataclasses import dataclass
from typing import Optional, List
from pokeapi import pokemon_names, get_pokemon
import constants


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
            if name not in pokemon_names:
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

        party = [{'name': party_member.name, 'is_shiny': party_member.is_shiny} for party_member in party_state]

        POKEMON_DB.set_battle_party(interaction.user, party)

        await interaction.response.send_message("Your battle party has been updated!", ephemeral=True)

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


class BattlePartyView(discord.ui.View):
    """
    Views the battle party for a given user.
    """

    def __init__(self, user: discord.User):
        super().__init__()
        self.user = user
        self.battle_party = POKEMON_DB.get_battle_party(user)
        self.member_index = 0
        self.message = None

    def empty_embed(self):
        """
        This embed only appears when a user does not have a battle party set.
        """

        desc = "Battle party is empty."
        embed = discord.Embed(description=desc, color=0x000000, title=f"{self.user.name}'s Pokédex")
        embed.set_footer(text="Party Member: 0 of 0")

        return embed

    def make_embed(self):
        """
        Creates the embed that represents a Pokémon in the battle party.
        """

        current_member = self.battle_party[self.member_index]

        pokemon = get_pokemon(current_member['name'])

        # Get the color corresponding to the first type of this Pokémon to use as the embed color.
        first_type_name = pokemon['types'][0]['type']['name']
        type_color = constants.TYPE_TO_COLOR[first_type_name]

        embed = discord.Embed(description='', color=type_color, title=f"{self.user.name}'s Battle Party")

        # Set the embed image to be shown.
        member_sprite = constants.get_sprite(pokemon, current_member['is_shiny'])
        embed.set_image(url=member_sprite)

        # Add the stats to the display.
        stats = (
            f"Pokédex #: *{pokemon['id']:03d}*\n"
            f"Height: *{pokemon['height']} decimetres*\n"
            f"Weight: *{pokemon['weight']} hectograms*\n"
        )
        embed.add_field(name=current_member['name'].title(), value=stats)

        # Show page status.
        embed.set_footer(text=f"Party Member: {self.member_index + 1} of {len(self.battle_party)}")

        return embed

    async def send(self, interaction: discord.Interaction):
        """
        Sends original message that shows the view. We do it within the class to save the message locally.

        :param interaction: The interaction of the command used.
        :return:
        """

        embed = self.make_embed() if self.battle_party else self.empty_embed()
        await interaction.response.send_message(embed=embed, view=self)
        self.message = await interaction.original_response()

    @discord.ui.button(label='◀', style=discord.ButtonStyle.grey)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Show the previous page when clicked.
        """

        # Special case for users that are not in the database.
        if not self.battle_party:
            button.disabled = True
            await interaction.response.defer()
            return

        # Loop around to the beginning if necessary.
        self.member_index = len(self.battle_party) - 1 if self.member_index == 0 else self.member_index - 1

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
        if not self.battle_party:
            button.disabled = True
            await interaction.response.defer()
            return

        # Loop around to the beginning if necessary.
        self.member_index = 0 if self.member_index + 1 == len(self.battle_party) else self.member_index + 1

        # Remake the embed with the next group of Pokémon, and update the message.
        await self.message.edit(embed=self.make_embed(), view=self)

        # We must acknowledge the interaction in some way.
        await interaction.response.defer()


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

        view = BattlePartyView(user or interaction.user)
        await view.send(interaction)


async def setup(bot):
    """
    Triggered when we load this class as an extension of the bot in main.py.
    """

    if bot.testing:
        await bot.add_cog(BattleParty(bot), guilds=[discord.Object(id=864728010132947015)])
    else:
        await bot.add_cog(BattleParty(bot))
