# Code by https://github.com/wdlord

"""This module defines project-level constants."""


def get_sprite(pokemon: dict, is_shiny: bool) -> str:
    # TODO: this is better suited for a utils class, but currently nothing else would go in there.
    """
    Tries to get the animated sprite for a Pokémon if available, otherwise gets the default static sprite.
    Extension is .gif if animated, .png if static.
    """

    sprite_type = 'front_shiny' if is_shiny else 'front_default'

    # The animated sprite can be None, so this statement will return the default sprite in that case.
    sprite_url = (
        pokemon['sprites']['versions']['generation-v']['black-white']['animated'][sprite_type]
        or
        pokemon['sprites'][sprite_type]
    )

    return sprite_url


ENCOUNTER_CHANCE = 0.005
SHINY_CHANCE = 0.01
BERRY_CHANCE = 0.01
MAX_ROLLS = 3

BLUK_BERRY = "<:blukberry:1111793629279834270>"

TYPE_TO_COLOR = {
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

TYPE_TO_ICON = {
    'normal': '<:NormalIcon:1110400039504855210>',
    'fire': '<:FireIcon:1110399898907586580>',
    'water': '<:WaterIcon:1110400249438146580>',
    'grass': '<:GrassIcon:1110399946194169947>',
    'electric': '<:ElectricIcon:1110399845233078273>',
    'ice': '<:IceIcon:1110400013693100103>',
    'fighting': '<:FightingIcon:1110399878334513192>',
    'poison': '<:PoisonIcon:1110400066184814612>',
    'ground': '<:GroundIcon:1110399965924163644>',
    'flying': '<:FlyingIcon:1110399913776402432>',
    'psychic': '<:PsychicIcon:1110400125118992404>',
    'bug': '<:BugIcon:1110389849606856704>',
    'rock': '<:RockIcon:1110400147420086373>',
    'ghost': '<:GhostIcon:1110399930306150433>',
    'dark': '<:DarkIcon:1110399801092231241>',
    'dragon': '<:DragonIcon:1110399818590855250>',
    'steel': '<:SteelIcon:1110400209499992165>',
    'fairy': '<:FairyIcon:1110399862421323806>'
}
