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
    "H10": (68.0, 34.0, "ST"),
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
    "A8": (60.0, 32.5, "AM"),
    "A9": (57.0, 12.0, "LM"),
    "A10": (57.0, 56.0, "RM"),
    "A11": (49.0, 35.5, "ST"),
}

POS_TO_SLOT_HOME = {
    "Goalkeeper": "H1",
    "Right Back": "H2", "Right Wing Back": "H2",
    "Right Center Back": "H3", "Center Back": "H3",
    "Left Center Back": "H4",
    "Left Back": "H5", "Left Wing Back": "H5",
    "Center Defensive Midfield": "H6", "Defensive Midfield": "H6", "Right Defensive Midfield": "H6", "Left Defensive Midfield": "H6",
    "Right Center Midfield": "H7", "Right Wing": "H7", "Right Midfield": "H7",
    "Center Midfield": "H8",
    "Left Center Midfield": "H9", "Center Attacking Midfield": "H9",
    "Center Forward": "H10", "Secondary Striker": "H10", "Right Center Forward": "H10",
    "Left Wing": "H11", "Left Midfield": "H11", "Left Center Forward": "H11"
}

POS_TO_SLOT_AWAY = {
    "Goalkeeper": "A1",
    "Left Back": "A2", "Left Wing Back": "A2",
    "Left Center Back": "A3", "Center Back": "A3",
    "Right Center Back": "A4",
    "Right Back": "A5", "Right Wing Back": "A5",
    "Left Defensive Midfield": "A6", "Defensive Midfield": "A6", "Center Defensive Midfield": "A6",
    "Right Defensive Midfield": "A7", "Center Midfield": "A7",
    "Center Attacking Midfield": "A8", "Left Center Midfield": "A8",
    "Left Midfield": "A9", "Left Wing": "A9",
    "Right Midfield": "A10", "Right Wing": "A10", "Right Center Midfield": "A10",
    "Center Forward": "A11", "Secondary Striker": "A11", "Right Center Forward": "A11", "Left Center Forward": "A11"
}

def get_real_lineup(events, team_name):
    for ev in events:
        if ev.get("type", {}).get("name") == "Starting XI" and team_name in ev.get("team", {}).get("name", ""):
            return ev.get("tactics", {}).get("lineup", [])
    return []

def build_roster_from_lineup(lineup, is_home):
    prefix = "H" if is_home else "A"
    pos_map = POS_TO_SLOT_HOME if is_home else POS_TO_SLOT_AWAY
    slots = {}
    assigned_players = set()
    used_slots = set()

    for p in lineup:
        pos = p["position"]["name"]
        candidate_slot = pos_map.get(pos)
        if candidate_slot and candidate_slot not in used_slots:
            slots[candidate_slot] = p
            used_slots.add(candidate_slot)
            assigned_players.add(p["player"]["id"])

    all_slots = [f"{prefix}{i}" for i in range(1, 12)]
    unassigned = [p for p in lineup if p["player"]["id"] not in assigned_players]
    u_idx = 0
    for s in all_slots:
        if s not in slots and u_idx < len(unassigned):
            slots[s] = unassigned[u_idx]
            u_idx += 1

    roster = {}
    KNOWN_STAR_NAMES = {
        "Keylor Navas": "Navas",
        "Daniel Carvajal": "Carvajal",
        "José Ignacio Fernández": "Nacho",
        "Sergio Ramos": "Ramos",
        "Marcelo Vieira": "Marcelo",
        "Carlos Henrique Casimiro": "Casemiro",
        "Luka Modrić": "Modric",
        "Cristiano Ronaldo": "C. Ronaldo",
        "Toni Kroos": "Kroos",
        "Karim Benzema": "Benzema",
        "Gareth Frank Bale": "Bale",
        "Marc-André ter Stegen": "Ter Stegen",
        "Jordi Alba": "Jordi Alba",
        "Samuel Yves Umtiti": "Umtiti",
        "Gerard Piqué": "Pique",
        "Sergi Roberto": "Sergi Roberto",
        "Sergio Busquets": "Busquets",
        "Lionel Andrés Messi": "Messi",
        "Andrés Iniesta": "Iniesta",
        "Francisco Alcácer": "Paco Alcácer",
        "Ivan Rakitić": "Rakitic",
        "Luis Alberto Suárez": "Suarez",
        "James David Rodríguez": "James",
        "Mateo Kovačić": "Kovacic",
        "Marco Asensio": "Asensio",
        "Kylian Mbappé": "Mbappe",
        "Ángel Fabián Di María": "Di Maria",
        "Emiliano Martínez": "E. Martinez",
        "Hugo Lloris": "Lloris",
        "Antoine Griezmann": "Griezmann",
        "Olivier Giroud": "Giroud",
        "Rodrigo Javier De Paul": "De Paul",
        "Julián Álvarez": "Alvarez",
        "Alexis Mac Allister": "Mac Allister",
        "Enzo Jeremías Fernández": "Enzo",
        "Nicolás Hernán Otamendi": "Otamendi",
        "Cristian Gabriel Romero": "Romero",
        "Nahuel Molina": "Molina",
        "Nicolás Alejandro Tagliafico": "Tagliafico",
        "Adrien Rabiot": "Rabiot",
        "Aurélien Djani Tchouaméni": "Tchouameni",
        "Dayotchanculle Oswald Upamecano": "Upamecano",
        "Raphaël Varane": "Varane",
        "Jules Olivier Koundé": "Kounde",
        "Théo Bernard François Hernández": "T. Hernandez",
        "Kingsley Coman": "Coman",
        "Marcus Thuram": "Thuram",
        "Randal Kolo Muani": "Kolo Muani",
        "Carles Puyol": "Puyol",
        "David Villa": "Villa",
        "Pedro Rodríguez": "Pedro",
        "Xavier Hernández": "Xavi",
        "Wayne Rooney": "Rooney",
        "Javier Hernández": "Chicharito",
        "Ryan Giggs": "Giggs",
        "Paul Scholes": "Scholes",
        "Michael Carrick": "Carrick",
        "Rio Ferdinand": "Ferdinand",
        "Nemanja Vidić": "Vidic",
        "Patrice Evra": "Evra",
        "Edwin van der Sar": "Van der Sar",
        "Gianluigi Buffon": "Buffon",
        "Andrea Pirlo": "Pirlo",
        "Paul Pogba": "Pogba",
        "Arturo Vidal": "Vidal",
        "Claudio Marchisio": "Marchisio",
        "Carlos Alberto Martínez Tévez": "Tevez",
        "Álvaro Borja Morata": "Morata",
        "Leonardo Bonucci": "Bonucci",
        "Giorgio Chiellini": "Chiellini",
        "Neymar da Silva Santos Júnior": "Neymar"
    }

    for s_id in all_slots:
        if s_id in slots:
            p_obj = slots[s_id]
            full_name = p_obj["player"]["name"]
            matched_name = None
            for star_k, star_v in KNOWN_STAR_NAMES.items():
                if star_k.lower() in full_name.lower():
                    matched_name = star_v
                    break
            short_name = matched_name or (full_name.split()[-1] if len(full_name.split()) > 1 else full_name)
            roster[s_id] = {
                "num": p_obj["jersey_number"],
                "name": short_name,
                "full_name": full_name,
                "player_id": p_obj["player"]["id"],
                "role": p_obj["position"]["name"]
            }
        else:
            roster[s_id] = {"num": int(s_id[1:]), "name": s_id, "full_name": s_id, "player_id": None, "role": "Player"}
    return roster

MATCH_DEFS = [
    {
        "id": "MATCH_EL_CLASICO_2017",
        "title": "⚽ Real Madrid 2 - 3 Barcelona (La Liga 2017 · Messi 92' Iconic Winner & Ramos Red)",
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
            "name": "Barcelona",
            "short": "BAR",
            "color": "#ef4444",
            "color_sec": "#2563eb",
            "badge": "BAR",
            "pattern": "blaugrana"
        },
        "home_gk": "Keylor Navas (RMA)",
        "away_gk": "Marc-André ter Stegen (BAR)"
    },
    {
        "id": "MATCH_WORLD_CUP_2022",
        "title": "🌍 Argentina 3 - 3 France (World Cup 2022 Final · Lusail Epic 120' & 12 Goals)",
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
        "away_gk": "Hugo Lloris (FRA)"
    },
    {
        "id": "MATCH_EL_CLASICO_5_0",
        "title": "⚡ Barcelona 5 - 0 Real Madrid (La Liga 2010 · Pep's Camp Nou Manita & 5 Goals)",
        "competition": "La Liga EA Sports · Camp Nou (FC Barcelona 5 - 0 Real Madrid)",
        "sb_url": "https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/69299.json",
        "home_team": {
            "name": "Barcelona",
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
        "away_gk": "Iker Casillas (RMA)"
    },
    {
        "id": "MATCH_UCL_WEMBLEY_2011",
        "title": "🏆 Barcelona 3 - 1 Manchester United (UCL Final 2011 · Wembley Masterclass)",
        "competition": "UEFA Champions League Final · Wembley Stadium London (3 - 1)",
        "sb_url": "https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/18236.json",
        "home_team": {
            "name": "Barcelona",
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
        "away_gk": "Edwin van der Sar (MUN)"
    },
    {
        "id": "MATCH_UCL_FINAL_2015",
        "title": "🏆 Juventus 1 - 3 Barcelona (UCL Final 2015 · Berlin Treble Triumph)",
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
            "name": "Barcelona",
            "short": "BAR",
            "color": "#ef4444",
            "color_sec": "#2563eb",
            "badge": "BAR",
            "pattern": "blaugrana"
        },
        "home_gk": "Gianluigi Buffon (JUV)",
        "away_gk": "Marc-André ter Stegen (BAR)"
    }
]

def build_smooth_match(m_def):
    print(f"Building smooth continuous match: {m_def['title']}")
    events = fetch_statsbomb(m_def["sb_url"])

    home_name = m_def["home_team"]["name"]
    away_name = m_def["away_team"]["name"]
    home_gk = m_def["home_gk"]
    away_gk = m_def["away_gk"]

    lineup_home = get_real_lineup(events, home_name)
    lineup_away = get_real_lineup(events, away_name)

    r_home = build_roster_from_lineup(lineup_home, True)
    r_away = build_roster_from_lineup(lineup_away, False)

    subs_map_home = {}
    subs_map_away = {}
    for ev in events:
        if ev.get("type", {}).get("name") == "Substitution":
            t_name = ev.get("team", {}).get("name")
            p_off = ev.get("player", {})
            p_on = ev.get("substitution", {}).get("replacement", {})
            target_map = subs_map_home if home_name in t_name else subs_map_away
            target_roster = r_home if home_name in t_name else r_away
            for slot, p_info in target_roster.items():
                if p_info.get("player_id") == p_off.get("id"):
                    target_map[p_on.get("id")] = slot
                    target_map[p_on.get("name")] = slot
                    break

    def resolve_slot(p_id, p_name, is_home):
        roster = r_home if is_home else r_away
        subs_map = subs_map_home if is_home else subs_map_away
        if p_id and p_id in subs_map:
            return subs_map[p_id]
        if p_name and p_name in subs_map:
            return subs_map[p_name]
        for slot, p_info in roster.items():
            if p_info.get("player_id") == p_id:
                return slot
        if p_name:
            p_low = p_name.lower()
            for slot, p_info in roster.items():
                if p_low in p_info.get("full_name", "").lower():
                    return slot
        return "H10" if is_home else "A11"

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

        if ev_type == 'Shot' and ev.get('shot', {}).get('outcome', {}).get('name') == 'Goal':
            shot = ev.get('shot', {})
            player_name = ev.get('player', {}).get('name', 'Unknown')
            p_id = ev.get('player', {}).get('id')
            shot_type = shot.get('type', {}).get('name', 'Open Play')

            assist_name = None
            assist_id = None
            prev_events = events[max(0, i-6):i]
            for pev in reversed(prev_events):
                if pev.get('type', {}).get('name') == 'Pass' and pev.get('team', {}).get('name') == t_name:
                    assist_name = pev.get('player', {}).get('name')
                    assist_id = pev.get('player', {}).get('id')
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

            shooter_slot = resolve_slot(p_id, player_name, is_home)
            assister_slot = resolve_slot(assist_id, assist_name, is_home) if assist_name else None

            # Shot start location on 105x68 pitch
            raw_loc = ev.get('location', [104.0, 40.0])
            if is_home:
                shot_start_x = round((raw_loc[0] / 120.0) * 105.0, 1)
                shot_start_y = round((raw_loc[1] / 80.0) * 68.0, 1)
            else:
                shot_start_x = round(((120.0 - raw_loc[0]) / 120.0) * 105.0, 1)
                shot_start_y = round(((80.0 - raw_loc[1]) / 80.0) * 68.0, 1)

            goals.append({
                "minute": minute,
                "second": second,
                "team": "Home" if is_home else "Away",
                "scorer": player_name,
                "scorer_slot": shooter_slot,
                "assist": assist_name or "Solo Individual Effort",
                "assist_slot": assister_slot,
                "type": f"{shot_type} ({h_zone})",
                "speed_kmh": speed,
                "goalkeeper": gk_facing,
                "shot_start": (shot_start_x, shot_start_y),
                "entry_x": target_goal_x,
                "entry_y": pitch_entry_y,
                "entry_z": pitch_entry_z,
                "zone_code": zone_code,
                "zone_label": h_zone,
                "score_after": [score_home, score_away]
            })

        if ev_type == 'Foul Committed' and ev.get('foul_committed', {}).get('card'):
            card_type = ev.get('foul_committed', {}).get('card', {}).get('name', 'Yellow Card')
            foul_player = ev.get('player', {}).get('name', 'Unknown')
            foul_p_id = ev.get('player', {}).get('id')

            fouled_player = "Opponent"
            fouled_p_id = None
            for rel_id in ev.get('related_events', []):
                for check_ev in events[max(0, i-4):min(len(events), i+5)]:
                    if check_ev.get('id') == rel_id and check_ev.get('type', {}).get('name') == 'Foul Won':
                        fouled_player = check_ev.get('player', {}).get('name', 'Opponent')
                        fouled_p_id = check_ev.get('player', {}).get('id')
                        break

            loc = ev.get('location', [60.0, 34.0])
            pitch_x = round((loc[0] / 120.0) * 105.0, 1)
            pitch_y = round((loc[1] / 80.0) * 68.0, 1)

            tackler_slot = resolve_slot(foul_p_id, foul_player, is_home)
            victim_slot = resolve_slot(fouled_p_id, fouled_player, not is_home)

            fouls.append({
                "minute": minute,
                "second": second,
                "team": "Home" if is_home else "Away",
                "tackler": foul_player,
                "tackler_slot": tackler_slot,
                "victim": fouled_player,
                "victim_slot": victim_slot,
                "card": card_type,
                "action": "Hard Sliding Tackle" if card_type == "Red Card" else "Tactical Foul / Trip",
                "loc": (pitch_x, pitch_y)
            })

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

    chapters = [{"min": 1, "label": "⏱ 01' Kick-Off", "desc": "Match Kick-Off & Tactical Circulation"}]
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
    chapters.append({"min": 45, "label": "🛡 45' Halftime", "desc": "Halftime Tactical Interval"})
    chapters.append({"min": 90, "label": "🏁 90' Full Time", "desc": "Whistle blows & Final Score"})
    chapters.sort(key=lambda c: c["min"])

    # SYNTHESIZE FULL SMOOTH CONTINUOUS MATCH PLAYS
    # Connect plays seamlessly without teleportation!
    plays = []
    last_pt = (52.5, 34.0)

    key_events = []
    for g in goals:
        key_events.append({"type": "GOAL", "data": g, "min": g["minute"], "sec": g["second"]})
    for f in fouls:
        key_events.append({"type": "FOUL", "data": f, "min": f["minute"], "sec": f["second"]})
    key_events.sort(key=lambda x: (x["min"], x["sec"]))

    cur_clock_min = 0
    cur_clock_sec = 0

    # Start with kickoff pass
    plays.append({
        "type": "PASS",
        "from_p": "H10",
        "to_p": "H6",
        "dur": 70,
        "start": (52.5, 34.0),
        "end": (42.0, 34.0),
        "t_start": (0, 0),
        "t_end": (0, 45)
    })
    last_pt = (42.0, 34.0)
    cur_clock_min = 0
    cur_clock_sec = 45

    for ev in key_events:
        target_min = ev["min"]
        target_sec = ev["sec"]

        if ev["type"] == "GOAL":
            g = ev["data"]
            is_h = (g["team"] == "Home")
            scorer_slot = g["scorer_slot"]
            assist_slot = g["assist_slot"] or ("H7" if is_h else "A9")
            shot_loc = g["shot_start"]
            goal_dest = (g["entry_x"], g["entry_y"])

            # 1. Approach dribble / pass towards shot location
            # Calculate dynamic duration: ensure player running at realistic pace (~23 km/h = 0.25 m/frame) has enough time to arrive
            dist_approach = math.hypot(shot_loc[0] - last_pt[0], shot_loc[1] - last_pt[1])
            approach_dur = max(90, int(dist_approach / 0.23) + 25)
            plays.append({
                "type": "PASS",
                "from_p": assist_slot,
                "to_p": scorer_slot,
                "dur": approach_dur,
                "start": last_pt,
                "end": shot_loc,
                "t_start": (max(0, target_min - 1), 30),
                "t_end": (target_min, max(0, target_sec - 10))
            })

            # 2. Scorer controls and takes high-speed shot!
            # Scorer is physically right at shot_loc touching the ball!
            plays.append({
                "type": "SHOT",
                "from_p": scorer_slot,
                "dur": 65,
                "start": shot_loc,
                "end": goal_dest,
                "h": g["entry_z"],
                "speed": g["speed_kmh"],
                "is_goal": True,
                "goal_data": g,
                "t_start": (target_min, max(0, target_sec - 10)),
                "t_end": (target_min, target_sec)
            })

            # 3. Goal Celebration
            corner_spot = (98.0, 16.0) if is_h else (12.0, 16.0)
            plays.append({
                "type": "CELEBRATION",
                "player": scorer_slot,
                "dur": 110,
                "start": goal_dest,
                "end": goal_dest,
                "scorer_pos": corner_spot,
                "t_start": (target_min, target_sec),
                "t_end": (min(90, target_min + 1), 30)
            })

            # 4. Restart Kick-off from center
            # Smooth ball pass from goal net to center circle
            dist_restart = math.hypot(52.5 - goal_dest[0], 34.0 - goal_dest[1])
            restart_dur = max(75, int(dist_restart / 0.55))
            plays.append({
                "type": "PASS",
                "from_p": "A1" if is_h else "H1",
                "to_p": "A11" if is_h else "H10",
                "dur": restart_dur,
                "start": goal_dest,
                "end": (52.5, 34.0),
                "t_start": (min(90, target_min + 1), 30),
                "t_end": (min(90, target_min + 2), 0)
            })
            last_pt = (52.5, 34.0)

        elif ev["type"] == "FOUL":
            f = ev["data"]
            f_loc = f["loc"]
            tackler_slot = f["tackler_slot"]
            victim_slot = f["victim_slot"]

            # 1. Build-up run into the tackle contest zone
            dist_foul = math.hypot(f_loc[0] - 2.5 - last_pt[0], f_loc[1] - 1.0 - last_pt[1])
            foul_buildup_dur = max(80, int(dist_foul / 0.23) + 20)
            plays.append({
                "type": "PASS",
                "from_p": victim_slot,
                "to_p": victim_slot,
                "dur": foul_buildup_dur,
                "start": last_pt,
                "end": (f_loc[0] - 2.5, f_loc[1] - 1.0),
                "t_start": (max(0, target_min - 1), 20),
                "t_end": (target_min, max(0, target_sec - 12))
            })

            # 2. Dramatic Sliding Tackle & Tumble Sequence (85 frames for ultra-fluid slide)
            plays.append({
                "type": "TACKLE",
                "tackler": tackler_slot,
                "victim": victim_slot,
                "dur": 85,
                "start": (f_loc[0] - 2.5, f_loc[1] - 1.0),
                "end": f_loc,
                "foul_data": f,
                "t_start": (target_min, max(0, target_sec - 12)),
                "t_end": (target_min, target_sec)
            })

            # 3. Free kick / possession continuation
            # Start exactly where the ball deflected to: (f_loc[0] + 3.2, f_loc[1] + 1.8)
            tackle_ball_end = (round(f_loc[0] + 3.2, 2), round(f_loc[1] + 1.8, 2))
            plays.append({
                "type": "DRIBBLE",
                "player": victim_slot,
                "dur": 60,
                "start": tackle_ball_end,
                "end": (tackle_ball_end[0] + 4.0, tackle_ball_end[1]),
                "t_start": (target_min, target_sec),
                "t_end": (min(90, target_min + 1), 0)
            })
            last_pt = (tackle_ball_end[0] + 4.0, tackle_ball_end[1])

    # Whistle sequence
    plays.append({
        "type": "PASS",
        "from_p": "H6",
        "to_p": "H1",
        "dur": 80,
        "start": last_pt,
        "end": (14.0, 34.0),
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

    # Generate Kinematic Frames with Real Formations & Continuity
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

    for f_idx in range(1, total_frames + 1):
        cur_item = next((item for item in timeline if item["start_frame"] <= f_idx <= item["end_frame"]), timeline[-1])
        play = cur_item["play"]
        p_start = cur_item["start_frame"]
        p_dur = cur_item["dur"]
        p_type = play["type"]

        u = max(0.0, min(1.0, (f_idx - p_start) / max(1, p_dur - 1)))
        x0, y0 = play["start"]
        x1, y1 = play["end"]

        # Kinematic Ball Coordinates
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
            if u < 0.35:
                # Ball with victim
                ua = u / 0.35
                bx = x0 + (x1 - x0) * ua
                by = y0 + (y1 - y0) * ua
                bz = 0.0
            else:
                # Loose ball deflects after tackle
                us = (u - 0.35) / 0.65
                bx = x1 + 3.2 * us
                by = y1 + 1.8 * us
                bz = math.sin(us * math.pi) * 0.4
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

        # 1. Update Home Players
        for pid, (base_x, base_y, role) in HOME_433_FORM.items():
            cur = p_pos[pid]
            is_scorer = (p_type == "CELEBRATION" and play.get("player") == pid)
            is_shooter = (p_type == "SHOT" and play.get("from_p") == pid)
            is_tackler = (p_type == "TACKLE" and play.get("tackler") == pid)
            is_victim = (p_type == "TACKLE" and play.get("victim") == pid)

            if is_scorer:
                tgt_x, tgt_y = play.get("scorer_pos", (96.0, 16.0))
            elif is_shooter:
                # Scorer is right behind ball during shot
                tgt_x = x0 + 0.5 * u
                tgt_y = y0 + 0.1 * u
            elif is_tackler:
                if u < 0.35:
                    # Closing down sprint
                    ua = u / 0.35
                    tgt_x = x0 + (x1 - x0) * (ua * 0.9)
                    tgt_y = y0 + (y1 - y0) * (ua * 0.9)
                elif u < 0.70:
                    # Sliding forward through impact point
                    us = (u - 0.35) / 0.35
                    tgt_x = x1 + 1.2 * us
                    tgt_y = y1 + 0.6 * us
                else:
                    tgt_x = x1 + 1.2
                    tgt_y = y1 + 0.6
            elif is_victim:
                if u < 0.35:
                    tgt_x = bx - 0.3
                    tgt_y = by
                elif u < 0.70:
                    us = (u - 0.35) / 0.35
                    tgt_x = x1 + 0.6 * us
                    tgt_y = y1 + 0.4 * us
                else:
                    tgt_x = x1 + 0.6
                    tgt_y = y1 + 0.4
            elif p_type == "DRIBBLE" and play.get("player") == pid:
                tgt_x = bx - 0.4
                tgt_y = by
            elif p_type == "PASS" and play.get("from_p") == pid and u < 0.25:
                tgt_x = x0 - 0.3
                tgt_y = y0
            elif p_type == "PASS" and play.get("to_p") == pid:
                tgt_x = x1 - 0.35
                tgt_y = y1
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
            dist = math.hypot(diff_x, diff_y)
            if dist > 0.001:
                is_urgent = is_shooter or (p_type == "PASS" and play.get("to_p") == pid) or is_tackler
                # Realistic human caps: urgent sprint <= 31.5 km/h (0.35m/frame), normal shifting <= 18.0 km/h (0.20m/frame)
                max_step_mag = 0.35 if is_urgent else 0.20
                gain = 0.16 if is_urgent else 0.08
                step_mag = min(dist * gain, max_step_mag)
                step_x = (diff_x / dist) * step_mag
                step_y = (diff_y / dist) * step_mag
                cur[0] += step_x
                cur[1] += step_y
                p_vx = round(step_x / dt, 2)
                p_vy = round(step_y / dt, 2)
            else:
                p_vx, p_vy = 0.0, 0.0

            r_info = r_home.get(pid, {"num": int(pid[1:]), "name": pid, "full_name": pid, "role": role})

            action_pose = "NORMAL"
            if is_tackler and 0.25 <= u <= 0.85:
                action_pose = "SLIDING_TACKLE"
            elif is_victim and 0.35 <= u <= 0.90:
                action_pose = "FOUL_FALL"
            elif is_shooter and u < 0.30:
                action_pose = "SHOOTING_KICK"

            players.append({
                "id": pid,
                "team": "Home",
                "num": r_info["num"],
                "name": r_info["name"],
                "full_name": r_info.get("full_name", r_info["name"]),
                "role": r_info["role"],
                "x": round(cur[0], 2),
                "y": round(cur[1], 2),
                "z": 0.0,
                "vx": p_vx,
                "vy": p_vy,
                "action": action_pose
            })

        # 2. Update Away Players
        for pid, (base_x, base_y, role) in AWAY_4231_FORM.items():
            cur = p_pos[pid]
            is_scorer = (p_type == "CELEBRATION" and play.get("player") == pid)
            is_shooter = (p_type == "SHOT" and play.get("from_p") == pid)
            is_tackler = (p_type == "TACKLE" and play.get("tackler") == pid)
            is_victim = (p_type == "TACKLE" and play.get("victim") == pid)

            if is_scorer:
                tgt_x, tgt_y = play.get("scorer_pos", (12.0, 16.0))
            elif is_shooter:
                tgt_x = x0 - 0.5 * u
                tgt_y = y0 + 0.1 * u
            elif is_tackler:
                if u < 0.35:
                    ua = u / 0.35
                    tgt_x = x0 + (x1 - x0) * (ua * 0.9)
                    tgt_y = y0 + (y1 - y0) * (ua * 0.9)
                elif u < 0.70:
                    us = (u - 0.35) / 0.35
                    tgt_x = x1 - 1.2 * us
                    tgt_y = y1 + 0.6 * us
                else:
                    tgt_x = x1 - 1.2
                    tgt_y = y1 + 0.6
            elif is_victim:
                if u < 0.35:
                    tgt_x = bx + 0.3
                    tgt_y = by
                elif u < 0.70:
                    us = (u - 0.35) / 0.35
                    tgt_x = x1 - 0.6 * us
                    tgt_y = y1 + 0.4 * us
                else:
                    tgt_x = x1 - 0.6
                    tgt_y = y1 + 0.4
            elif p_type == "DRIBBLE" and play.get("player") == pid:
                tgt_x = bx + 0.4
                tgt_y = by
            elif p_type == "PASS" and play.get("from_p") == pid and u < 0.25:
                tgt_x = x0 + 0.3
                tgt_y = y0
            elif p_type == "PASS" and play.get("to_p") == pid:
                tgt_x = x1 + 0.35
                tgt_y = y1
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
            dist = math.hypot(diff_x, diff_y)
            if dist > 0.001:
                is_urgent = is_shooter or (p_type == "PASS" and play.get("to_p") == pid) or is_tackler
                # Realistic human caps: urgent sprint <= 31.5 km/h (0.35m/frame), normal shifting <= 18.0 km/h (0.20m/frame)
                max_step_mag = 0.35 if is_urgent else 0.20
                gain = 0.16 if is_urgent else 0.08
                step_mag = min(dist * gain, max_step_mag)
                step_x = (diff_x / dist) * step_mag
                step_y = (diff_y / dist) * step_mag
                cur[0] += step_x
                cur[1] += step_y
                p_vx = round(step_x / dt, 2)
                p_vy = round(step_y / dt, 2)
            else:
                p_vx, p_vy = 0.0, 0.0

            r_info = r_away.get(pid, {"num": int(pid[1:]), "name": pid, "full_name": pid, "role": role})

            action_pose = "NORMAL"
            if is_tackler and 0.25 <= u <= 0.85:
                action_pose = "SLIDING_TACKLE"
            elif is_victim and 0.35 <= u <= 0.90:
                action_pose = "FOUL_FALL"
            elif is_shooter and u < 0.30:
                action_pose = "SHOOTING_KICK"

            players.append({
                "id": pid,
                "team": "Away",
                "num": r_info["num"],
                "name": r_info["name"],
                "full_name": r_info.get("full_name", r_info["name"]),
                "role": r_info["role"],
                "x": round(cur[0], 2),
                "y": round(cur[1], 2),
                "z": 0.0,
                "vx": p_vx,
                "vy": p_vy,
                "action": action_pose
            })

        # Anti-stacking repulsion pass: prevent players from merging into each other
        for pi in range(len(players)):
            for pj in range(pi + 1, len(players)):
                p1, p2 = players[pi], players[pj]
                # Allow close contact only during sliding tackle/tumble contest
                if p1.get("action") in ("SLIDING_TACKLE", "FOUL_FALL") or p2.get("action") in ("SLIDING_TACKLE", "FOUL_FALL"):
                    continue
                d_ij = math.hypot(p2["x"] - p1["x"], p2["y"] - p1["y"])
                if d_ij < 0.85:
                    overlap = 0.85 - d_ij
                    push = overlap * 0.5
                    if d_ij > 0.001:
                        nx = (p2["x"] - p1["x"]) / d_ij
                        ny = (p2["y"] - p1["y"]) / d_ij
                    else:
                        nx, ny = 1.0, 0.0
                    p1["x"] = round(p1["x"] - nx * push, 2)
                    p1["y"] = round(p1["y"] - ny * push, 2)
                    p2["x"] = round(p2["x"] + nx * push, 2)
                    p2["y"] = round(p2["y"] + ny * push, 2)
                    # Update local state cache
                    p_pos[p1["id"]][0] = p1["x"]
                    p_pos[p1["id"]][1] = p1["y"]
                    p_pos[p2["id"]][0] = p2["x"]
                    p_pos[p2["id"]][1] = p2["y"]

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
    for m_def in MATCH_DEFS:
        match_data = build_smooth_match(m_def)
        fname = f"data/{m_def['id'].lower()}.json"
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(match_data, f, indent=2)
        print(f"Generated {fname}: {len(match_data['frames'])} frames, {len(match_data['metadata']['goals'])} goals, {len(match_data['metadata']['fouls'])} fouls.")

    with open("data/match_el_clasico_2017.json", "r", encoding="utf-8") as f:
        clasico_17 = json.load(f)
    with open("data/sample_match_tracking.json", "w", encoding="utf-8") as f:
        json.dump(clasico_17, f, indent=2)
    with open("data/match_el_clasico.json", "w", encoding="utf-8") as f:
        json.dump(clasico_17, f, indent=2)
    print("All match datasets rebuilt with 100% physically continuous kinematics!")

if __name__ == "__main__":
    build_all()
