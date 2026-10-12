import urllib.request
import json
import math
import os

HEADERS = {'User-Agent': 'Mozilla/5.0'}

def fetch_statsbomb(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode('utf-8'))

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

MATCH_DEFS = [
    {
        "id": "MATCH_EL_CLASICO_2017",
        "title": "⚽ Real Madrid 2 - 3 Barcelona (La Liga 2017 · Messi 92' Iconic Bernabéu Winner)",
        "competition": "La Liga EA Sports · Santiago Bernabéu (Real Madrid 2 - 3 Barcelona)",
        "sb_url": "https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/267569.json",
        "home_team": {
            "name": "Real Madrid",
            "short": "RMA",
            "color": "#eab308",
            "color_sec": "#f8fafc",
            "badge": "RMA",
            "pattern": "white"
        },
        "away_team": {
            "name": "FC Barcelona",
            "short": "BAR",
            "color": "#ef4444",
            "color_sec": "#2563eb",
            "badge": "BAR",
            "pattern": "blaugrana"
        },
        "home_gk": "Keylor Navas (RMA)",
        "away_gk": "Marc-André ter Stegen (BAR)",
        "roster": {
            "home": {
                "H1": {"num": 1, "name": "Keylor Navas", "role": "GK"},
                "H2": {"num": 2, "name": "Carvajal", "role": "RB"},
                "H3": {"num": 4, "name": "Sergio Ramos", "role": "CB"},
                "H4": {"num": 6, "name": "Nacho", "role": "CB"},
                "H5": {"num": 12, "name": "Marcelo", "role": "LB"},
                "H6": {"num": 14, "name": "Casemiro", "role": "DM"},
                "H7": {"num": 11, "name": "Gareth Bale", "role": "RW"},
                "H8": {"num": 19, "name": "Luka Modrić", "role": "CM"},
                "H9": {"num": 8, "name": "Toni Kroos", "role": "CM"},
                "H10": {"num": 9, "name": "Karim Benzema", "role": "ST"},
                "H11": {"num": 7, "name": "Cristiano Ronaldo", "role": "LW"},
            },
            "away": {
                "A1": {"num": 1, "name": "Ter Stegen", "role": "GK"},
                "A2": {"num": 18, "name": "Jordi Alba", "role": "LB"},
                "A3": {"num": 23, "name": "Samuel Umtiti", "role": "CB"},
                "A4": {"num": 3, "name": "Gerard Piqué", "role": "CB"},
                "A5": {"num": 20, "name": "Sergi Roberto", "role": "RB"},
                "A6": {"num": 5, "name": "Sergio Busquets", "role": "DM"},
                "A7": {"num": 4, "name": "Ivan Rakitić", "role": "CM"},
                "A8": {"num": 8, "name": "Andrés Iniesta", "role": "CM"},
                "A9": {"num": 17, "name": "Paco Alcácer", "role": "LW"},
                "A10": {"num": 9, "name": "Luis Suárez", "role": "ST"},
                "A11": {"num": 10, "name": "Lionel Messi", "role": "RW"},
            }
        }
    },
    {
        "id": "MATCH_WORLD_CUP_2022",
        "title": "🌍 Argentina 3 - 3 France (FIFA World Cup 2022 Final · Lusail Epic 120')",
        "competition": "FIFA World Cup Final 2022 · Lusail Iconic Stadium (3 - 3 a.e.t)",
        "sb_url": "https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/3869685.json",
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
        "home_gk": "Emiliano Martínez (ARG)",
        "away_gk": "Hugo Lloris (FRA)",
        "roster": {
            "home": {
                "H1": {"num": 23, "name": "E. Martínez", "role": "GK"},
                "H2": {"num": 26, "name": "N. Molina", "role": "RB"},
                "H3": {"num": 13, "name": "C. Romero", "role": "CB"},
                "H4": {"num": 19, "name": "N. Otamendi", "role": "CB"},
                "H5": {"num": 8, "name": "M. Acuña", "role": "LB"},
                "H6": {"num": 24, "name": "Enzo Fernández", "role": "DM"},
                "H7": {"num": 11, "name": "Ángel Di María", "role": "RW"},
                "H8": {"num": 7, "name": "Rodrigo De Paul", "role": "CM"},
                "H9": {"num": 20, "name": "A. Mac Allister", "role": "CM"},
                "H10": {"num": 10, "name": "Lionel Messi", "role": "ST"},
                "H11": {"num": 9, "name": "Julián Álvarez", "role": "LW"},
            },
            "away": {
                "A1": {"num": 1, "name": "Hugo Lloris", "role": "GK"},
                "A2": {"num": 22, "name": "Théo Hernandez", "role": "LB"},
                "A3": {"num": 18, "name": "D. Upamecano", "role": "CB"},
                "A4": {"num": 4, "name": "Raphaël Varane", "role": "CB"},
                "A5": {"num": 5, "name": "Jules Koundé", "role": "RB"},
                "A6": {"num": 8, "name": "A. Tchouaméni", "role": "DM"},
                "A7": {"num": 14, "name": "Adrien Rabiot", "role": "DM"},
                "A8": {"num": 7, "name": "A. Griezmann", "role": "AM"},
                "A9": {"num": 11, "name": "O. Dembélé", "role": "LM"},
                "A10": {"num": 9, "name": "Olivier Giroud", "role": "RM"},
                "A11": {"num": 10, "name": "Kylian Mbappé", "role": "ST"},
            }
        }
    },
    {
        "id": "MATCH_EL_CLASICO_5_0",
        "title": "⚡ Barcelona 5 - 0 Real Madrid (La Liga 2010 · Pep's Camp Nou Manita)",
        "competition": "La Liga EA Sports · Camp Nou (FC Barcelona 5 - 0 Real Madrid)",
        "sb_url": "https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/69299.json",
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
        "home_gk": "Víctor Valdés (BAR)",
        "away_gk": "Iker Casillas (RMA)",
        "roster": {
            "home": {
                "H1": {"num": 1, "name": "Víctor Valdés", "role": "GK"},
                "H2": {"num": 2, "name": "Dani Alves", "role": "RB"},
                "H3": {"num": 5, "name": "Carles Puyol", "role": "CB"},
                "H4": {"num": 3, "name": "Gerard Piqué", "role": "CB"},
                "H5": {"num": 22, "name": "Éric Abidal", "role": "LB"},
                "H6": {"num": 16, "name": "Sergio Busquets", "role": "DM"},
                "H7": {"num": 17, "name": "Pedro", "role": "RW"},
                "H8": {"num": 6, "name": "Xavi Hernández", "role": "CM"},
                "H9": {"num": 8, "name": "Andrés Iniesta", "role": "CM"},
                "H10": {"num": 7, "name": "David Villa", "role": "ST"},
                "H11": {"num": 10, "name": "Lionel Messi", "role": "LW"},
            },
            "away": {
                "A1": {"num": 1, "name": "Iker Casillas", "role": "GK"},
                "A2": {"num": 12, "name": "Marcelo", "role": "LB"},
                "A3": {"num": 2, "name": "Ricardo Carvalho", "role": "CB"},
                "A4": {"num": 3, "name": "Pepe", "role": "CB"},
                "A5": {"num": 4, "name": "Sergio Ramos", "role": "RB"},
                "A6": {"num": 14, "name": "Xabi Alonso", "role": "DM"},
                "A7": {"num": 24, "name": "Sami Khedira", "role": "DM"},
                "A8": {"num": 23, "name": "Mesut Özil", "role": "AM"},
                "A9": {"num": 22, "name": "Ángel Di María", "role": "LM"},
                "A10": {"num": 7, "name": "Cristiano Ronaldo", "role": "RM"},
                "A11": {"num": 20, "name": "Gonzalo Higuaín", "role": "ST"},
            }
        }
    },
    {
        "id": "MATCH_UCL_WEMBLEY_2011",
        "title": "🏆 Barcelona 3 - 1 Manchester United (UCL Final 2011 · Wembley Masterclass)",
        "competition": "UEFA Champions League Final · Wembley Stadium London (3 - 1)",
        "sb_url": "https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/18236.json",
        "home_team": {
            "name": "FC Barcelona",
            "short": "BAR",
            "color": "#ef4444",
            "color_sec": "#2563eb",
            "badge": "BAR",
            "pattern": "blaugrana"
        },
        "away_team": {
            "name": "Manchester United",
            "short": "MUN",
            "color": "#dc2626",
            "color_sec": "#ffffff",
            "badge": "MUN",
            "pattern": "red"
        },
        "home_gk": "Víctor Valdés (BAR)",
        "away_gk": "Edwin van der Sar (MUN)",
        "roster": {
            "home": {
                "H1": {"num": 1, "name": "Víctor Valdés", "role": "GK"},
                "H2": {"num": 2, "name": "Dani Alves", "role": "RB"},
                "H3": {"num": 14, "name": "Javier Mascherano", "role": "CB"},
                "H4": {"num": 3, "name": "Gerard Piqué", "role": "CB"},
                "H5": {"num": 22, "name": "Éric Abidal", "role": "LB"},
                "H6": {"num": 16, "name": "Sergio Busquets", "role": "DM"},
                "H7": {"num": 17, "name": "Pedro", "role": "RW"},
                "H8": {"num": 6, "name": "Xavi Hernández", "role": "CM"},
                "H9": {"num": 8, "name": "Andrés Iniesta", "role": "CM"},
                "H10": {"num": 7, "name": "David Villa", "role": "ST"},
                "H11": {"num": 10, "name": "Lionel Messi", "role": "LW"},
            },
            "away": {
                "A1": {"num": 1, "name": "Van der Sar", "role": "GK"},
                "A2": {"num": 3, "name": "Patrice Evra", "role": "LB"},
                "A3": {"num": 15, "name": "Nemanja Vidić", "role": "CB"},
                "A4": {"num": 5, "name": "Rio Ferdinand", "role": "CB"},
                "A5": {"num": 20, "name": "Fábio", "role": "RB"},
                "A6": {"num": 16, "name": "Michael Carrick", "role": "DM"},
                "A7": {"num": 11, "name": "Ryan Giggs", "role": "DM"},
                "A8": {"num": 13, "name": "Park Ji-sung", "role": "LM"},
                "A9": {"num": 25, "name": "Antonio Valencia", "role": "RM"},
                "A10": {"num": 10, "name": "Wayne Rooney", "role": "SS"},
                "A11": {"num": 14, "name": "Javier Hernández", "role": "ST"},
            }
        }
    },
    {
        "id": "MATCH_UCL_FINAL_2015",
        "title": "🏆 Juventus 1 - 3 Barcelona (UCL Final 2015 · Olympiastadion Berlin Treble)",
        "competition": "UEFA Champions League Final · Olympiastadion Berlin (1 - 3)",
        "sb_url": "https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/18242.json",
        "home_team": {
            "name": "Juventus",
            "short": "JUV",
            "color": "#0f172a",
            "color_sec": "#ffffff",
            "badge": "JUV",
            "pattern": "bianconeri"
        },
        "away_team": {
            "name": "FC Barcelona",
            "short": "BAR",
            "color": "#ef4444",
            "color_sec": "#2563eb",
            "badge": "BAR",
            "pattern": "blaugrana"
        },
        "home_gk": "Gianluigi Buffon (JUV)",
        "away_gk": "Marc-André ter Stegen (BAR)",
        "roster": {
            "home": {
                "H1": {"num": 1, "name": "Gianluigi Buffon", "role": "GK"},
                "H2": {"num": 26, "name": "Stephan Lichtsteiner", "role": "RB"},
                "H3": {"num": 19, "name": "Leonardo Bonucci", "role": "CB"},
                "H4": {"num": 15, "name": "Andrea Barzagli", "role": "CB"},
                "H5": {"num": 33, "name": "Patrice Evra", "role": "LB"},
                "H6": {"num": 21, "name": "Andrea Pirlo", "role": "DM"},
                "H7": {"num": 8, "name": "Claudio Marchisio", "role": "CM"},
                "H8": {"num": 6, "name": "Paul Pogba", "role": "CM"},
                "H9": {"num": 23, "name": "Arturo Vidal", "role": "AM"},
                "H10": {"num": 10, "name": "Carlos Tévez", "role": "ST"},
                "H11": {"num": 9, "name": "Álvaro Morata", "role": "ST"},
            },
            "away": {
                "A1": {"num": 1, "name": "Ter Stegen", "role": "GK"},
                "A2": {"num": 18, "name": "Jordi Alba", "role": "LB"},
                "A3": {"num": 14, "name": "Javier Mascherano", "role": "CB"},
                "A4": {"num": 3, "name": "Gerard Piqué", "role": "CB"},
                "A5": {"num": 22, "name": "Dani Alves", "role": "RB"},
                "A6": {"num": 5, "name": "Sergio Busquets", "role": "DM"},
                "A7": {"num": 4, "name": "Ivan Rakitić", "role": "CM"},
                "A8": {"num": 8, "name": "Andrés Iniesta", "role": "CM"},
                "A9": {"num": 11, "name": "Neymar Jr", "role": "LW"},
                "A10": {"num": 9, "name": "Luis Suárez", "role": "ST"},
                "A11": {"num": 10, "name": "Lionel Messi", "role": "RW"},
            }
        }
    }
]

def parse_statsbomb_match(m_def):
    print(f"Processing real match: {m_def['title']}")
    events = fetch_statsbomb(m_def["sb_url"])

    home_name = m_def["home_team"]["name"]
    away_name = m_def["away_team"]["name"]
    home_gk = m_def["home_gk"]
    away_gk = m_def["away_gk"]

    goals = []
    fouls = []
    score_home = 0
    score_away = 0

    for i, ev in enumerate(events):
        ev_type = ev.get('type', {}).get('name')
        t_name = ev.get('team', {}).get('name')
        is_home = (home_name in t_name)
        minute = ev.get('minute', 0)
        second = ev.get('second', 0)

        # 1. Real Goals & Assists
        if ev_type == 'Shot' and ev.get('shot', {}).get('outcome', {}).get('name') == 'Goal':
            shot = ev.get('shot', {})
            player_name = ev.get('player', {}).get('name', 'Unknown')
            shot_type = shot.get('type', {}).get('name', 'Open Play')

            assist_name = None
            prev_events = events[max(0, i-6):i]
            for pev in reversed(prev_events):
                if pev.get('type', {}).get('name') == 'Pass' and pev.get('team', {}).get('name') == t_name:
                    assist_name = pev.get('player', {}).get('name')
                    break

            end_loc = shot.get('end_location', [120.0, 40.0, 1.0])
            sb_y = end_loc[1] if len(end_loc) > 1 else 40.0
            sb_z = end_loc[2] if len(end_loc) > 2 else 1.0

            target_goal_x = 105.0 if is_home else 0.0
            pitch_entry_y = round(34.0 + (sb_y - 40.0) / 4.0 * 3.66, 2)
            pitch_entry_z = round(min(2.44, max(0.1, sb_z)), 2)

            gk_facing = away_gk if is_home else home_gk

            if sb_y < 38.67:
                h_zone = "Top Corner (Left)" if sb_z > 1.22 else "Bottom Corner (Left)"
                zone_code = "TL" if sb_z > 1.22 else "BL"
            elif sb_y > 41.33:
                h_zone = "Top Corner (Right)" if sb_z > 1.22 else "Bottom Corner (Right)"
                zone_code = "TR" if sb_z > 1.22 else "BR"
            else:
                h_zone = "High Center" if sb_z > 1.22 else "Low Center"
                zone_code = "TC" if sb_z > 1.22 else "BC"

            if is_home:
                score_home += 1
            else:
                score_away += 1

            speed = round(94.0 + (i % 25) * 1.1, 1)

            goals.append({
                "minute": minute,
                "second": second,
                "team": "Home" if is_home else "Away",
                "scorer": player_name,
                "assist": assist_name or "Solo Individual Effort",
                "type": f"{shot_type} ({h_zone})",
                "speed_kmh": speed,
                "goalkeeper": gk_facing,
                "entry_x": target_goal_x,
                "entry_y": pitch_entry_y,
                "entry_z": pitch_entry_z,
                "zone_code": zone_code,
                "zone_label": h_zone,
                "score_after": [score_home, score_away]
            })

        # 2. Real Tackles & Card Fouls
        if ev_type == 'Foul Committed' and ev.get('foul_committed', {}).get('card'):
            card_type = ev.get('foul_committed', {}).get('card', {}).get('name', 'Yellow Card')
            foul_player = ev.get('player', {}).get('name', 'Unknown')
            fouled_player = "Opponent"
            for rel_id in ev.get('related_events', []):
                for check_ev in events[max(0, i-4):min(len(events), i+5)]:
                    if check_ev.get('id') == rel_id and check_ev.get('type', {}).get('name') == 'Foul Won':
                        fouled_player = check_ev.get('player', {}).get('name', 'Opponent')
                        break

            loc = ev.get('location', [60.0, 34.0])
            pitch_x = round((loc[0] / 120.0) * 105.0, 1)
            pitch_y = round((loc[1] / 80.0) * 68.0, 1)

            fouls.append({
                "minute": minute,
                "second": second,
                "team": "Home" if is_home else "Away",
                "tackler": foul_player,
                "victim": fouled_player,
                "card": card_type,
                "action": "Hard Sliding Tackle" if card_type == "Red Card" else "Tactical Foul / Trip",
                "loc": (pitch_x, pitch_y)
            })

    # Goalkeeper Heatmap Aggregation
    gk_stats = {}
    for g in goals:
        gk = g["goalkeeper"]
        if gk not in gk_stats:
            gk_stats[gk] = {
                "name": gk,
                "total_conceded": 0,
                "zones": {"TL": 0, "TC": 0, "TR": 0, "BL": 0, "BC": 0, "BR": 0}
            }
        gk_stats[gk]["total_conceded"] += 1
        z = g.get("zone_code", "BC")
        gk_stats[gk]["zones"][z] = gk_stats[gk]["zones"].get(z, 0) + 1

    # Chapters Generation
    chapters = [{"min": 1, "label": "⏱ 01' Kick-Off", "desc": "Match Kick-Off & Tactical Setup"}]
    for f in fouls:
        if f["card"] == "Red Card":
            chapters.append({
                "min": f["minute"],
                "label": f"🟥 {f['minute']}' Red Card!",
                "desc": f"{f['tackler']} sliding tackle foul on {f['victim']}"
            })
    for g in goals:
        chapters.append({
            "min": g["minute"],
            "label": f"⚽ {g['minute']}' GOAL! ({g['score_after'][0]}-{g['score_after'][1]})",
            "desc": f"{g['scorer']} strike vs {g['goalkeeper']}"
        })
    chapters.append({"min": 45, "label": "🛡 45' Halftime", "desc": "Tactical interval & adjustments"})
    chapters.append({"min": 90, "label": "🏁 90' Full Time", "desc": "Final whistle & post-match summary"})
    chapters.sort(key=lambda c: c["min"])

    # Plays Synthesis for Full 90-Minute Continuous Kinematics
    plays = []
    # Build continuous sequence connecting from kick-off through fouls and goals
    curr_t = (0, 30)
    last_pt = (52.5, 34.0)

    # Sort key events chronologically
    key_events = []
    for g in goals:
        key_events.append({"type": "GOAL", "data": g, "min": g["minute"], "sec": g["second"]})
    for f in fouls:
        key_events.append({"type": "FOUL", "data": f, "min": f["minute"], "sec": f["second"]})
    key_events.sort(key=lambda x: (x["min"], x["sec"]))

    for ev in key_events:
        t_target = (ev["min"], ev["sec"])
        if ev["type"] == "GOAL":
            g = ev["data"]
            is_h = (g["team"] == "Home")
            shoot_player = "H10" if is_h else "A11"
            assist_player = "H8" if is_h else "A8"
            gk_player = "A1" if is_h else "H1"

            # Pre-goal build-up pass
            mid_pt = (74.0, 30.0) if is_h else (32.0, 38.0)
            plays.append({
                "type": "PASS",
                "from_p": assist_player,
                "to_p": shoot_player,
                "dur": 70,
                "start": last_pt,
                "end": mid_pt,
                "t_start": (max(0, ev["min"] - 1), 20),
                "t_end": (ev["min"], max(0, ev["sec"] - 8))
            })
            # Goal Strike
            goal_dest = (g["entry_x"], g["entry_y"])
            plays.append({
                "type": "SHOT",
                "from_p": shoot_player,
                "dur": 55,
                "start": mid_pt,
                "end": goal_dest,
                "h": g["entry_z"],
                "speed": g["speed_kmh"],
                "is_goal": True,
                "goal_data": g,
                "t_start": (ev["min"], max(0, ev["sec"] - 8)),
                "t_end": (ev["min"], ev["sec"])
            })
            # Goal Celebration
            scorer_corner = (98.0, 16.0) if is_h else (10.0, 16.0)
            plays.append({
                "type": "CELEBRATION",
                "player": shoot_player,
                "dur": 110,
                "start": goal_dest,
                "end": goal_dest,
                "scorer_pos": scorer_corner,
                "t_start": (ev["min"], ev["sec"]),
                "t_end": (min(90, ev["min"] + 2), 0)
            })
            last_pt = (52.5, 34.0)

        elif ev["type"] == "FOUL":
            f = ev["data"]
            f_loc = f["loc"]
            tackler_p = "H3" if f["team"] == "Home" else "A4"
            victim_p = "A10" if f["team"] == "Home" else "H10"

            plays.append({
                "type": "TACKLE",
                "tackler": tackler_p,
                "victim": victim_p,
                "dur": 80,
                "start": last_pt,
                "end": f_loc,
                "foul_data": f,
                "t_start": (max(0, ev["min"] - 1), 30),
                "t_end": (ev["min"], ev["sec"])
            })
            last_pt = f_loc

    # Final play to whistle
    plays.append({
        "type": "DRIBBLE",
        "player": "H6",
        "dur": 90,
        "start": last_pt,
        "end": (52.5, 34.0),
        "t_start": (89, 0),
        "t_end": (90, 0)
    })

    metadata = {
        "match_id": m_def["id"],
        "title": m_def["title"],
        "competition": m_def["competition"],
        "home_team": m_def["home_team"],
        "away_team": m_def["away_team"],
        "goals": goals,
        "fouls": fouls,
        "goalkeepers": list(gk_stats.values()),
        "chapters": chapters
    }

    # Generate kinematic frames
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
    dt = 0.04

    roster_data = m_def["roster"]

    for f_idx in range(1, total_frames + 1):
        cur_item = next((item for item in timeline if item["start_frame"] <= f_idx <= item["end_frame"]), timeline[-1])
        play = cur_item["play"]
        p_start = cur_item["start_frame"]
        p_dur = cur_item["dur"]
        p_type = play["type"]

        u = max(0.0, min(1.0, (f_idx - p_start) / max(1, p_dur - 1)))
        x0, y0 = play["start"]
        x1, y1 = play["end"]

        # Physics Ball Movement
        if p_type == "DRIBBLE":
            s = u * u * (3.0 - 2.0 * u)
            bx = x0 + (x1 - x0) * s
            by = y0 + (y1 - y0) * s
            bz = 0.0
        elif p_type == "PASS":
            s = 1.0 - math.pow(1.0 - u, 1.6)
            bx = x0 + (x1 - x0) * s
            by = y0 + (y1 - y0) * s
            bz = math.sin(u * math.pi) * play.get("h", 0.0)
        elif p_type == "SHOT":
            bx = x0 + (x1 - x0) * u
            by = y0 + (y1 - y0) * u
            max_h = play.get("h", 1.2)
            bz = (0.2 + (max_h - 0.2) * u) + math.sin(u * math.pi) * 0.2
        elif p_type == "TACKLE":
            # Ball rolls loose or gets tackled
            bx = x0 + (x1 - x0) * u
            by = y0 + (y1 - y0) * u
            bz = 0.0
        elif p_type == "CELEBRATION":
            bx = x1
            by = y1
            bz = 0.0
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
            speed_kmh = round(play.get("speed", 100.0), 1)
        elif p_type in ("CELEBRATION", "TACKLE"):
            speed_kmh = round(min(22.0, raw_speed_kmh), 1)
        else:
            speed_kmh = round(min(75.0, raw_speed_kmh), 1)

        m_s, s_s = play.get("t_start", (0, 0))
        m_e, s_e = play.get("t_end", (90, 0))
        sec_start = m_s * 60 + s_s
        sec_end = m_e * 60 + s_e
        curr_sec = int(sec_start + (sec_end - sec_start) * u)

        c_min = curr_sec // 60
        c_sec = curr_sec % 60
        clock_str = f"{c_min:02d}:{c_sec:02d}"

        last_bx, last_by, last_bz = bx, by, bz

        players = []

        # Home Team
        for pid, (base_x, base_y, role) in HOME_433_FORM.items():
            cur = p_pos[pid]
            is_scorer = (p_type == "CELEBRATION" and play.get("player") == pid)
            is_tackler = (p_type == "TACKLE" and play.get("tackler") == pid)
            is_victim = (p_type == "TACKLE" and play.get("victim") == pid)

            if is_scorer:
                tgt_x, tgt_y = play.get("scorer_pos", (96.0, 16.0))
            elif is_tackler:
                tgt_x, tgt_y = bx + 0.3, by + 0.2
            elif is_victim:
                tgt_x, tgt_y = bx - 0.2, by - 0.2
            elif p_type == "DRIBBLE" and play.get("player") == pid:
                tgt_x = bx - 0.4
                tgt_y = by
            elif p_type == "PASS" and play.get("from_p") == pid and u < 0.25:
                tgt_x = x0 - 0.3
                tgt_y = y0
            elif p_type == "PASS" and play.get("to_p") == pid:
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

            diff_x = tgt_x - cur[0]
            diff_y = tgt_y - cur[1]
            dist = math.sqrt(diff_x**2 + diff_y**2)
            if dist > 0.001:
                is_retreating = (diff_x < 0)
                max_s_x = 0.14 if is_retreating else 0.30
                max_s_y = 0.20
                step_x = math.copysign(min(abs(diff_x) * 0.09, max_s_x), diff_x)
                step_y = math.copysign(min(abs(diff_y) * 0.09, max_s_y), diff_y)
                cur[0] += step_x
                cur[1] += step_y
                p_vx = round(step_x / dt, 2)
                p_vy = round(step_y / dt, 2)
            else:
                p_vx, p_vy = 0.0, 0.0

            r_info = roster_data["home"].get(pid, {"num": int(pid[1:]), "name": pid, "role": role})

            # Check special pose action (tackle sliding vs falling down)
            action_pose = "NORMAL"
            if is_tackler and 0.2 <= u <= 0.8:
                action_pose = "SLIDING_TACKLE"
            elif is_victim and 0.3 <= u <= 0.8:
                action_pose = "FOUL_FALL"

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
                "vy": p_vy,
                "action": action_pose
            })

        # Away Team
        for pid, (base_x, base_y, role) in AWAY_4231_FORM.items():
            cur = p_pos[pid]
            is_scorer = (p_type == "CELEBRATION" and play.get("player") == pid)
            is_tackler = (p_type == "TACKLE" and play.get("tackler") == pid)
            is_victim = (p_type == "TACKLE" and play.get("victim") == pid)

            if is_scorer:
                tgt_x, tgt_y = play.get("scorer_pos", (12.0, 16.0))
            elif is_tackler:
                tgt_x, tgt_y = bx - 0.3, by + 0.2
            elif is_victim:
                tgt_x, tgt_y = bx + 0.2, by - 0.2
            elif p_type == "DRIBBLE" and play.get("player") == pid:
                tgt_x = bx + 0.4
                tgt_y = by
            elif p_type == "PASS" and play.get("from_p") == pid and u < 0.25:
                tgt_x = x0 + 0.3
                tgt_y = y0
            elif p_type == "PASS" and play.get("to_p") == pid:
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

            diff_x = tgt_x - cur[0]
            diff_y = tgt_y - cur[1]
            dist = math.sqrt(diff_x**2 + diff_y**2)
            if dist > 0.001:
                is_retreating = (diff_x > 0)
                max_s_x = 0.14 if is_retreating else 0.30
                max_s_y = 0.20
                step_x = math.copysign(min(abs(diff_x) * 0.09, max_s_x), diff_x)
                step_y = math.copysign(min(abs(diff_y) * 0.09, max_s_y), diff_y)
                cur[0] += step_x
                cur[1] += step_y
                p_vx = round(step_x / dt, 2)
                p_vy = round(step_y / dt, 2)
            else:
                p_vx, p_vy = 0.0, 0.0

            r_info = roster_data["away"].get(pid, {"num": int(pid[1:]), "name": pid, "role": role})

            action_pose = "NORMAL"
            if is_tackler and 0.2 <= u <= 0.8:
                action_pose = "SLIDING_TACKLE"
            elif is_victim and 0.3 <= u <= 0.8:
                action_pose = "FOUL_FALL"

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
                "vy": p_vy,
                "action": action_pose
            })

        # Include active play metadata on frame if goal or foul is occurring
        f_active_event = None
        if p_type == "SHOT" and play.get("is_goal"):
            f_active_event = {"type": "GOAL", "goal": play.get("goal_data")}
        elif p_type == "TACKLE":
            f_active_event = {"type": "FOUL", "foul": play.get("foul_data")}

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
            "players": players,
            "event": f_active_event
        })

    return {
        "match_id": m_def["id"],
        "match_title": metadata["title"],
        "metadata": metadata,
        "frames": frames
    }

def build_all():
    os.makedirs("data", exist_ok=True)
    generated = []
    for m_def in MATCH_DEFS:
        match_data = parse_statsbomb_match(m_def)
        fname = f"data/{m_def['id'].lower()}.json"
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(match_data, f, indent=2)
        print(f"Saved {fname}: {len(match_data['frames'])} frames, {len(match_data['metadata']['goals'])} goals, {len(match_data['metadata']['fouls'])} fouls.")
        generated.append((m_def["id"], fname))

    # Also symlink or copy the flagship 2017 El Clasico to default sample_match_tracking.json and match_el_clasico.json
    with open("data/match_el_clasico_2017.json", "r", encoding="utf-8") as f:
        clasico_17 = json.load(f)
    with open("data/sample_match_tracking.json", "w", encoding="utf-8") as f:
        json.dump(clasico_17, f, indent=2)
    with open("data/match_el_clasico.json", "w", encoding="utf-8") as f:
        json.dump(clasico_17, f, indent=2)
    print("Flagship default match updated!")

if __name__ == "__main__":
    build_all()
