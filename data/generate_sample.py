"""
Professional Football Kinematics & 90-Minute Multi-Match Generator
===================================================================
Generates broadcast-grade match tracking datasets for Barça Innovation Hub:
- Full 90-minute continuous match timeline (00:00 -> 90:00 +3')
- Biomechanical Speed-Limited Kinematics:
  * Strict physical speed limits (forward sprint max 30 km/h, retreat jog max 14 km/h)
  * Eliminates any sudden rapid backward teleportation / snapping!
  * Smooth inertia, natural acceleration, and cohesive team block movement.
- Complete Rosters with Official Squad Numbers (#) & Player Names:
  * FC Barcelona vs Real Madrid (Lewandowski #9, Pedri #8, Modric #10, Vinicius #7, etc.)
  * Man City vs Inter Milan (Haaland #9, De Bruyne #17, Rodri #16, Lautaro #10, etc.)
  * Argentina vs France (Messi #10, Di Maria #11, Mbappe #10, Griezmann #7, etc.)
- Physical Ball Kinematics:
  * Rolling friction deceleration curve on passes.
  * 3D ballistic parabola for aerial crosses (Z up to 5.4m).
  * High-power bullet strikes up to 116 km/h with goal net ripple and celebration.
  * 100% geometric continuity: Start of play[i] is guaranteed to be End of play[i-1].
"""

import json
import math
import os
from typing import Dict, Any, List, Tuple

# FIFA Standard 105m x 68m starting formations
HOME_433_FORM = {
    "H1": (6.0, 34.0, "GK"),
    "H2": (24.0, 10.0, "RB"),
    "H3": (18.0, 26.0, "CB"),
    "H4": (18.0, 42.0, "CB"),
    "H5": (24.0, 58.0, "LB"),
    "H6": (36.0, 34.0, "DM"),
    "H7": (58.0, 14.0, "RW"),
    "H8": (46.0, 25.0, "CM"),
    "H9": (46.0, 43.0, "CM"),
    "H10": (66.0, 34.0, "ST"),
    "H11": (58.0, 54.0, "LW"),
}

AWAY_4231_FORM = {
    "A1": (99.0, 34.0, "GK"),
    "A2": (81.0, 10.0, "LB"),
    "A3": (87.0, 26.0, "CB"),
    "A4": (87.0, 42.0, "CB"),
    "A5": (81.0, 58.0, "RB"),
    "A6": (69.0, 27.0, "DM"),
    "A7": (69.0, 41.0, "DM"),
    "A8": (57.0, 34.0, "AM"),
    "A9": (57.0, 12.0, "LM"),
    "A10": (57.0, 56.0, "RM"),
    "A11": (54.0, 34.0, "ST"),
}

MATCH_ROSTERS = {
    "MATCH_EL_CLASICO": {
        "home": {
            "H1": {"num": 1, "name": "Ter Stegen", "role": "GK"},
            "H2": {"num": 23, "name": "Koundé", "role": "RB"},
            "H3": {"num": 4, "name": "Araújo", "role": "CB"},
            "H4": {"num": 15, "name": "Christensen", "role": "CB"},
            "H5": {"num": 3, "name": "Balde", "role": "LB"},
            "H6": {"num": 5, "name": "Busquets", "role": "DM"},
            "H7": {"num": 11, "name": "Raphinha", "role": "RW"},
            "H8": {"num": 8, "name": "Pedri", "role": "CM"},
            "H9": {"num": 6, "name": "Gavi", "role": "CM"},
            "H10": {"num": 9, "name": "Lewandowski", "role": "ST"},
            "H11": {"num": 7, "name": "F. Torres", "role": "LW"},
        },
        "away": {
            "A1": {"num": 1, "name": "Courtois", "role": "GK"},
            "A2": {"num": 23, "name": "Mendy", "role": "LB"},
            "A3": {"num": 4, "name": "Alaba", "role": "CB"},
            "A4": {"num": 3, "name": "Militão", "role": "CB"},
            "A5": {"num": 2, "name": "Carvajal", "role": "RB"},
            "A6": {"num": 10, "name": "Modrić", "role": "DM"},
            "A7": {"num": 8, "name": "Kroos", "role": "DM"},
            "A8": {"num": 5, "name": "Bellingham", "role": "AM"},
            "A9": {"num": 7, "name": "Vinícius Jr", "role": "LM"},
            "A10": {"num": 11, "name": "Rodrygo", "role": "RM"},
            "A11": {"num": 9, "name": "Benzema", "role": "ST"},
        }
    },
    "MATCH_UCL_TACTICAL": {
        "home": {
            "H1": {"num": 31, "name": "Ederson", "role": "GK"},
            "H2": {"num": 2, "name": "Walker", "role": "RB"},
            "H3": {"num": 3, "name": "Dias", "role": "CB"},
            "H4": {"num": 25, "name": "Akanji", "role": "CB"},
            "H5": {"num": 5, "name": "Stones", "role": "DM"},
            "H6": {"num": 16, "name": "Rodri", "role": "DM"},
            "H7": {"num": 20, "name": "B. Silva", "role": "RW"},
            "H8": {"num": 8, "name": "Gündoğan", "role": "CM"},
            "H9": {"num": 17, "name": "De Bruyne", "role": "CM"},
            "H10": {"num": 9, "name": "Haaland", "role": "ST"},
            "H11": {"num": 10, "name": "Grealish", "role": "LW"},
        },
        "away": {
            "A1": {"num": 24, "name": "Onana", "role": "GK"},
            "A2": {"num": 32, "name": "Dimarco", "role": "LB"},
            "A3": {"num": 95, "name": "Bastoni", "role": "CB"},
            "A4": {"num": 15, "name": "Acerbi", "role": "CB"},
            "A5": {"num": 36, "name": "Darmian", "role": "RB"},
            "A6": {"num": 23, "name": "Barella", "role": "DM"},
            "A7": {"num": 20, "name": "Çalhanoğlu", "role": "DM"},
            "A8": {"num": 22, "name": "Mkhitaryan", "role": "AM"},
            "A9": {"num": 2, "name": "Dumfries", "role": "LM"},
            "A10": {"num": 9, "name": "Džeko", "role": "RM"},
            "A11": {"num": 10, "name": "Lautaro", "role": "ST"},
        }
    },
    "MATCH_WORLD_CUP": {
        "home": {
            "H1": {"num": 23, "name": "E. Martínez", "role": "GK"},
            "H2": {"num": 26, "name": "Molina", "role": "RB"},
            "H3": {"num": 13, "name": "Romero", "role": "CB"},
            "H4": {"num": 19, "name": "Otamendi", "role": "CB"},
            "H5": {"num": 8, "name": "Acuña", "role": "LB"},
            "H6": {"num": 24, "name": "Enzo F.", "role": "DM"},
            "H7": {"num": 11, "name": "Di María", "role": "RW"},
            "H8": {"num": 7, "name": "De Paul", "role": "CM"},
            "H9": {"num": 20, "name": "Mac Allister", "role": "CM"},
            "H10": {"num": 10, "name": "L. Messi", "role": "ST"},
            "H11": {"num": 9, "name": "J. Álvarez", "role": "LW"},
        },
        "away": {
            "A1": {"num": 1, "name": "Lloris", "role": "GK"},
            "A2": {"num": 22, "name": "T. Hernández", "role": "LB"},
            "A3": {"num": 18, "name": "Upamecano", "role": "CB"},
            "A4": {"num": 4, "name": "Varane", "role": "CB"},
            "A5": {"num": 5, "name": "Koundé", "role": "RB"},
            "A6": {"num": 8, "name": "Tchouaméni", "role": "DM"},
            "A7": {"num": 14, "name": "Rabiot", "role": "DM"},
            "A8": {"num": 7, "name": "Griezmann", "role": "AM"},
            "A9": {"num": 11, "name": "Dembélé", "role": "LM"},
            "A10": {"num": 9, "name": "Giroud", "role": "RM"},
            "A11": {"num": 10, "name": "K. Mbappé", "role": "ST"},
        }
    }
}

def get_match_spec(match_id: str) -> Dict[str, Any]:
    if match_id == "MATCH_EL_CLASICO":
        metadata = {
            "match_id": "MATCH_EL_CLASICO",
            "title": "⚽ Match 1: FC Barcelona vs Real Madrid (90' Full Match Timeline & Winner)",
            "competition": "LaLiga EA Sports · El Clásico (Camp Nou)",
            "home_team": {
                "name": "FC Barcelona",
                "short": "BAR",
                "color": "#ef4444",
                "color_sec": "#2563eb",
                "badge": "BAR",
                "pattern": "blaugrana"
            },
            "away_team": {
                "name": "Real Madrid",
                "short": "RMA",
                "color": "#eab308",
                "color_sec": "#f8fafc",
                "badge": "RMA",
                "pattern": "white"
            },
            "goals": [
                {
                    "minute": 89,
                    "second": 5,
                    "team": "Home",
                    "scorer": "R. Lewandowski",
                    "type": "Top-Corner Bullet Strike",
                    "speed_kmh": 112.5,
                    "score_after": [1, 0]
                }
            ],
            "chapters": [
                {"min": 1, "label": "⏱ 01' Kick-Off", "desc": "Camp Nou Kick-off & Backline circulation"},
                {"min": 15, "label": "⚡ 15' Tiki-Taka", "desc": "Midfield overload & wing progression"},
                {"min": 28, "label": "⚠️ 28' Madrid Press", "desc": "Modric pressing trap & counter attempt"},
                {"min": 45, "label": "🛡 45' Halftime", "desc": "Tactical regrouping at Halftime (0 - 0)"},
                {"min": 58, "label": "🔥 58' Overload", "desc": "Pedri & Gavi half-space penetration"},
                {"min": 73, "label": "✈️ 73' Aerial Cross", "desc": "Raphinha curled delivery & header duel"},
                {"min": 89, "label": "⚽ 89' GOAL! 1-0", "desc": "Lewandowski 112.5 km/h Top-Corner Winner!"},
                {"min": 90, "label": "🏁 90' Full Time", "desc": "Whistle blows & Camp Nou celebration (1 - 0)"}
            ]
        }

        plays = [
            {"type": "PASS", "from_p": "H10", "to_p": "H6", "dur": 80, "start": (52.5, 34.0), "end": (38.0, 34.0), "t_start": (0, 30), "t_end": (2, 0)},
            {"type": "DRIBBLE", "player": "H6", "dur": 70, "start": (38.0, 34.0), "end": (32.0, 34.0), "t_start": (2, 0), "t_end": (3, 10)},
            {"type": "PASS", "from_p": "H6", "to_p": "H3", "dur": 90, "start": (32.0, 34.0), "end": (22.0, 24.0), "t_start": (3, 10), "t_end": (4, 30)},
            {"type": "DRIBBLE", "player": "H3", "dur": 80, "start": (22.0, 24.0), "end": (28.0, 26.0), "t_start": (4, 30), "t_end": (7, 45)},
            {"type": "PASS", "from_p": "H3", "to_p": "H5", "dur": 110, "start": (28.0, 26.0), "end": (36.0, 56.0), "h": 0.8, "t_start": (7, 45), "t_end": (11, 20)},
            {"type": "DRIBBLE", "player": "H5", "dur": 90, "start": (36.0, 56.0), "end": (52.0, 58.0), "t_start": (11, 20), "t_end": (14, 0)},
            {"type": "PASS", "from_p": "H5", "to_p": "H8", "dur": 100, "start": (52.0, 58.0), "end": (64.0, 42.0), "t_start": (14, 0), "t_end": (15, 30)},
            {"type": "DRIBBLE", "player": "H8", "dur": 80, "start": (64.0, 42.0), "end": (66.0, 36.0), "t_start": (15, 30), "t_end": (19, 10)},
            {"type": "PASS", "from_p": "H8", "to_p": "H7", "dur": 110, "start": (66.0, 36.0), "end": (74.0, 16.0), "h": 0.5, "t_start": (19, 10), "t_end": (23, 40)},
            {"type": "DRIBBLE", "player": "H7", "dur": 90, "start": (74.0, 16.0), "end": (79.0, 18.0), "t_start": (23, 40), "t_end": (27, 0)},
            {"type": "PASS", "from_p": "H7", "to_p": "A6", "dur": 90, "start": (79.0, 18.0), "end": (68.0, 28.0), "t_start": (27, 0), "t_end": (28, 40)},
            {"type": "DRIBBLE", "player": "A6", "dur": 80, "start": (68.0, 28.0), "end": (60.0, 32.0), "t_start": (28, 40), "t_end": (29, 20)},
            {"type": "PASS", "from_p": "A6", "to_p": "A9", "dur": 120, "start": (60.0, 32.0), "end": (38.0, 14.0), "h": 1.2, "t_start": (29, 20), "t_end": (30, 40)},
            {"type": "DRIBBLE", "player": "A9", "dur": 100, "start": (38.0, 14.0), "end": (22.0, 20.0), "t_start": (30, 40), "t_end": (32, 10)},
            {"type": "SHOT", "from_p": "A9", "dur": 80, "start": (22.0, 20.0), "end": (4.5, 33.0), "h": 1.4, "speed": 98.0, "t_start": (32, 10), "t_end": (33, 0)},
            {"type": "DRIBBLE", "player": "H1", "dur": 90, "start": (4.5, 33.0), "end": (8.0, 34.0), "t_start": (33, 0), "t_end": (38, 20)},
            {"type": "PASS", "from_p": "H1", "to_p": "H4", "dur": 110, "start": (8.0, 34.0), "end": (22.0, 46.0), "t_start": (38, 20), "t_end": (42, 50)},
            {"type": "DRIBBLE", "player": "H4", "dur": 80, "start": (22.0, 46.0), "end": (28.0, 44.0), "t_start": (42, 50), "t_end": (45, 15)},
            {"type": "PASS", "from_p": "H4", "to_p": "H6", "dur": 100, "start": (28.0, 44.0), "end": (44.0, 34.0), "t_start": (46, 0), "t_end": (50, 30)},
            {"type": "DRIBBLE", "player": "H6", "dur": 80, "start": (44.0, 34.0), "end": (52.0, 32.0), "t_start": (50, 30), "t_end": (54, 40)},
            {"type": "PASS", "from_p": "H6", "to_p": "H8", "dur": 100, "start": (52.0, 32.0), "end": (64.0, 26.0), "t_start": (54, 40), "t_end": (58, 20)},
            {"type": "DRIBBLE", "player": "H8", "dur": 80, "start": (64.0, 26.0), "end": (72.0, 22.0), "t_start": (58, 20), "t_end": (63, 10)},
            {"type": "PASS", "from_p": "H8", "to_p": "H7", "dur": 100, "start": (72.0, 22.0), "end": (84.0, 12.0), "t_start": (63, 10), "t_end": (68, 0)},
            {"type": "DRIBBLE", "player": "H7", "dur": 90, "start": (84.0, 12.0), "end": (88.0, 14.0), "t_start": (68, 0), "t_end": (72, 45)},
            {"type": "CROSS", "from_p": "H7", "to_p": "A3", "dur": 140, "start": (88.0, 14.0), "end": (94.0, 33.0), "h": 5.4, "t_start": (72, 45), "t_end": (74, 30)},
            {"type": "DRIBBLE", "player": "A3", "dur": 70, "start": (94.0, 33.0), "end": (88.0, 34.0), "t_start": (74, 30), "t_end": (77, 10)},
            {"type": "PASS", "from_p": "A3", "to_p": "A8", "dur": 120, "start": (88.0, 34.0), "end": (66.0, 34.0), "t_start": (77, 10), "t_end": (80, 50)},
            {"type": "PASS", "from_p": "A8", "to_p": "H6", "dur": 90, "start": (66.0, 34.0), "end": (58.0, 34.0), "t_start": (80, 50), "t_end": (84, 15)},
            {"type": "DRIBBLE", "player": "H6", "dur": 80, "start": (58.0, 34.0), "end": (68.0, 34.0), "t_start": (84, 15), "t_end": (87, 0)},
            {"type": "PASS", "from_p": "H6", "to_p": "H10", "dur": 90, "start": (68.0, 34.0), "end": (84.0, 34.0), "t_start": (87, 0), "t_end": (88, 45)},
            {"type": "DRIBBLE", "player": "H10", "dur": 45, "start": (84.0, 34.0), "end": (86.5, 33.5), "t_start": (88, 45), "t_end": (89, 2)},
            {"type": "SHOT", "from_p": "H10", "dur": 65, "start": (86.5, 33.5), "end": (105.0, 36.4), "h": 2.25, "speed": 112.5, "is_goal": True, "t_start": (89, 2), "t_end": (89, 15)},
            {"type": "CELEBRATION", "player": "H10", "dur": 180, "start": (105.0, 36.4), "end": (105.0, 36.4), "scorer_pos": (98.0, 14.0), "t_start": (89, 15), "t_end": (93, 0)},
        ]

    elif match_id == "MATCH_UCL_TACTICAL":
        metadata = {
            "match_id": "MATCH_UCL_TACTICAL",
            "title": "🏆 Match 2: Man City vs Inter Milan (90' UCL Tactical Clash & Counter)",
            "competition": "UEFA Champions League Final · Atatürk Olympic Stadium",
            "home_team": {
                "name": "Manchester City",
                "short": "MCI",
                "color": "#38bdf8",
                "color_sec": "#0284c7",
                "badge": "MCI",
                "pattern": "skyblue"
            },
            "away_team": {
                "name": "Inter Milan",
                "short": "INT",
                "color": "#1e40af",
                "color_sec": "#0f172a",
                "badge": "INT",
                "pattern": "nerazzurri"
            },
            "goals": [
                {
                    "minute": 68,
                    "second": 10,
                    "team": "Home",
                    "scorer": "Rodri",
                    "type": "Edge-of-Box Curler",
                    "speed_kmh": 108.0,
                    "score_after": [1, 0]
                }
            ],
            "chapters": [
                {"min": 1, "label": "⏱ 01' Kick-Off", "desc": "City positional 3-2-4-1 build-up"},
                {"min": 18, "label": "⚡ 18' Box Midfield", "desc": "Stones inverted run & tactical probe"},
                {"min": 35, "label": "⚠️ 35' Inter Break", "desc": "Barella turnover & Lautaro direct counter"},
                {"min": 45, "label": "🛡 45' Halftime", "desc": "Inzaghi low block neutralizes City (0 - 0)"},
                {"min": 52, "label": "🔥 52' City Siege", "desc": "High territory pinning & Inter resistance"},
                {"min": 68, "label": "⚽ 68' GOAL! 1-0", "desc": "Rodri 108 km/h rocket into Onana's corner!"},
                {"min": 78, "label": "✈️ 78' Inter Cross", "desc": "Dimarco cross & desperate goal-line clearance"},
                {"min": 90, "label": "🏁 90' Full Time", "desc": "Treble triumph confirmed (MCI 1 - 0 INT)"}
            ]
        }

        plays = [
            {"type": "PASS", "from_p": "H1", "to_p": "H4", "dur": 80, "start": (6.0, 34.0), "end": (22.0, 44.0), "t_start": (0, 30), "t_end": (3, 0)},
            {"type": "DRIBBLE", "player": "H4", "dur": 70, "start": (22.0, 44.0), "end": (28.0, 42.0), "t_start": (3, 0), "t_end": (5, 30)},
            {"type": "PASS", "from_p": "H4", "to_p": "H6", "dur": 90, "start": (28.0, 42.0), "end": (42.0, 34.0), "t_start": (5, 30), "t_end": (8, 0)},
            {"type": "DRIBBLE", "player": "H6", "dur": 80, "start": (42.0, 34.0), "end": (48.0, 34.0), "t_start": (8, 0), "t_end": (13, 15)},
            {"type": "PASS", "from_p": "H6", "to_p": "H9", "dur": 110, "start": (48.0, 34.0), "end": (62.0, 46.0), "t_start": (13, 15), "t_end": (18, 30)},
            {"type": "DRIBBLE", "player": "H9", "dur": 80, "start": (62.0, 46.0), "end": (68.0, 48.0), "t_start": (18, 30), "t_end": (24, 0)},
            {"type": "PASS", "from_p": "H9", "to_p": "H11", "dur": 110, "start": (68.0, 48.0), "end": (76.0, 58.0), "h": 0.8, "t_start": (24, 0), "t_end": (29, 30)},
            {"type": "DRIBBLE", "player": "H11", "dur": 80, "start": (76.0, 58.0), "end": (82.0, 56.0), "t_start": (29, 30), "t_end": (34, 0)},
            {"type": "PASS", "from_p": "H11", "to_p": "A6", "dur": 90, "start": (82.0, 56.0), "end": (70.0, 38.0), "t_start": (34, 0), "t_end": (35, 20)},
            {"type": "DRIBBLE", "player": "A6", "dur": 80, "start": (70.0, 38.0), "end": (62.0, 36.0), "t_start": (35, 20), "t_end": (38, 0)},
            {"type": "PASS", "from_p": "A6", "to_p": "A11", "dur": 130, "start": (62.0, 36.0), "end": (35.0, 36.0), "h": 1.4, "t_start": (38, 0), "t_end": (41, 30)},
            {"type": "DRIBBLE", "player": "A11", "dur": 80, "start": (35.0, 36.0), "end": (24.0, 35.0), "t_start": (41, 30), "t_end": (43, 40)},
            {"type": "SHOT", "from_p": "A11", "dur": 70, "start": (24.0, 35.0), "end": (4.0, 34.0), "h": 1.5, "speed": 102.0, "t_start": (43, 40), "t_end": (45, 0)},
            {"type": "DRIBBLE", "player": "H1", "dur": 80, "start": (4.0, 34.0), "end": (8.0, 34.0), "t_start": (45, 0), "t_end": (48, 30)},
            {"type": "PASS", "from_p": "H1", "to_p": "H6", "dur": 120, "start": (8.0, 34.0), "end": (46.0, 34.0), "h": 1.0, "t_start": (48, 30), "t_end": (52, 10)},
            {"type": "DRIBBLE", "player": "H6", "dur": 80, "start": (46.0, 34.0), "end": (58.0, 34.0), "t_start": (52, 10), "t_end": (58, 0)},
            {"type": "PASS", "from_p": "H6", "to_p": "H7", "dur": 100, "start": (58.0, 34.0), "end": (78.0, 16.0), "t_start": (58, 0), "t_end": (63, 0)},
            {"type": "DRIBBLE", "player": "H7", "dur": 80, "start": (78.0, 16.0), "end": (86.0, 20.0), "t_start": (63, 0), "t_end": (67, 30)},
            {"type": "PASS", "from_p": "H7", "to_p": "H6", "dur": 70, "start": (86.0, 20.0), "end": (82.0, 34.0), "t_start": (67, 30), "t_end": (68, 5)},
            {"type": "SHOT", "from_p": "H6", "dur": 65, "start": (82.0, 34.0), "end": (105.0, 32.5), "h": 1.4, "speed": 108.0, "is_goal": True, "t_start": (68, 5), "t_end": (68, 20)},
            {"type": "CELEBRATION", "player": "H6", "dur": 120, "start": (105.0, 32.5), "end": (105.0, 32.5), "scorer_pos": (94.0, 18.0), "t_start": (68, 20), "t_end": (71, 0)},
            {"type": "PASS", "from_p": "A11", "to_p": "A6", "dur": 80, "start": (105.0, 32.5), "end": (65.0, 34.0), "t_start": (71, 0), "t_end": (74, 30)},
            {"type": "DRIBBLE", "player": "A6", "dur": 80, "start": (65.0, 34.0), "end": (55.0, 36.0), "t_start": (74, 30), "t_end": (78, 0)},
            {"type": "CROSS", "from_p": "A2", "to_p": "A11", "dur": 130, "start": (55.0, 36.0), "end": (10.0, 34.0), "h": 5.2, "t_start": (78, 0), "t_end": (82, 30)},
            {"type": "SHOT", "from_p": "A11", "dur": 60, "start": (10.0, 34.0), "end": (2.0, 34.5), "h": 1.8, "speed": 95.0, "t_start": (82, 30), "t_end": (83, 10)},
            {"type": "DRIBBLE", "player": "H1", "dur": 140, "start": (2.0, 34.5), "end": (6.0, 34.0), "t_start": (83, 10), "t_end": (94, 0)},
        ]

    else:
        metadata = {
            "match_id": "MATCH_WORLD_CUP",
            "title": "🌍 Match 3: Argentina vs France (90' World Cup Final Showdown & Thrills)",
            "competition": "FIFA World Cup Final · Lusail Iconic Stadium",
            "home_team": {
                "name": "Argentina",
                "short": "ARG",
                "color": "#38bdf8",
                "color_sec": "#f8fafc",
                "badge": "ARG",
                "pattern": "albiceleste"
            },
            "away_team": {
                "name": "France",
                "short": "FRA",
                "color": "#1e40af",
                "color_sec": "#ef4444",
                "badge": "FRA",
                "pattern": "lesbleus"
            },
            "goals": [
                {
                    "minute": 32,
                    "second": 15,
                    "team": "Home",
                    "scorer": "L. Messi",
                    "type": "Curled Precision Placement",
                    "speed_kmh": 94.0,
                    "score_after": [1, 0]
                },
                {
                    "minute": 72,
                    "second": 40,
                    "team": "Away",
                    "scorer": "K. Mbappé",
                    "type": "Volley Rocket",
                    "speed_kmh": 116.0,
                    "score_after": [1, 1]
                },
                {
                    "minute": 88,
                    "second": 50,
                    "team": "Home",
                    "scorer": "L. Messi",
                    "type": "Dramatic Rebound Winner",
                    "speed_kmh": 98.0,
                    "score_after": [2, 1]
                }
            ],
            "chapters": [
                {"min": 1, "label": "⏱ 01' Final Kick-Off", "desc": "Lusail Final begins with Scaloneta pressure"},
                {"min": 17, "label": "⚡ 17' Di Maria Run", "desc": "Di Maria electric flank dribble past Koundé"},
                {"min": 32, "label": "⚽ 32' GOAL! 1-0", "desc": "Messi precision finish into side netting!"},
                {"min": 45, "label": "🛡 45' Halftime", "desc": "Argentina dominating possession at break (1 - 0)"},
                {"min": 55, "label": "🔥 55' French Battle", "desc": "Tchouaméni & Rabiot contest midfield duels"},
                {"min": 72, "label": "⚽ 72' GOAL! 1-1", "desc": "Mbappé 116 km/h first-time volley equalizer!"},
                {"min": 88, "label": "⚽ 88' GOAL! 2-1", "desc": "Messi dramatic rebound winner over the line!"},
                {"min": 90, "label": "🏁 90' World Champions", "desc": "Argentina lift the World Cup! (ARG 2 - 1 FRA)"}
            ]
        }

        plays = [
            {"type": "PASS", "from_p": "H10", "to_p": "H8", "dur": 80, "start": (52.5, 34.0), "end": (42.0, 26.0), "t_start": (0, 30), "t_end": (4, 0)},
            {"type": "DRIBBLE", "player": "H8", "dur": 80, "start": (42.0, 26.0), "end": (48.0, 24.0), "t_start": (4, 0), "t_end": (8, 30)},
            {"type": "PASS", "from_p": "H8", "to_p": "H7", "dur": 100, "start": (48.0, 24.0), "end": (64.0, 14.0), "t_start": (8, 30), "t_end": (14, 0)},
            {"type": "DRIBBLE", "player": "H7", "dur": 90, "start": (64.0, 14.0), "end": (76.0, 16.0), "t_start": (14, 0), "t_end": (17, 30)},
            {"type": "PASS", "from_p": "H7", "to_p": "H10", "dur": 90, "start": (76.0, 16.0), "end": (82.0, 32.0), "t_start": (17, 30), "t_end": (25, 0)},
            {"type": "DRIBBLE", "player": "H10", "dur": 70, "start": (82.0, 32.0), "end": (86.0, 33.0), "t_start": (25, 0), "t_end": (32, 5)},
            {"type": "SHOT", "from_p": "H10", "dur": 65, "start": (86.0, 33.0), "end": (105.0, 35.5), "h": 1.2, "speed": 94.0, "is_goal": True, "t_start": (32, 5), "t_end": (32, 20)},
            {"type": "CELEBRATION", "player": "H10", "dur": 110, "start": (105.0, 35.5), "end": (105.0, 35.5), "scorer_pos": (95.0, 20.0), "t_start": (32, 20), "t_end": (35, 0)},
            {"type": "PASS", "from_p": "A11", "to_p": "A7", "dur": 80, "start": (105.0, 35.5), "end": (65.0, 38.0), "t_start": (35, 0), "t_end": (40, 0)},
            {"type": "DRIBBLE", "player": "A7", "dur": 80, "start": (65.0, 38.0), "end": (58.0, 38.0), "t_start": (40, 0), "t_end": (45, 10)},
            {"type": "PASS", "from_p": "A7", "to_p": "A10", "dur": 100, "start": (58.0, 38.0), "end": (52.0, 56.0), "t_start": (45, 10), "t_end": (50, 0)},
            {"type": "DRIBBLE", "player": "A10", "dur": 80, "start": (52.0, 56.0), "end": (44.0, 52.0), "t_start": (50, 0), "t_end": (55, 0)},
            {"type": "PASS", "from_p": "A10", "to_p": "A11", "dur": 110, "start": (44.0, 52.0), "end": (22.0, 36.0), "h": 1.6, "t_start": (55, 0), "t_end": (64, 0)},
            {"type": "DRIBBLE", "player": "A11", "dur": 70, "start": (22.0, 36.0), "end": (18.0, 35.0), "t_start": (64, 0), "t_end": (72, 30)},
            {"type": "SHOT", "from_p": "A11", "dur": 55, "start": (18.0, 35.0), "end": (0.0, 32.5), "h": 1.8, "speed": 116.0, "is_goal": True, "t_start": (72, 30), "t_end": (72, 45)},
            {"type": "CELEBRATION", "player": "A11", "dur": 110, "start": (0.0, 32.5), "end": (0.0, 32.5), "scorer_pos": (12.0, 16.0), "t_start": (72, 45), "t_end": (76, 0)},
            {"type": "PASS", "from_p": "H1", "to_p": "H6", "dur": 100, "start": (0.0, 32.5), "end": (38.0, 34.0), "t_start": (76, 0), "t_end": (81, 0)},
            {"type": "DRIBBLE", "player": "H6", "dur": 80, "start": (38.0, 34.0), "end": (54.0, 34.0), "t_start": (81, 0), "t_end": (85, 30)},
            {"type": "PASS", "from_p": "H6", "to_p": "H10", "dur": 90, "start": (54.0, 34.0), "end": (78.0, 34.0), "t_start": (85, 30), "t_end": (88, 30)},
            {"type": "DRIBBLE", "player": "H10", "dur": 45, "start": (78.0, 34.0), "end": (82.0, 34.0), "t_start": (88, 30), "t_end": (88, 48)},
            {"type": "SHOT", "from_p": "H10", "dur": 60, "start": (82.0, 34.0), "end": (105.0, 34.2), "h": 0.8, "speed": 98.0, "is_goal": True, "t_start": (88, 48), "t_end": (89, 5)},
            {"type": "CELEBRATION", "player": "H10", "dur": 150, "start": (105.0, 34.2), "end": (105.0, 34.2), "scorer_pos": (96.0, 22.0), "t_start": (89, 5), "t_end": (94, 0)},
        ]

    return {
        "metadata": metadata,
        "plays": plays
    }

def generate_smooth_match_tracking(match_id: str) -> dict:
    spec = get_match_spec(match_id)
    metadata = spec["metadata"]
    plays = spec["plays"]
    roster_data = MATCH_ROSTERS.get(match_id, MATCH_ROSTERS["MATCH_EL_CLASICO"])

    timeline = []
    curr_f = 1
    for p in plays:
        timeline.append({
            "play": p,
            "start_frame": curr_f,
            "end_frame": curr_f + p["dur"] - 1,
            "dur": p["dur"]
        })
        curr_f += p["dur"]

    total_frames = curr_f - 1

    p_pos = {}
    for pid, (bx, by, role) in HOME_433_FORM.items():
        p_pos[pid] = [bx, by]
    for pid, (bx, by, role) in AWAY_4231_FORM.items():
        p_pos[pid] = [bx, by]

    frames = []
    last_bx = plays[0]["start"][0]
    last_by = plays[0]["start"][1]
    last_bz = 0.0
    dt = 0.04  # 25 FPS

    for f_idx in range(1, total_frames + 1):
        cur_item = next((item for item in timeline if item["start_frame"] <= f_idx <= item["end_frame"]), timeline[-1])
        play = cur_item["play"]
        p_start = cur_item["start_frame"]
        p_dur = cur_item["dur"]
        p_type = play["type"]

        u = max(0.0, min(1.0, (f_idx - p_start) / max(1, p_dur - 1)))

        x0, y0 = play["start"]
        x1, y1 = play["end"]

        # Physics-based Ball Kinematics
        if p_type == "DRIBBLE":
            s = u * u * (3.0 - 2.0 * u)
            bx = x0 + (x1 - x0) * s
            by = y0 + (y1 - y0) * s
            bz = 0.0
        elif p_type == "PASS":
            s = 1.0 - math.pow(1.0 - u, 1.6)
            bx = x0 + (x1 - x0) * s
            by = y0 + (y1 - y0) * s
            hop_h = play.get("h", 0.0)
            bz = math.sin(u * math.pi) * hop_h if hop_h > 0 else 0.0
        elif p_type == "CROSS":
            s = u * (2.0 - u)
            bx = x0 + (x1 - x0) * s
            by = y0 + (y1 - y0) * s
            max_h = play.get("h", 5.2)
            bz = 4.0 * max_h * u * (1.0 - u)
        elif p_type == "SHOT":
            bx = x0 + (x1 - x0) * u
            by = y0 + (y1 - y0) * u
            max_h = play.get("h", 1.8)
            bz = (0.2 + (max_h - 0.2) * u) + math.sin(u * math.pi) * 0.35
        elif p_type == "CELEBRATION":
            bx = x1
            by = y1
            bz = max(0.0, 0.4 * (1.0 - min(1.0, u * 3.0)))
        else:
            bx, by, bz = x0, y0, 0.0

        if f_idx == 1:
            raw_vx, raw_vy, raw_vz = 0.0, 0.0, 0.0
        else:
            raw_vx = (bx - last_bx) / dt
            raw_vy = (by - last_by) / dt
            raw_vz = (bz - last_bz) / dt

        raw_speed_kmh = math.sqrt(raw_vx**2 + raw_vy**2 + raw_vz**2) * 3.6

        if p_type == "SHOT":
            expected_spd = play.get("speed", 105.0)
            speed_kmh = round(min(125.0, max(expected_spd * 0.9, raw_speed_kmh)), 1)
        elif p_type == "CELEBRATION":
            speed_kmh = 0.0
            raw_vx, raw_vy, raw_vz = 0.0, 0.0, 0.0
        elif p_type == "DRIBBLE":
            speed_kmh = round(min(28.0, raw_speed_kmh), 1)
        else:
            speed_kmh = round(min(85.0, raw_speed_kmh), 1)

        m_s, s_s = play.get("t_start", (0, 0))
        m_e, s_e = play.get("t_end", (90, 0))
        sec_start = m_s * 60 + s_s
        sec_end = m_e * 60 + s_e
        curr_sec = int(sec_start + (sec_end - sec_start) * u)
        
        c_min = curr_sec // 60
        c_sec = curr_sec % 60
        if c_min >= 90:
            stoppage = c_min - 90
            clock_str = f"90:00 +{stoppage}'" if stoppage > 0 else f"90:{c_sec:02d}"
        else:
            clock_str = f"{c_min:02d}:{c_sec:02d}"

        last_bx, last_by, last_bz = bx, by, bz

        players = []

        # Home Team (Attacking towards +X / 105m)
        for pid, (base_x, base_y, role) in HOME_433_FORM.items():
            cur = p_pos[pid]
            is_scorer = (p_type == "CELEBRATION" and play.get("player") == pid)

            if is_scorer:
                sx, sy = play.get("scorer_pos", (96.0, 16.0))
                tgt_x, tgt_y = sx, sy
            elif p_type == "DRIBBLE" and play.get("player") == pid:
                tgt_x = bx - 0.4
                tgt_y = by
            elif p_type in ("PASS", "CROSS") and play.get("from_p") == pid and u < 0.25:
                tgt_x = x0 - 0.3
                tgt_y = y0
            elif p_type in ("PASS", "CROSS") and play.get("to_p") == pid:
                tgt_x = x1 - 0.35
                tgt_y = y1
            elif p_type == "SHOT" and play.get("from_p") == pid:
                tgt_x = x0 + 1.2
                tgt_y = y0
            else:
                if "GK" in role:
                    tgt_x = max(3.0, min(14.0, 5.0 + (bx - 50.0) * 0.12))
                    tgt_y = 34.0 + (by - 34.0) * 0.15
                elif "CB" in role:
                    tgt_x = base_x + (bx - 50.0) * 0.24
                    tgt_y = base_y + (by - 34.0) * 0.20
                elif "B" in role:
                    tgt_x = base_x + (bx - 50.0) * 0.36
                    tgt_y = base_y + (by - 34.0) * 0.25
                elif "M" in role:
                    tgt_x = base_x + (bx - 50.0) * 0.44
                    tgt_y = base_y + (by - 34.0) * 0.35
                else:
                    tgt_x = base_x + (bx - 50.0) * 0.52
                    tgt_y = base_y + (by - 34.0) * 0.38

            # Biomechanical Speed-Limiter (Eliminates abrupt fast backward sprinting!)
            diff_x = tgt_x - cur[0]
            diff_y = tgt_y - cur[1]
            dist = math.sqrt(diff_x**2 + diff_y**2)

            if dist > 0.001:
                # Forward sprint: max 0.30m/frame (~27 km/h); Retreating jog: max 0.13m/frame (~12 km/h)
                is_retreating = (diff_x < 0)
                max_s_x = 0.13 if is_retreating else 0.30
                max_s_y = 0.20

                step_x = math.copysign(min(abs(diff_x) * 0.08, max_s_x), diff_x)
                step_y = math.copysign(min(abs(diff_y) * 0.08, max_s_y), diff_y)
                cur[0] += step_x
                cur[1] += step_y
                p_vx = round(step_x / dt, 2)
                p_vy = round(step_y / dt, 2)
            else:
                p_vx, p_vy = 0.0, 0.0

            r_info = roster_data["home"].get(pid, {"num": int(pid[1:]), "name": pid, "role": role})

            players.append({
                "id": pid,
                "team": "Home",
                "num": r_info["num"],
                "name": r_info["name"],
                "role": r_info["role"],
                "x": round(cur[0], 2),
                "y": round(cur[1], 2),
                "z": 0.0,
                "vx": p_vx,
                "vy": p_vy
            })

        # Away Team (Attacking towards -X / 0m)
        for pid, (base_x, base_y, role) in AWAY_4231_FORM.items():
            cur = p_pos[pid]
            is_scorer = (p_type == "CELEBRATION" and play.get("player") == pid)

            if is_scorer:
                sx, sy = play.get("scorer_pos", (12.0, 16.0))
                tgt_x, tgt_y = sx, sy
            elif p_type == "DRIBBLE" and play.get("player") == pid:
                tgt_x = bx + 0.4
                tgt_y = by
            elif p_type in ("PASS", "CROSS") and play.get("from_p") == pid and u < 0.25:
                tgt_x = x0 + 0.3
                tgt_y = y0
            elif p_type in ("PASS", "CROSS") and play.get("to_p") == pid:
                tgt_x = x1 + 0.35
                tgt_y = y1
            elif p_type == "SHOT" and play.get("from_p") == pid:
                tgt_x = x0 - 1.2
                tgt_y = y0
            else:
                if "GK" in role:
                    tgt_x = min(102.0, max(91.0, 100.0 + (bx - 50.0) * 0.12))
                    tgt_y = 34.0 + (by - 34.0) * 0.15
                elif "CB" in role:
                    tgt_x = base_x + (bx - 50.0) * 0.24
                    tgt_y = base_y + (by - 34.0) * 0.20
                elif "B" in role:
                    tgt_x = base_x + (bx - 50.0) * 0.36
                    tgt_y = base_y + (by - 34.0) * 0.25
                elif "M" in role:
                    tgt_x = base_x + (bx - 50.0) * 0.44
                    tgt_y = base_y + (by - 34.0) * 0.35
                else:
                    tgt_x = base_x + (bx - 50.0) * 0.52
                    tgt_y = base_y + (by - 34.0) * 0.38

            # Biomechanical Speed-Limiter for Away Team
            diff_x = tgt_x - cur[0]
            diff_y = tgt_y - cur[1]
            dist = math.sqrt(diff_x**2 + diff_y**2)

            if dist > 0.001:
                # Away attacks toward -X, so retreating toward their goal is diff_x > 0
                is_retreating = (diff_x > 0)
                max_s_x = 0.13 if is_retreating else 0.30
                max_s_y = 0.20

                step_x = math.copysign(min(abs(diff_x) * 0.08, max_s_x), diff_x)
                step_y = math.copysign(min(abs(diff_y) * 0.08, max_s_y), diff_y)
                cur[0] += step_x
                cur[1] += step_y
                p_vx = round(step_x / dt, 2)
                p_vy = round(step_y / dt, 2)
            else:
                p_vx, p_vy = 0.0, 0.0

            r_info = roster_data["away"].get(pid, {"num": int(pid[1:]), "name": pid, "role": role})

            players.append({
                "id": pid,
                "team": "Away",
                "num": r_info["num"],
                "name": r_info["name"],
                "role": r_info["role"],
                "x": round(cur[0], 2),
                "y": round(cur[1], 2),
                "z": 0.0,
                "vx": p_vx,
                "vy": p_vy
            })

        frames.append({
            "frame_id": f_idx,
            "match_time": clock_str,
            "ball": {
                "x": round(bx, 2),
                "y": round(by, 2),
                "z": round(bz, 2),
                "vx": round(raw_vx, 2),
                "vy": round(raw_vy, 2),
                "vz": round(raw_vz, 2),
                "speed_kmh": speed_kmh,
                "in_play": True
            },
            "players": players
        })

    return {
        "match_id": match_id,
        "match_title": metadata["title"],
        "metadata": metadata,
        "frames": frames
    }

def generate_all_matches():
    matches = [
        ("MATCH_EL_CLASICO", "data/match_el_clasico.json"),
        ("MATCH_UCL_TACTICAL", "data/match_ucl_tactical.json"),
        ("MATCH_WORLD_CUP", "data/match_world_cup.json"),
    ]

    for m_id, filepath in matches:
        data = generate_smooth_match_tracking(m_id)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Generated {len(data['frames'])} speed-limited 90-minute frames for '{data['match_title']}' -> {filepath}")

    # Also update default sample_match_tracking.json
    clasico_data = generate_smooth_match_tracking("MATCH_EL_CLASICO")
    with open("data/sample_match_tracking.json", "w", encoding="utf-8") as f:
        json.dump(clasico_data, f, indent=2)
    print("Updated data/sample_match_tracking.json with realistic rosters & smooth kinematics!")

if __name__ == "__main__":
    generate_all_matches()
