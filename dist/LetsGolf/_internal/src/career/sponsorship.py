"""
sponsorship.py — sponsor deal groups, definitions, and progress helpers.

Sponsors appear in groups of 2–3.  The player picks exactly one from each
group; the others are permanently unavailable.  When the picked deal is
completed (target met) or dropped, that deal is also gone, and the next
group becomes available.

Contract economics
------------------
  signing_fee  : paid immediately on acceptance.  Smaller for harder/longer
                 deals (lower % of total value).
  season_bonus : paid when the performance target is met.
  Total value  : signing_fee + season_bonus.  Harder deals have a smaller
                 signing_fee fraction but a higher total value.

Target types: "played" | "top10" | "top5" | "top3" | "win"
"""

SPONSOR_GROUPS: list[dict] = [

    # ── Tour 1: Amateur Circuit (8 events / season) ──────────────────────────

    {
        "id": "g1a", "min_tour": 1,
        "sponsors": [
            {
                "id": "tee_time_beverages",
                "name": "Tee Time Beverages",
                "signing_fee": 250,
                "season_bonus": 750,
                "target": {"type": "played", "count": 4},
                "description": "Play at least 4 events this season.",
            },
            {
                "id": "par_pro_grips",
                "name": "Par Pro Grips",
                "signing_fee": 200,
                "season_bonus": 1100,
                "target": {"type": "top10", "count": 2},
                "description": "Finish top 10 in 2 events this season.",
            },
            {
                "id": "birdie_wear",
                "name": "Birdie Wear Co.",
                "signing_fee": 150,
                "season_bonus": 1600,
                "target": {"type": "top5", "count": 1},
                "description": "Finish top 5 in 1 event this season.",
            },
        ],
    },
    {
        "id": "g1b", "min_tour": 1,
        "sponsors": [
            {
                "id": "rough_cut_energy",
                "name": "Rough Cut Energy",
                "signing_fee": 300,
                "season_bonus": 900,
                "target": {"type": "played", "count": 5},
                "description": "Play at least 5 events this season.",
            },
            {
                "id": "eagle_eye_golf",
                "name": "Eagle Eye Golf",
                "signing_fee": 200,
                "season_bonus": 1300,
                "target": {"type": "top10", "count": 3},
                "description": "Finish top 10 in 3 events this season.",
            },
            {
                "id": "first_flight_shoes",
                "name": "First Flight Shoes",
                "signing_fee": 150,
                "season_bonus": 1850,
                "target": {"type": "top5", "count": 2},
                "description": "Finish top 5 in 2 events this season.",
            },
        ],
    },
    {
        "id": "g1c", "min_tour": 1,
        "sponsors": [
            {
                "id": "green_flag_media",
                "name": "Green Flag Media",
                "signing_fee": 250,
                "season_bonus": 750,
                "target": {"type": "played", "count": 4},
                "description": "Play at least 4 events this season.",
            },
            {
                "id": "caddie_choice_bags",
                "name": "Caddie's Choice Bags",
                "signing_fee": 200,
                "season_bonus": 1550,
                "target": {"type": "top10", "count": 4},
                "description": "Finish top 10 in 4 events this season.",
            },
            {
                "id": "local_links_champ",
                "name": "Local Links Champion",
                "signing_fee": 100,
                "season_bonus": 2900,
                "target": {"type": "win", "count": 1},
                "description": "Win 1 event this season.",
            },
        ],
    },
    {
        "id": "g1d", "min_tour": 1,
        "sponsors": [
            {
                "id": "swing_steady_aids",
                "name": "Swing Steady Training",
                "signing_fee": 200,
                "season_bonus": 600,
                "target": {"type": "played", "count": 3},
                "description": "Play at least 3 events this season.",
            },
            {
                "id": "ace_golf_apparel",
                "name": "Ace Golf Apparel",
                "signing_fee": 200,
                "season_bonus": 1300,
                "target": {"type": "top10", "count": 3},
                "description": "Finish top 10 in 3 events this season.",
            },
            {
                "id": "starter_sports_mag",
                "name": "Starter Sports Magazine",
                "signing_fee": 100,
                "season_bonus": 2150,
                "target": {"type": "top3", "count": 1},
                "description": "Finish top 3 in 1 event this season.",
            },
        ],
    },

    # ── Tour 2: Challenger Tour (10 events / season) ─────────────────────────

    {
        "id": "g2a", "min_tour": 2,
        "sponsors": [
            {
                "id": "rally_sport_nutrition",
                "name": "Rally Sport Nutrition",
                "signing_fee": 700,
                "season_bonus": 2300,
                "target": {"type": "played", "count": 6},
                "description": "Play at least 6 events this season.",
            },
            {
                "id": "champion_blades",
                "name": "Champion Blades Golf",
                "signing_fee": 550,
                "season_bonus": 3950,
                "target": {"type": "top10", "count": 3},
                "description": "Finish top 10 in 3 events this season.",
            },
            {
                "id": "summit_footwear",
                "name": "Summit Footwear",
                "signing_fee": 400,
                "season_bonus": 5600,
                "target": {"type": "top5", "count": 2},
                "description": "Finish top 5 in 2 events this season.",
            },
        ],
    },
    {
        "id": "g2b", "min_tour": 2,
        "sponsors": [
            {
                "id": "birdsong_apparel",
                "name": "Birdsong Apparel",
                "signing_fee": 800,
                "season_bonus": 2200,
                "target": {"type": "played", "count": 7},
                "description": "Play at least 7 events this season.",
            },
            {
                "id": "challenger_circuit_radio",
                "name": "Challenger Circuit Radio",
                "signing_fee": 550,
                "season_bonus": 4450,
                "target": {"type": "top10", "count": 4},
                "description": "Finish top 10 in 4 events this season.",
            },
            {
                "id": "pro_putt_balls",
                "name": "Pro-Putt Golf Balls",
                "signing_fee": 400,
                "season_bonus": 6600,
                "target": {"type": "top5", "count": 3},
                "description": "Finish top 5 in 3 events this season.",
            },
        ],
    },
    {
        "id": "g2c", "min_tour": 2,
        "sponsors": [
            {
                "id": "iron_edge_equipment",
                "name": "IronEdge Equipment",
                "signing_fee": 600,
                "season_bonus": 3400,
                "target": {"type": "top10", "count": 3},
                "description": "Finish top 10 in 3 events this season.",
            },
            {
                "id": "regional_golf_digest",
                "name": "Regional Golf Digest",
                "signing_fee": 500,
                "season_bonus": 5500,
                "target": {"type": "top5", "count": 2},
                "description": "Finish top 5 in 2 events this season.",
            },
            {
                "id": "rising_star_sports",
                "name": "Rising Star Sports",
                "signing_fee": 350,
                "season_bonus": 7650,
                "target": {"type": "top3", "count": 1},
                "description": "Finish top 3 in 1 event this season.",
            },
        ],
    },
    {
        "id": "g2d", "min_tour": 2,
        "sponsors": [
            {
                "id": "teestrong_gloves",
                "name": "TeeStrong Gloves",
                "signing_fee": 700,
                "season_bonus": 3300,
                "target": {"type": "top10", "count": 4},
                "description": "Finish top 10 in 4 events this season.",
            },
            {
                "id": "rough_rider_irons",
                "name": "Rough Rider Irons",
                "signing_fee": 450,
                "season_bonus": 5550,
                "target": {"type": "top5", "count": 2},
                "description": "Finish top 5 in 2 events this season.",
            },
            {
                "id": "challenger_cup_sports",
                "name": "Challenger Cup Sports",
                "signing_fee": 300,
                "season_bonus": 9700,
                "target": {"type": "win", "count": 1},
                "description": "Win 1 event this season.",
            },
        ],
    },

    # ── Tour 3: Development Tour (13 events / season) ────────────────────────

    {
        "id": "g3a", "min_tour": 3,
        "sponsors": [
            {
                "id": "national_golf_channel",
                "name": "National Golf Channel",
                "signing_fee": 2500,
                "season_bonus": 9500,
                "target": {"type": "played", "count": 9},
                "description": "Play at least 9 events this season.",
            },
            {
                "id": "voltaedge_equipment",
                "name": "VoltaEdge Equipment",
                "signing_fee": 2000,
                "season_bonus": 16000,
                "target": {"type": "top10", "count": 4},
                "description": "Finish top 10 in 4 events this season.",
            },
            {
                "id": "fastswing_clothing",
                "name": "FastSwing Clothing",
                "signing_fee": 1500,
                "season_bonus": 23500,
                "target": {"type": "top5", "count": 3},
                "description": "Finish top 5 in 3 events this season.",
            },
        ],
    },
    {
        "id": "g3b", "min_tour": 3,
        "sponsors": [
            {
                "id": "precision_max_balls",
                "name": "PrecisionMax Golf Balls",
                "signing_fee": 3000,
                "season_bonus": 10000,
                "target": {"type": "played", "count": 10},
                "description": "Play at least 10 events this season.",
            },
            {
                "id": "continental_footwear",
                "name": "Continental Footwear",
                "signing_fee": 2000,
                "season_bonus": 20000,
                "target": {"type": "top10", "count": 5},
                "description": "Finish top 10 in 5 events this season.",
            },
            {
                "id": "tigers_den_energy",
                "name": "Tiger's Den Energy",
                "signing_fee": 1200,
                "season_bonus": 28800,
                "target": {"type": "top5", "count": 4},
                "description": "Finish top 5 in 4 events this season.",
            },
        ],
    },
    {
        "id": "g3c", "min_tour": 3,
        "sponsors": [
            {
                "id": "drivefar_tech",
                "name": "DriveFar Technology",
                "signing_fee": 2000,
                "season_bonus": 18000,
                "target": {"type": "top10", "count": 5},
                "description": "Finish top 10 in 5 events this season.",
            },
            {
                "id": "birdie_cup_beverages",
                "name": "Birdie Cup Beverages",
                "signing_fee": 1500,
                "season_bonus": 25500,
                "target": {"type": "top5", "count": 3},
                "description": "Finish top 5 in 3 events this season.",
            },
            {
                "id": "allweather_apparel",
                "name": "AllWeather Apparel",
                "signing_fee": 1000,
                "season_bonus": 37000,
                "target": {"type": "top3", "count": 2},
                "description": "Finish top 3 in 2 events this season.",
            },
        ],
    },
    {
        "id": "g3d", "min_tour": 3,
        "sponsors": [
            {
                "id": "pinnacle_golf_equip",
                "name": "Pinnacle Golf Equipment",
                "signing_fee": 2500,
                "season_bonus": 22500,
                "target": {"type": "top10", "count": 6},
                "description": "Finish top 10 in 6 events this season.",
            },
            {
                "id": "proform_fitness",
                "name": "ProForm Fitness",
                "signing_fee": 1500,
                "season_bonus": 28500,
                "target": {"type": "top5", "count": 4},
                "description": "Finish top 5 in 4 events this season.",
            },
            {
                "id": "national_sports_weekly",
                "name": "National Sports Weekly",
                "signing_fee": 800,
                "season_bonus": 44200,
                "target": {"type": "win", "count": 1},
                "description": "Win 1 event this season.",
            },
        ],
    },

    # ── Tour 4: Continental Tour (15 events / season) ────────────────────────

    {
        "id": "g4a", "min_tour": 4,
        "sponsors": [
            {
                "id": "continental_motors",
                "name": "Continental Motors",
                "signing_fee": 8000,
                "season_bonus": 60000,
                "target": {"type": "top10", "count": 5},
                "description": "Finish top 10 in 5 events this season.",
            },
            {
                "id": "summit_finance",
                "name": "Summit Finance Group",
                "signing_fee": 6000,
                "season_bonus": 84000,
                "target": {"type": "top5", "count": 4},
                "description": "Finish top 5 in 4 events this season.",
            },
            {
                "id": "tour_edge_equipment",
                "name": "TourEdge Equipment",
                "signing_fee": 4000,
                "season_bonus": 116000,
                "target": {"type": "top3", "count": 2},
                "description": "Finish top 3 in 2 events this season.",
            },
        ],
    },
    {
        "id": "g4b", "min_tour": 4,
        "sponsors": [
            {
                "id": "chrono_golf_watches",
                "name": "ChronoGolf Watches",
                "signing_fee": 10000,
                "season_bonus": 65000,
                "target": {"type": "top10", "count": 6},
                "description": "Finish top 10 in 6 events this season.",
            },
            {
                "id": "acedrive_tech",
                "name": "AceDrive Golf Tech",
                "signing_fee": 7000,
                "season_bonus": 93000,
                "target": {"type": "top5", "count": 4},
                "description": "Finish top 5 in 4 events this season.",
            },
            {
                "id": "sportvibe_media",
                "name": "SportVibe Media Network",
                "signing_fee": 5000,
                "season_bonus": 130000,
                "target": {"type": "top3", "count": 3},
                "description": "Finish top 3 in 3 events this season.",
            },
        ],
    },
    {
        "id": "g4c", "min_tour": 4,
        "sponsors": [
            {
                "id": "pacific_rim_airlines",
                "name": "Pacific Rim Airlines",
                "signing_fee": 9000,
                "season_bonus": 71000,
                "target": {"type": "top10", "count": 7},
                "description": "Finish top 10 in 7 events this season.",
            },
            {
                "id": "goldstrike_beverages",
                "name": "GoldStrike Beverages",
                "signing_fee": 6000,
                "season_bonus": 99000,
                "target": {"type": "top5", "count": 5},
                "description": "Finish top 5 in 5 events this season.",
            },
            {
                "id": "prestige_athletic_wear",
                "name": "Prestige Athletic Wear",
                "signing_fee": 4000,
                "season_bonus": 141000,
                "target": {"type": "win", "count": 1},
                "description": "Win 1 event this season.",
            },
        ],
    },
    {
        "id": "g4d", "min_tour": 4,
        "sponsors": [
            {
                "id": "skyhigh_energy",
                "name": "SkyHigh Energy",
                "signing_fee": 8000,
                "season_bonus": 77000,
                "target": {"type": "top5", "count": 5},
                "description": "Finish top 5 in 5 events this season.",
            },
            {
                "id": "protech_shaft_corp",
                "name": "ProTech Shaft Corp",
                "signing_fee": 5000,
                "season_bonus": 120000,
                "target": {"type": "top3", "count": 3},
                "description": "Finish top 3 in 3 events this season.",
            },
            {
                "id": "continental_golf_assoc",
                "name": "Continental Golf Assoc.",
                "signing_fee": 3500,
                "season_bonus": 171500,
                "target": {"type": "win", "count": 2},
                "description": "Win 2 or more events this season.",
            },
        ],
    },

    # ── Tour 5: World Tour (17 events / season) ──────────────────────────────

    {
        "id": "g5a", "min_tour": 5,
        "sponsors": [
            {
                "id": "omega_drive_watches",
                "name": "Omega Drive Watches",
                "signing_fee": 20000,
                "season_bonus": 155000,
                "target": {"type": "top5", "count": 5},
                "description": "Finish top 5 in 5 events this season.",
            },
            {
                "id": "global_premier_bank",
                "name": "Global Premier Bank",
                "signing_fee": 15000,
                "season_bonus": 235000,
                "target": {"type": "top3", "count": 3},
                "description": "Finish top 3 in 3 events this season.",
            },
            {
                "id": "titan_auto",
                "name": "Titan Automobiles",
                "signing_fee": 10000,
                "season_bonus": 340000,
                "target": {"type": "win", "count": 1},
                "description": "Win 1 event this season.",
            },
        ],
    },
    {
        "id": "g5b", "min_tour": 5,
        "sponsors": [
            {
                "id": "worldclass_golf",
                "name": "WorldClass Golf Equipment",
                "signing_fee": 25000,
                "season_bonus": 175000,
                "target": {"type": "top5", "count": 6},
                "description": "Finish top 5 in 6 events this season.",
            },
            {
                "id": "skyward_airlines",
                "name": "Skyward Airlines",
                "signing_fee": 18000,
                "season_bonus": 262000,
                "target": {"type": "top3", "count": 4},
                "description": "Finish top 3 in 4 events this season.",
            },
            {
                "id": "summit_spirits",
                "name": "Summit Spirits",
                "signing_fee": 12000,
                "season_bonus": 388000,
                "target": {"type": "win", "count": 2},
                "description": "Win 2 or more events this season.",
            },
        ],
    },
    {
        "id": "g5c", "min_tour": 5,
        "sponsors": [
            {
                "id": "prestige_golf_wear",
                "name": "Prestige Golf Wear",
                "signing_fee": 22000,
                "season_bonus": 188000,
                "target": {"type": "top5", "count": 6},
                "description": "Finish top 5 in 6 events this season.",
            },
            {
                "id": "global_sports_network",
                "name": "Global Sports Network",
                "signing_fee": 15000,
                "season_bonus": 285000,
                "target": {"type": "top3", "count": 4},
                "description": "Finish top 3 in 4 events this season.",
            },
            {
                "id": "neopower_energy",
                "name": "NeoPower Energy Corp",
                "signing_fee": 10000,
                "season_bonus": 415000,
                "target": {"type": "win", "count": 2},
                "description": "Win 2 or more events this season.",
            },
        ],
    },
    {
        "id": "g5d", "min_tour": 5,
        "sponsors": [
            {
                "id": "stormblade_tech",
                "name": "StormBlade Technology",
                "signing_fee": 20000,
                "season_bonus": 205000,
                "target": {"type": "top3", "count": 5},
                "description": "Finish top 3 in 5 events this season.",
            },
            {
                "id": "intl_finance_group",
                "name": "International Finance Group",
                "signing_fee": 15000,
                "season_bonus": 310000,
                "target": {"type": "top3", "count": 3},
                "description": "Finish top 3 in 3 events this season.",
            },
            {
                "id": "apex_luxury_cars",
                "name": "Apex Luxury Cars",
                "signing_fee": 10000,
                "season_bonus": 465000,
                "target": {"type": "win", "count": 3},
                "description": "Win 3 or more events this season.",
            },
        ],
    },

    # ── Tour 6: Grand Tour (22 events / season) ──────────────────────────────

    {
        "id": "g6a", "min_tour": 6,
        "sponsors": [
            {
                "id": "valhalla_timepieces",
                "name": "Valhalla Timepieces",
                "signing_fee": 50000,
                "season_bonus": 400000,
                "target": {"type": "top5", "count": 7},
                "description": "Finish top 5 in 7 events this season.",
            },
            {
                "id": "sovereign_bank",
                "name": "Sovereign Private Bank",
                "signing_fee": 35000,
                "season_bonus": 615000,
                "target": {"type": "top3", "count": 4},
                "description": "Finish top 3 in 4 events this season.",
            },
            {
                "id": "phoenix_supercars",
                "name": "Phoenix Supercars",
                "signing_fee": 25000,
                "season_bonus": 875000,
                "target": {"type": "win", "count": 2},
                "description": "Win 2 or more events this season.",
            },
        ],
    },
    {
        "id": "g6b", "min_tour": 6,
        "sponsors": [
            {
                "id": "royal_crown_spirits",
                "name": "Royal Crown Spirits",
                "signing_fee": 60000,
                "season_bonus": 440000,
                "target": {"type": "top5", "count": 8},
                "description": "Finish top 5 in 8 events this season.",
            },
            {
                "id": "diamond_circuit_jewelry",
                "name": "Diamond Circuit Jewelry",
                "signing_fee": 40000,
                "season_bonus": 660000,
                "target": {"type": "top3", "count": 5},
                "description": "Finish top 3 in 5 events this season.",
            },
            {
                "id": "grand_prix_motorsport",
                "name": "Grand Prix Motorsport",
                "signing_fee": 30000,
                "season_bonus": 920000,
                "target": {"type": "win", "count": 3},
                "description": "Win 3 or more events this season.",
            },
        ],
    },
    {
        "id": "g6c", "min_tour": 6,
        "sponsors": [
            {
                "id": "globalair_aviation",
                "name": "GlobalAir Private Aviation",
                "signing_fee": 55000,
                "season_bonus": 495000,
                "target": {"type": "top5", "count": 8},
                "description": "Finish top 5 in 8 events this season.",
            },
            {
                "id": "apex_couture",
                "name": "Apex Couture Fashion",
                "signing_fee": 40000,
                "season_bonus": 710000,
                "target": {"type": "top3", "count": 5},
                "description": "Finish top 3 in 5 events this season.",
            },
            {
                "id": "pinnacle_investments",
                "name": "Pinnacle Investment Group",
                "signing_fee": 25000,
                "season_bonus": 1025000,
                "target": {"type": "win", "count": 3},
                "description": "Win 3 or more events this season.",
            },
        ],
    },
    {
        "id": "g6d", "min_tour": 6,
        "sponsors": [
            {
                "id": "legend_golf_signature",
                "name": "Legend Golf Signature",
                "signing_fee": 70000,
                "season_bonus": 530000,
                "target": {"type": "top5", "count": 9},
                "description": "Finish top 5 in 9 events this season.",
            },
            {
                "id": "world_media_empire",
                "name": "World Media Empire",
                "signing_fee": 45000,
                "season_bonus": 755000,
                "target": {"type": "top3", "count": 6},
                "description": "Finish top 3 in 6 events this season.",
            },
            {
                "id": "crown_jewel_hotels",
                "name": "Crown Jewel Hotels",
                "signing_fee": 30000,
                "season_bonus": 1170000,
                "target": {"type": "win", "count": 4},
                "description": "Win 4 or more events this season.",
            },
        ],
    },
]

# Flat list — used for ID lookups and backward-compat save serialisation.
SPONSORS: list[dict] = [s for g in SPONSOR_GROUPS for s in g["sponsors"]]
_SPONSOR_BY_ID: dict[str, dict] = {s["id"]: s for s in SPONSORS}


def get_offer_group(tour_level: int, dismissed_ids: list[str]) -> list[dict]:
    """Return the current group of sponsor offers.

    Finds the first group (lowest min_tour, then definition order) that
    is unlocked for this tour level and has at least one non-dismissed
    sponsor.  Returns an empty list when nothing is available.
    """
    for group in SPONSOR_GROUPS:
        if group["min_tour"] > tour_level:
            continue
        available = [s for s in group["sponsors"]
                     if s["id"] not in dismissed_ids]
        if available:
            return available
    return []


def get_group_sibling_ids(sponsor_id: str) -> list[str]:
    """Return all sponsor IDs that belong to the same group as sponsor_id."""
    for group in SPONSOR_GROUPS:
        ids = [s["id"] for s in group["sponsors"]]
        if sponsor_id in ids:
            return ids
    return [sponsor_id]


def get_available_sponsors(tour_level: int, reputation: int = 0) -> list[dict]:
    """Legacy shim kept for call sites not yet migrated to get_offer_group."""
    return get_offer_group(tour_level, [])


def is_target_met(contract: dict, progress: dict) -> bool:
    """Return True if the season target in contract has been achieved."""
    target = contract["target"]
    return progress.get(target["type"], 0) >= target["count"]


def progress_label(contract: dict, progress: dict) -> str:
    """Human-readable progress, e.g. '2 / 3 top-10 finishes'."""
    target = contract["target"]
    t_type = target["type"]
    count  = target["count"]
    done   = progress.get(t_type, 0)
    labels = {
        "top10":  "top-10 finish",
        "top5":   "top-5 finish",
        "top3":   "top-3 finish",
        "win":    "win",
        "played": "event played",
    }
    noun = labels.get(t_type, t_type)
    if count > 1:
        noun += "es" if noun.endswith("finish") else "s"
    return f"{done} / {count} {noun}"
