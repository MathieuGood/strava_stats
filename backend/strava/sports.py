SPORT_ALIASES = {
    "bike": "Ride",
    "biking": "Ride",
    "ride": "Ride",
    "inline": "InlineSkate",
    "inline_skate": "InlineSkate",
    "inline skating": "InlineSkate",
    "roller": "RollerSki",
    "rollerski": "RollerSki",
    "run": "Run",
    "running": "Run",
    "walk": "Walk",
    "walking": "Walk",
    "sup": "StandUpPaddling",
    "stand up paddling": "StandUpPaddling",
}


def resolve_sport(sport: str) -> str:
    return SPORT_ALIASES.get(sport.lower(), sport)
