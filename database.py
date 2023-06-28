# Code by https://github.com/wdlord

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import discord
from creds import MONGO_USER, MONGO_PASSWORD
import constants
from dataclasses import dataclass


@dataclass
class TradeablePokemon:
    name: str
    is_shiny: bool
    owner: discord.User


class PokemonDatabase:
    """
    Connection with the MongoDB collection.
    """

    def __init__(self):
        self.db = client['Pokeroll']['pokemon']

    def add_pokemon(self, user: discord.User, pokemon_name: str, is_shiny: bool):
        """
        Adds a Pokémon to a user's Pokédex.
        """

        self.db.update_one(
            {'_id': user.id},
            {'$inc': {
                f'pokemon.{pokemon_name}.normal': int(not is_shiny),
                f'pokemon.{pokemon_name}.shiny': int(is_shiny),
            }},
            upsert=True
        )

    def get_pokemon_data(self, user: discord.User, pokemon_name: str) -> dict:
        """
        Gets the saved data for a user's particular Pokémon.
        """

        user_obj = self.db.find_one({'_id': user.id})

        if not user_obj or not user_obj['pokemon'].get(pokemon_name, None):
            return {'normal': 0, 'shiny': 0}

        else:
            return user_obj['pokemon'][pokemon_name]

    def get_all_pokemon(self, user: discord.User) -> dict:
        """
        Gets a dict of a user's captured Pokémon.
        """

        user_obj = self.db.find_one({'_id': user.id})
        return user_obj['pokemon'] if user_obj else None

    def reset_all_rolls(self):
        """
        Resets the remaining rolls for all users.
        """

        self.db.update_many({}, {'$set': {'remaining_rolls': constants.MAX_ROLLS}})

    def reset_user_rolls(self, user: discord.User):
        """
        Resets the rolls for a particular user.
        Intended for use in testing_commands.py.
        """

        self.db.update_one({'_id': user.id}, {'$set': {'remaining_rolls': constants.MAX_ROLLS}})

    def use_roll(self, user: discord.User):
        """
        Subtracts a roll from a given user.
        """

        self.db.update_one({'_id': user.id}, {'$inc': {'remaining_rolls': -1}})

    def get_remaining_rolls(self, user: discord.User, upsert=True):
        """
        Gets the number of Pokémon rolls a user has left.
        """

        user_obj = self.db.find_one({'_id': user.id})

        try:
            remaining_rolls = user_obj['remaining_rolls']
            return remaining_rolls

        # Creates remaining_rolls field if necessary.
        except (TypeError, KeyError):
            self.db.update_one({'_id': user.id}, {'$set': {'remaining_rolls': constants.MAX_ROLLS}}, upsert=upsert)
            return constants.MAX_ROLLS

    def set_favorite(self, user: discord.User, pokemon_name: str, is_shiny: bool):
        """
        Sets the user's favorite Pokémon for their Pokédex.
        """

        self.db.update_one(
            {'_id': user.id},
            {'$set': {
                'favorite': {
                    'name': pokemon_name,
                    'is_shiny': is_shiny
                }
            }},
            upsert=True
        )

    def get_favorite(self, user: discord.User):
        """
        Gets the user's favorite Pokémon for their Pokédex.
        """
        user_obj = self.db.find_one({'_id': user.id})

        try:
            favorite = user_obj['favorite']
            return favorite

        # Creates user if necessary.
        except (TypeError, KeyError) as error:

            # This would mean that the user has not been added to the database yet.
            if type(error) is TypeError:
                return None

            # If the user has not set a favorite, we will set their favorite as their first Pokémon.
            if type(error) is KeyError:

                first_pokemon_name = None

                # Finds the first owned Pokémon.
                for name in list(user_obj['pokemon'].keys()):
                    if user_obj['pokemon'][name]['normal'] or user_obj['pokemon'][name]['shiny']:
                        first_pokemon_name = name
                        break

                if not first_pokemon_name:
                    print('User does not own any Pokemon.')
                    return

                favorite = {
                    'name': first_pokemon_name,
                    'is_shiny': (user_obj['pokemon'][first_pokemon_name]['normal'] == 0)
                }

                self.db.update_one({'_id': user.id}, {'$set': {'favorite': favorite}}, upsert=True)

                return favorite

    def give_berry(self, user: discord.User, amount: int = 1):
        """
        Gives a Bluk Berry (used for evolution) to the user.
        The only time we give multiple is when using testing commands.
        """

        self.db.update_one({'_id': user.id}, {'$inc': {'berries': amount}}, upsert=True)

    def num_berries(self, user: discord.User):
        """
        Gets the number of berries a user has (or None if user DNE).
        """

        user_obj = self.db.find_one({'_id': user.id})

        return user_obj.get('berries', 0) if user_obj else None

    def evolve(self, user: discord.User, old_pokemon: str, new_pokemon: str, is_shiny: bool):
        """
        Evolves one of the user's Pokémon and consumes a Bluk Berry.
        Consumes Bluk Berry, consumes old Pokémon, adds new Pokémon.
        """

        self.db.update_one(
            {'_id': user.id},
            {'$inc': {
                    f'pokemon.{old_pokemon}.normal': -int(not is_shiny),
                    f'pokemon.{old_pokemon}.shiny': -int(is_shiny),
                    f'pokemon.{new_pokemon}.normal': int(not is_shiny),
                    f'pokemon.{new_pokemon}.shiny': int(is_shiny),
                    'berries': -1
                }}
        )

    def trade(self, your_pokemon: TradeablePokemon, their_pokemon: TradeablePokemon):
        """
        Trades one Pokémon for another.
        """

        # Update first user's Pokémon.
        self.db.update_one(
            {'_id': your_pokemon.owner.id},
            {'$inc': {
                f'pokemon.{your_pokemon.name}.normal': -int(not your_pokemon.is_shiny),
                f'pokemon.{your_pokemon.name}.shiny': -int(your_pokemon.is_shiny),
                f'pokemon.{their_pokemon.name}.normal': +int(not their_pokemon.is_shiny),
                f'pokemon.{their_pokemon.name}.shiny': +int(their_pokemon.is_shiny),
            }}
        )

        # Update second user's Pokémon.
        self.db.update_one(
            {'_id': their_pokemon.owner.id},
            {'$inc': {
                f'pokemon.{your_pokemon.name}.normal': +int(not your_pokemon.is_shiny),
                f'pokemon.{your_pokemon.name}.shiny': +int(your_pokemon.is_shiny),
                f'pokemon.{their_pokemon.name}.normal': -int(not their_pokemon.is_shiny),
                f'pokemon.{their_pokemon.name}.shiny': -int(their_pokemon.is_shiny),
            }}
        )

        # Update first user's favorite if necessary.
        first_user = self.db.find_one({'_id': your_pokemon.owner.id})
        first_user_favorite = self.get_favorite(your_pokemon.owner)

        if first_user_favorite.get('name') == your_pokemon.name:
            if first_user['pokemon'][your_pokemon.name]['shiny' if your_pokemon.is_shiny else 'normal'] == 0:
                self.set_favorite(your_pokemon.owner, their_pokemon.name, their_pokemon.is_shiny)

        # Update second user's favorite if necessary.
        second_user = self.db.find_one({'_id': their_pokemon.owner.id})
        second_user_favorite = self.get_favorite(their_pokemon.owner)

        if second_user_favorite.get('name') == their_pokemon.name:
            if second_user['pokemon'][their_pokemon.name]['shiny' if their_pokemon.is_shiny else 'normal'] == 0:
                self.set_favorite(their_pokemon.owner, your_pokemon.name, your_pokemon.is_shiny)


uri = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@pokeroll.5g5ryxr.mongodb.net/?retryWrites=true&w=majority"

# Create a new client and connect to the server.
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection.
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")

except Exception as e:
    print(e)


# This instance will be used across any classes that need database access.
POKEMON_DB: PokemonDatabase = PokemonDatabase()
