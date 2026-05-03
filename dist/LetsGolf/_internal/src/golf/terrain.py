"""
Terrain system — defines all surface types on the course and how they
affect shot distance and accuracy.
"""

from enum import Enum


class Terrain(Enum):
    """Every terrain type that can appear on a golf course."""
    TEE        = 'X'
    FAIRWAY    = 'F'
    ROUGH      = 'R'
    DEEP_ROUGH = 'D'
    BUNKER     = 'B'
    WATER      = 'W'
    TREES      = 'T'
    GREEN      = 'G'


# Properties for each terrain type.
# dist_mod  : multiplied by club max distance (1.0 = no penalty)
# acc_mod   : multiplied by club accuracy (1.0 = no penalty)
# color     : placeholder RGB tile colour used until real art assets exist
# name      : human-readable label shown in the HUD
TERRAIN_PROPS = {
    Terrain.TEE: {
        'dist_mod': 1.0,
        'acc_mod':  1.0,
        'color':    (110, 200, 110),
        'name':     'Tee Box',
    },
    Terrain.FAIRWAY: {
        'dist_mod': 1.0,
        'acc_mod':  1.0,
        'color':    (75, 155, 75),
        'name':     'Fairway',
    },
    Terrain.ROUGH: {
        'dist_mod': 0.75,
        'acc_mod':  0.70,
        'color':    (45, 110, 45),
        'name':     'Rough',
    },
    Terrain.DEEP_ROUGH: {
        # Near-OOB penalty: 45% distance loss + doubled scatter. Intended as
        # a severe recovery situation, not a routine setback like plain rough.
        'dist_mod': 0.55,
        'acc_mod':  0.50,
        'color':    (28, 80, 28),
        'name':     'Deep Rough',
    },
    Terrain.BUNKER: {
        'dist_mod': 0.60,
        'acc_mod':  0.78,
        'color':    (210, 195, 140),
        'name':     'Bunker',
    },
    Terrain.WATER: {
        'dist_mod': 0.0,
        'acc_mod':  0.0,
        'color':    (55, 110, 200),
        'name':     'Water',
    },
    Terrain.TREES: {
        'dist_mod': 0.40,
        'acc_mod':  0.30,
        'color':    (20, 70, 20),
        'name':     'Trees',
    },
    Terrain.GREEN: {
        'dist_mod': 1.0,
        'acc_mod':  1.0,
        'color':    (120, 220, 120),
        'name':     'Green',
    },
}

# Quick lookup: single character → Terrain enum
CHAR_TO_TERRAIN = {t.value: t for t in Terrain}
