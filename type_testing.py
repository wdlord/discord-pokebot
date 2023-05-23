
types = "normal fire water grass electric ice fighting poison ground flying psychic bug rock ghost dark steel fairy"
types = types.split()

print(' '.join(f'\\:{t.title()}Icon:' for t in types))

icons = "<:NormalIcon:1110400039504855210> <:FireIcon:1110399898907586580> <:WaterIcon:1110400249438146580> <:GrassIcon:1110399946194169947> <:ElectricIcon:1110399845233078273> <:IceIcon:1110400013693100103> <:FightingIcon:1110399878334513192> <:PoisonIcon:1110400066184814612> <:GroundIcon:1110399965924163644> <:FlyingIcon:1110399913776402432> <:PsychicIcon:1110400125118992404> <:BugIcon:1110389849606856704> <:RockIcon:1110400147420086373> <:GhostIcon:1110399930306150433> <:DarkIcon:1110399801092231241> <:SteelIcon:1110400209499992165> <:FairyIcon:1110399862421323806>"

icon_dict = {types[i]: icon for i, icon in enumerate(icons.split())}

print(icon_dict)
