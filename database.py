import pymongo.typings

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import discord
from creds import MONGO_USER, MONGO_PASSWORD


class PokemonDatabase:

    def __init__(self):
        self.db = client['Pokeroll']['pokemon']

    def add_pokemon(self, user: discord.User, pokemon: str, shiny: bool):
        """
        Adds a Pokémon to a user's Pokédex.

        :param user: The discord user that is receiving a new Pokémon.
        :param pokemon: The name of the new Pokémon.
        :param shiny: Whether the Pokémon is a shiny variant.
        :return:
        """

        self.db.update_one(
            {'_id': user.id},
            {'$inc': {
                f'pokemon.{pokemon}.normal': int(not shiny),
                f'pokemon.{pokemon}.shiny': int(shiny),
            }},
            upsert=True
        )

    def get_pokemon_data(self, user: discord.User, pokemon: str) -> dict:
        """
        Gets the saved data for a user's particular Pokémon.

        :param user: The discord user that we are searching for a Pokémon.
        :param pokemon: The name of the Pokémon to search.
        :return:
        """

        user_obj = self.db.find_one({'_id': user.id})
        pokemon_list = user_obj['pokemon']
        return pokemon_list.get(f'{pokemon}', {'normal': 0, 'shiny': 0})

    def reset_all_rolls(self):
        """
        Resets the remaining rolls for all users.
        """

        self.db.update_many({}, {'$set': {'remaining_rolls': 3}})

    def reset_user_rolls(self, user: discord.User):
        """
        Resets the rolls for a particular user.
        Intended for use in testing_commands.py.
        """

        self.db.update_one({'_id': user.id}, {'$set': {'remaining_rolls': 3}})

    def use_roll(self, user: discord.User):
        """
        Subtracts a roll from a given user.
        """

        self.db.update_one({'_id': user.id}, {'$inc': {'remaining_rolls': -1}})

    def get_remaining_rolls(self, user: discord.User):
        """
        Gets the number of Pokémon rolls a user has left.
        """

        user_obj = self.db.find_one({'_id': user.id})

        try:
            remaining_rolls = user_obj['remaining_rolls']
            return remaining_rolls

        # Creates remaining_rolls field if necessary.
        except TypeError:
            self.db.update_one({'_id': user.id}, {'$set': {'remaining_rolls': 3}}, upsert=True)
            return 3


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
