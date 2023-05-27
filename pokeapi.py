# Code by https://github.com/wdlord

import requests
import random
import json
import unittest
from typing import Optional, List
from dataclasses import dataclass


# This loads a list of Pokémon names to be used with the 'random' button.
with open('pokemon_names.json', 'r') as f:
    pokemon_names = json.load(f)


def get_pokemon(name: Optional[str] = None) -> Optional[dict]:
    """
    Get a Pokémon by name, or a random Pokémon if no argument is passed.

    :param name: Case-insensitive Pokémon name (or None).
    :return: Pokémon dict from https://pokeapi.co
    """

    # Randomly select a Pokémon if no name is supplied.
    if not name:
        name = pokemon_names[random.randrange(0, len(pokemon_names))]
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}/")

        # Get a new random Pokémon if the one we used could not be found.
        if response.status_code == 404:
            return get_pokemon()

        elif response.status_code != 200:
            print(f"pokeapi error: {response.status_code}")

        return response.json()

    # Attempt lookup if a name was supplied.
    else:
        name = name.lower().strip()
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}/")

        if response.status_code != 200:
            print(f"pokeapi error: {response.status_code}: {name}")
            return None

        return response.json()


def get_evolution_chain(pokemon_name: str) -> dict:
    """
    Gets the evolution chain object for a Pokémon ID.

    :param pokemon_name: The name of a  Pokémon.
    :return: The evolution chain object from https://pokeapi.co
    """

    # The species ID != the Pokémon ID, so we must first look up the species and get the chain URL from there.
    response1 = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_name}/")

    if response1.status_code != 200:
        print(f"pokeapi error (species): {response1.status_code}")

    # Now we can directly query this evolution chain URL to get the correct Pokémon chain.
    response2 = requests.get(response1.json()['evolution_chain']['url'])

    if response2.status_code != 200:
        print(f"pokeapi error (evolution_chain): {response2.status_code}")

    return response2.json()


class TestInputs(unittest.TestCase):
    """
    This class contains unit tests for the get_pokemon() function.
    """

    def test_mixed_case(self):
        self.assertEqual(get_pokemon('pIKACHU')['name'], 'pikachu')

    def test_whitespace(self):
        self.assertEqual(get_pokemon('\tpikachu ')['name'], 'pikachu')

    def test_invalid_name(self):
        self.assertEqual(get_pokemon('Kuriboh'), None)

    def test_random(self):
        self.assertNotEqual(get_pokemon(), None)

    def test_show_expected_output(self):

        pokemon = get_pokemon('pikachu')
        print(json.dumps(pokemon, indent=4))

        self.assertEqual(pokemon['name'], 'pikachu')

    def test_specific(self):

        name = input('type name or press enter to skip...')

        if name:
            name = name.strip().lower()
            pokemon = get_pokemon(name)
            print(json.dumps(pokemon, indent=4))

            self.assertEqual(pokemon['name'], name)

    def test_evolution_chain(self):

        chain = get_evolution_chain(5)
        print(json.dumps(chain, indent=4))

        self.assertNotEqual(chain, None)


if __name__ == "__main__":
    unittest.main()
