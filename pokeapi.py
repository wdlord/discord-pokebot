import requests
import random
import json
import unittest
from typing import Optional


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


type_to_color = {
    'normal': 0xA8A77A,
    'fire': 0xEE8130,
    'water': 0x6390F0,
    'grass': 0x7AC74C,
    'electric': 0xF7D02C,
    'ice': 0x96D9D6,
    'fighting': 0xC22E28,
    'poison': 0xA33EA1,
    'ground': 0xE2BF65,
    'flying': 0xA98FF3,
    'psychic': 0xF95587,
    'bug': 0xA6B91A,
    'rock': 0xB6A136,
    'ghost': 0x735797,
    'dark': 0x705746,
    'dragon': 0x6F35FC,
    'steel': 0xB7B7CE,
    'fairy': 0xD685AD,
}


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
        import json

        pokemon = get_pokemon('pikachu')
        print(json.dumps(pokemon, indent=4))

        self.assertEqual(pokemon['name'], 'pikachu')

    def test_specific(self):

        import json

        name = input('type name or press enter to skip...')

        if name:
            name = name.strip().lower()
            pokemon = get_pokemon(name)
            print(json.dumps(pokemon, indent=4))

            self.assertEqual(pokemon['name'], name)


if __name__ == "__main__":
    unittest.main()
