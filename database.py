import pymongo.typings

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import discord
from typing import Optional
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
                f'{pokemon}.normal': int(not shiny),
                f'{pokemon}.shiny': int(shiny),
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
        return user_obj.get(pokemon, {'normal': 0, 'shiny': 0})


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
