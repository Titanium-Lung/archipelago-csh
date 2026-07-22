"""
This file handles the getting of data relevant to the multiworld and giving it to app.py
"""

import os
import zlib
from datetime import datetime
from Utils import restricted_loads # type: ignore

"""
Returns all of the players in the multiworld and relevant info
Info including slot id, name, game, and also matches them to any patch file 
"""
def get_players(arch_file_path, extract_folder_path):
    with open(arch_file_path, "rb") as f:
        data = f.read()
    
    decoded = restricted_loads(zlib.decompress(data[1:]))

    players = [
        {"slot": slot_id, "name": info.name, "game": info.game}
        for slot_id, info, in decoded["slot_info"].items()
    ]

    with os.scandir(extract_folder_path) as folder:
        for file in folder:
            if file.is_file():
                if "P" in file.name[2:]:
                    try:
                        # Looks for the structure of the name of the patch file (not perfect)
                        first = file.name.index("P")
                        second = file.name.index("P", first+1)
                        end = file.name.index('_', second+1)
                    
                        patch_id = int(file.name[second+1:end])
                        for player in players:
                            if player['slot'] == patch_id:
                                player['patch'] = file.name

                    except ValueError:
                        continue
    
    return players

"""
Gets the data for each player in the multiworld 
Data includes slot id, name, game, checks gotten, total checks, and last activity (most recent check)
Also gets all hints
"""
def multitracker_data(arch_file_path, extract_folder_path, released_games, conn, room_id):
    with open(arch_file_path, "rb") as f:
        data = f.read()
    
    decoded_arch = restricted_loads(zlib.decompress(data[1:]))

    players: list = [
        {"slot": slot_id, "name": info.name, "game": info.game}
        for slot_id, info, in decoded_arch["slot_info"].items()
    ]

    hints: list = []

    # Totals 
    total_checks = 0
    total_checked = 0
    games_complete = 0
    recent_activity = "None"
    recent_activity_dt = (datetime.now() - datetime.fromtimestamp(0)) # timedelta object

    with os.scandir(extract_folder_path) as folder:
        apsave = False
        # Scans uploaded folder for apsave
        for file in folder:
            if file.is_file():
                if file.name.endswith(".apsave"):
                    with open(file.path, "rb") as f:
                        decoded_apsave = restricted_loads(zlib.decompress(f.read()))

                        # with open("sample ap files/sample_apsave.txt", "w") as f:
                        #     f.write(str(decoded_apsave))

                        player_activity = {}
                        for activity in decoded_apsave["client_activity_timers"]:
                            player_activity[activity[0]] = activity[1]

                        for player in players:
                            checks = len(decoded_arch["locations"][player["slot"]])
                            player["total_checks"] = checks
                            total_checks += checks

                            player_tuple = decoded_arch["connect_names"][player["name"]] # Gives in format of (team#, slot#)

                            location_checks = decoded_apsave["location_checks"]
                            checked = len(location_checks.get(player_tuple, set())) # Player won't be present in location_checks dict if they haven't gotten any locations
                            player["checks_found"] = checked
                            total_checked += checked

                            player["percent_checked"] = checked/checks*100

                            # Calculate last activity (check) if it exists 
                            if player_tuple in player_activity:
                                timediff = (datetime.now() - datetime.fromtimestamp(player_activity[player_tuple]))
                                total_seconds = int(timediff.total_seconds())
                                hours = total_seconds // 3600
                                minutes = (total_seconds % 3600) // 60

                                player["last_activity"] = f"{hours:02}:{minutes:02}"
                                player["last_activity_num"] = total_seconds

                                if recent_activity_dt > timediff:
                                    recent_activity = f"{hours:02}:{minutes:02}"
                                    recent_activity_dt = timediff
                            else:
                                player["last_activity"] = "None"
                                player["last_activity_num"] = 2147483647 # large number 
                            
                            if player_tuple in decoded_apsave["client_game_state"]:
                                player["status"] = decoded_apsave["client_game_state"][player_tuple]
                                if player["status"] == 30: # 30 means completed
                                    games_complete += 1
                                elif player["name"].lower() in released_games: 
                                    player["status"] = 25 # I made this up; it's for released games
                            else:
                                if player["name"].lower() in released_games:
                                    player["status"] = 25
                                else:
                                    player["status"] = 0
                        
                        slot_hints = ([], [])
                        for player in decoded_apsave["hints"]: # player is (team#, slot#)
                            slot = player[1]
                            for hint_info in decoded_apsave["hints"][player]:
                                if hint_info.finding_player == slot: # no double ups
                                    slot_hints[0].append((room_id, int(slot), str(hint_info.location)))
                                    slot_hints[1].append((hint_info.entrance, hint_info.found, str(hint_info.location)))
                        
                        # Database doesn't store entrance or found
                        extra_hint_info = slot_hints[1]

                        with conn.cursor() as cur:
                            cur.executemany("""SELECT location_name, to_name, from_name, item_name, game, location_id FROM locations 
                                        WHERE room_id = %s AND slot = %s AND location_id = %s""", slot_hints[0], returning=True)
                            loc_infos = []
                            loc_len = 0
                            for result in cur.results():
                                loc_infos.append(cur.fetchone())
                                loc_len+=1

                            for index in range(loc_len):
                                loc_info = loc_infos[index]
                                hint_info = extra_hint_info[index]

                                hint = {}
                                hint["location"] = loc_info[0]
                                hint["receiving_player"] = loc_info[1]
                                hint["finding_player"] = loc_info[2]
                                hint["item"] = loc_info[3]
                                hint["game"] = loc_info[4]
                                if hint_info[0].strip():
                                    hint["entrance"] = hint_info[0]
                                else:
                                    hint["entrance"] = "Vanilla"
                                hint["found"] = hint_info[1]

                                hints.append(hint)
                        
                        apsave = True

        # if there is no apsave
        if not apsave: 
            for player in players:
                checks = len(decoded_arch["locations"][player["slot"]])
                player["total_checks"] = checks
                total_checks += checks

                player["checks_found"] = 0
                player["last_activity"] = "None"
                player["last_activity_num"] = 2147483647 # Arbitrarily large number
                player["status"] = 0
                player["percent_checked"] = 0
    
    totals: dict = {"total_checks": total_checks, 
                    "total_checked": total_checked, 
                    "games_complete": games_complete, 
                    "num_players": len(players), 
                    "num_players_not_released": len(players)-len(released_games), 
                    "recent_activity": recent_activity}

    return players, totals, hints

"""
Gets received items, locations, and hints for one player
"""
def individual_player_data(extract_folder_path, arch_file_path, room_id, slot: int, conn):
    with open(arch_file_path, "rb") as f:
        data = f.read()
    
    decoded_arch = restricted_loads(zlib.decompress(data[1:]))
    
    items: dict = {} # dict for add or update
    locations: list = []
    hints: list = []
    name: str = ""

    with conn.cursor() as cur:
        # Get all the locations ahead of time no matter whether there's an apsave
        cur.execute("SELECT location_name, location_id FROM locations WHERE room_id = %s AND slot = %s", (room_id, slot))
        locations_db = cur.fetchall()

        for location_info in locations_db:
            location = {}
            location["name"] = location_info[0]
            location["checked"] = False
            location["number"] = location_info[1]
            locations.append(location)

        cur.execute("""SELECT i.id, i.name, s.name FROM items as i, slots as s
                    WHERE i.room_id = %s AND s.room_id = i.room_id AND s.id = %s AND i.game = s.game""", (room_id, slot))
        items_db = cur.fetchall()
        item_infos = {}
        for item_info in items_db:
            item_infos[item_info[0]] = {}
            item_infos[item_info[0]]['name'] = item_info[1]
            name = item_info[2]

        count = 1 # Tracks order of received items
        for item in decoded_arch["precollected_items"][slot]:
            item_name = item_infos[str(item)]['name']
            # Add or Update
            if item_name in items:
                items[item_name]["count"] += 1
            else:
                items[item_name] = {}
                items[item_name]["count"] = 1
            items[item_name]["last_order_received"] = count
            count+=1

        with os.scandir(extract_folder_path) as folder:
            # Scan uploaded folder for apsave
            for file in folder:
                if file.is_file():
                    if file.name.endswith(".apsave"):
                        with open(file.path, "rb") as f:
                            decoded_apsave = restricted_loads(zlib.decompress(f.read()))

                            if (0, slot, True) in decoded_apsave["received_items"]: # (0, slot, True) is format of received_items dict in the apsave
                                for item_info in decoded_apsave["received_items"][(0, slot, True)]: # item_info has .item, .location, .player (all ids) (and also .flags)
                                    item_name = item_infos[str(item_info.item)]['name']
                                    
                                    if item_name in items:
                                        items[item_name]["count"] += 1
                                    else:
                                        items[item_name] = {}
                                        items[item_name]["count"] = 1
                                    items[item_name]["last_order_received"] = count
                                    count+=1
                            
                            for location in locations:
                                if (0, slot) in decoded_apsave["location_checks"]:
                                    if int(location["number"]) in decoded_apsave["location_checks"][(0, slot)]:
                                        location["checked"] = True
                                    else:
                                        location["checked"] = False
                                else:
                                    location["checked"] = False
                            
                            if (0, slot) in decoded_apsave["hints"]:
                                slot_hints = ([], [])
                                for hint_info in decoded_apsave["hints"][(0, slot)]: # Hard codes team to 0
                                    slot_hints[0].append((room_id, int(hint_info.finding_player), str(hint_info.location)))
                                    slot_hints[1].append((hint_info.entrance, hint_info.found, str(hint_info.location)))

                                # Database doesn't store entrance or found
                                extra_hint_info = slot_hints[1]

                                cur.executemany("""SELECT location_name, to_name, from_name, item_name, game, location_id FROM locations 
                                    WHERE room_id = %s AND slot = %s AND location_id = %s""", slot_hints[0], returning=True)
                                loc_infos = []
                                loc_len = 0
                                for result in cur.results():
                                    loc_infos.append(cur.fetchone())
                                    loc_len+=1

                                for index in range(loc_len):
                                    loc_info = loc_infos[index]
                                    hint_info = extra_hint_info[index]
                                
                                    hint = {}
                                    hint["location"] = loc_info[0]
                                    hint["receiving_player"] = loc_info[1]
                                    hint["finding_player"] = loc_info[2]
                                    hint["item"] = loc_info[3]
                                    hint["game"] = loc_info[4]
                                    if hint_info[0].strip():
                                        hint["entrance"] = hint_info[0]
                                    else:
                                        hint["entrance"] = "Vanilla"
                                    hint["found"] = hint_info[1]

                                    hints.append(hint)
        
        return items, locations, hints, name

"""
Gets the info of every item received by all players 
"""
def sphere_data(extract_folder_path, conn, room_id):
    items: list = []

    with os.scandir(extract_folder_path) as folder:
        # Scans upload folder for apsave
        for file in folder:
            if file.is_file():
                if file.name.endswith(".apsave"):
                    with open(file.path, "rb") as f:
                        decoded_apsave = restricted_loads(zlib.decompress(f.read()))

                        location_checks = []
                        for player in decoded_apsave["location_checks"]: # player is (team#, slotid) tuple
                            for location_id in decoded_apsave["location_checks"][player]:
                                location_checks.append((room_id, int(player[1]), str(location_id)))

                        with conn.cursor() as cur:
                            cur.executemany("""SELECT sphere, from_name, to_name, location_name, item_name, game 
                                            FROM locations WHERE room_id=%s AND slot=%s AND location_id = %s""", location_checks, returning=True)
                            loc_infos = [cur.fetchone() for _ in cur.results()]

                            for loc_info in loc_infos:
                                item = {}
                                item['sphere'] = loc_info[0]
                                item['from'] = loc_info[1]
                                item['to'] = loc_info[2]
                                item['location_name'] = loc_info[3]
                                item['item_name'] = loc_info[4]
                                item['game'] = loc_info[5]

                                items.append(item)
    
    return items