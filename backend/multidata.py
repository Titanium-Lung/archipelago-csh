"""
This file handles the getting of data relevant to the multiworld and giving it to app.py
"""

import os
import zlib
from datetime import datetime
from Utils import restricted_loads # type: ignore
from app import ServerState

"""
Returns all of the players in the multiworld and relevant info
Info including slot id, name, game, and also matches them to any patch file 
"""
def get_players(state: ServerState):
    with open(state.arch_file_path, "rb") as f:
        data = f.read()
    
    decoded = restricted_loads(zlib.decompress(data[1:]))

    players = [
        {"slot": slot_id, "name": info.name, "game": info.game}
        for slot_id, info, in decoded["slot_info"].items()
    ]

    with os.scandir(state.extract_folder_path) as folder:
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
def multitracker_data(state: ServerState):
    with open(state.arch_file_path, "rb") as f:
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

    with os.scandir(state.extract_folder_path) as folder:
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
                                elif player["name"] in state.released_games: 
                                    player["status"] = 40 # I made this up; it's for released games
                            else:
                                if player["name"] in state.released_games:
                                    player["status"] = 40
                                else:
                                    player["status"] = 0
                        
                        for player in decoded_apsave["hints"]: # player is (team#, slot#)
                            for hint_info in decoded_apsave["hints"][player]:
                                slot = player[1]
                                if hint_info.finding_player == slot: # no double ups. Must be finding player because location_info is keyed by location
                                    hint = {}
                                    hint["location"] = state.location_info[slot][hint_info.location]["location_name"]
                                    hint["receiving_player"] = state.location_info[slot][hint_info.location]["to"]
                                    hint["finding_player"] = state.location_info[slot][hint_info.location]["from"]
                                    hint["item"] = state.location_info[slot][hint_info.location]["item_name"]
                                    hint["game"] = state.location_info[slot][hint_info.location]["game"]
                                    if hint_info.entrance.strip():
                                        hint["entrance"] = hint_info.entrance
                                    else:
                                        hint["entrance"] = "Vanilla"
                                    hint["found"] = hint_info.found

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
                player["last_activity_num"] = 2147483647
                player["status"] = 0
                player["percent_checked"] = 0
    
    totals: dict = {"total_checks": total_checks, "total_checked": total_checked, "games_complete": games_complete, "num_players": len(players), "num_players_not_released": len(players)-len(state.released_games), "recent_activity": recent_activity}

    return players, totals, hints

"""
Gets received items, locations, and hints for one player
TODO Precollected items
"""
def individual_player_data(state: ServerState, slot: int):
    with open(state.arch_file_path, "rb") as f:
        data = f.read()
    
    decoded_arch = restricted_loads(zlib.decompress(data[1:]))
    
    items: dict = {} # dict for add or update
    locations: list = []
    hints: list = []

    # Get all the locations ahead of time no matter whether there's an apsave
    for location_num in decoded_arch["locations"][slot]:
        location = {}
        location["name"] = state.location_info[slot][location_num]["location_name"]
        location["checked"] = False
        location["number"] = location_num
        locations.append(location)

    with os.scandir(state.extract_folder_path) as folder:
        # Scan uploaded folder for apsave
        for file in folder:
            if file.is_file():
                if file.name.endswith(".apsave"):
                    with open(file.path, "rb") as f:
                        decoded_apsave = restricted_loads(zlib.decompress(f.read()))

                        count = 1 # Tracks order of received items
                        if (0, slot, True) in decoded_apsave["received_items"]: # (0, slot, True) is format of received_items dict in the apsave
                            for item_info in decoded_apsave["received_items"][(0, slot, True)]: # hard codes team number to 0
                                item_name = state.ids[state.slotinfos[slot].game]["id_to_item_name"][item_info.item]
                                # Add or Update
                                if item_name in items:
                                    items[item_name]["count"] += 1
                                else:
                                    items[item_name] = {}
                                    items[item_name]["count"] = 1
                                items[item_name]["last_order_received"] = count
                                count+=1
                        
                        for location in locations:
                            if (0, slot) in decoded_apsave["location_checks"]:
                                if location["number"] in decoded_apsave["location_checks"][(0, slot)]:
                                    location["checked"] = True
                                else:
                                    location["checked"] = False
                            else:
                                location["checked"] = False
                        
                        if (0, slot) in decoded_apsave["hints"]:
                            for hint_info in decoded_apsave["hints"][(0, slot)]: # Hard codes team to 0
                                receiving_slot = hint_info.finding_player
                                hint = {}
                                hint["location"] = state.location_info[receiving_slot][hint_info.location]["location_name"]
                                hint["receiving_player"] = state.location_info[receiving_slot][hint_info.location]["to"]
                                hint["finding_player"] = state.location_info[receiving_slot][hint_info.location]["from"]
                                hint["item"] = state.location_info[receiving_slot][hint_info.location]["item_name"]
                                hint["game"] = state.location_info[receiving_slot][hint_info.location]["game"]

                                if hint_info.entrance.strip():
                                    hint["entrance"] = hint_info.entrance
                                else:
                                    hint["entrance"] = "Vanilla"
                                hint["found"] = hint_info.found

                                hints.append(hint)
    
    return items, locations, hints

"""
Gets the info of every item received by all players 
"""
def sphere_data(state: ServerState):
    items: list = []

    with os.scandir(state.extract_folder_path) as folder:
        # Scans upload folder for apsave
        for file in folder:
            if file.is_file():
                if file.name.endswith(".apsave"):
                    with open(file.path, "rb") as f:
                        decoded_apsave = restricted_loads(zlib.decompress(f.read()))

                        for key in decoded_apsave["location_checks"]: # key is (team#, slotid) tuple
                            for location_id in decoded_apsave["location_checks"][key]:
                                item = state.location_info[key[1]][location_id] # location_info dict has all relevant data already
                                items.append(item)
    
    return items