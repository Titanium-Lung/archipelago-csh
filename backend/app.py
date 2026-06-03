from flask import Flask, request, jsonify, abort, send_file
from flask_cors import CORS
import os
import subprocess
import atexit
import threading
import sys
import zlib
import zipfile
from datetime import datetime
sys.path.insert(0, "Archipelago-0.6.7")
from Utils import restricted_loads

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

UPLOAD_FOLDER = "uploads"
ARCHIPELAGO_SERVER = "Archipelago-0.6.7/MultiServer.py"
SERVER_PORT = 38281

running_process = None
extract_folder_path = None
arch_file_path = None
location_info = {}
ids = {}
slotinfos = {}

@app.route("/upload", methods=["POST"])
def upload_file():
    global running_process
    global arch_file_path
    global extract_folder_path
    global location_info
    global ids

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if not file.filename.endswith(".zip"):
        return jsonify({"error": "File must be a .zip file"}), 400

    zip_save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(zip_save_path)

    extract_folder_path = zip_save_path[:zip_save_path.index('.')]

    filename = None

    with zipfile.ZipFile(zip_save_path) as zf:
        for name in zf.namelist():
            if name.endswith(".archipelago"):
                filename = name

        zf.extractall(path=extract_folder_path)
        os.remove(zip_save_path)
    
    if filename is None:
        return jsonify({"error": "No archipelago file found in zip"}), 400

    arch_file_path = os.path.join(extract_folder_path, filename)

    with open(arch_file_path, "rb") as f:
        data = f.read()
        decoded_arch = restricted_loads(zlib.decompress(data[1:]))

        ids = {}
        for game in decoded_arch["datapackage"]:
            subdict = decoded_arch["datapackage"][game]
            ids[game] = {}
            ids[game]['id_to_item_name'] = {v: k for k, v in subdict['item_name_to_id'].items()}
            ids[game]['id_to_location_name'] = {v: k for k, v in subdict['location_name_to_id'].items()}
        
        sphere_num = 1
        for sphere in decoded_arch["spheres"]:
            for slot in sphere:
                slotinfo = decoded_arch["slot_info"][slot]
                slotinfos[slot] = slotinfo
                for location_id in sphere[slot]:
                    location_info[location_id] = {}

                    location_info[location_id]["sphere"] = sphere_num
                    location_info[location_id]["from"] = slotinfo.name
                    location_info[location_id]["game"] = slotinfo.game

                    location_tuple = decoded_arch["locations"][slot][location_id] # format is: (item_id, receiver_slot_id, unknown#)
                    location_info[location_id]["to"] = decoded_arch["slot_info"][location_tuple[1]].name
                    location_info[location_id]["location_name"] = ids[slotinfo.game]['id_to_location_name'][location_id]
                    location_info[location_id]["item_name"] = ids[decoded_arch["slot_info"][location_tuple[1]].game]['id_to_item_name'][location_tuple[0]]
            sphere_num+=1

    if running_process is not None:
        running_process.terminate()
    
    running_process = subprocess.Popen(
        ["Archipelago-0.6.7/venv/bin/python3", ARCHIPELAGO_SERVER, arch_file_path, f"--port={SERVER_PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
    )

    thread = threading.Thread(target=write_log, args=(running_process, "logs/serverlog.txt"))
    thread.daemon = True
    thread.start()

    result = {
        "message": "Server started",
        "filename": file.filename,
        "port": SERVER_PORT
    }

    return jsonify(result)

@app.route("/restart")
def restart_server():
    pass

@app.route("/log")
def stream_log():
    if running_process is None: 
        return

    f = open("logs/serverlog.txt", "r")
    
    result = { 
        "lines": f.readlines()
    }

    return jsonify(result)

@app.route("/room")
def room_info():
    if running_process is None:
        abort(404)
    else:
        return jsonify({
            "port": SERVER_PORT
        })
    
@app.route("/command", methods=["POST"])
def server_command():
    if running_process is None:
        abort(404)
    else:
        data = request.get_json()
        running_process.stdin.write((data.get('command') + '\n').encode())
        running_process.stdin.flush()
        return jsonify({"message":"ok"})
    
@app.route("/players")
def get_players():
    if running_process is None:
        return jsonify({"error": "No archipelago server running"}), 404
    
    if arch_file_path is None:
        return jsonify({"error": "No file uploaded"}), 404

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
                    first = file.name.index("P")
                    second = file.name.index("P", first+1)
                    end = file.name.index('_', second+1)

                    try:
                        patch_id = int(file.name[second+1:end])
                        for player in players:
                            if player['slot'] == patch_id:
                                player['patch'] = file.name

                    except ValueError:
                        continue

    return jsonify({"players": players})

@app.route("/players/<filename>")
def send_patch_file(filename):
    if running_process is None:
        return jsonify({"error": "No archipelago server running"}), 404
    
    filepath = os.path.join(extract_folder_path, filename)

    return send_file(filepath)

@app.route("/tracker")
def multiworld_data():
    if running_process is None:
        return jsonify({"error": "No archipelago server running"}), 404
    
    if arch_file_path is None:
        return jsonify({"error": "No file uploaded"}), 404

    with open(arch_file_path, "rb") as f:
        data = f.read()
    
    decoded_arch = restricted_loads(zlib.decompress(data[1:]))

    players = [
        {"slot": slot_id, "name": info.name, "game": info.game}
        for slot_id, info, in decoded_arch["slot_info"].items()
    ]

    hints = []

    total_checks = 0
    total_checked = 0
    games_complete = 0
    recent_activity = "None"
    recent_activity_dt = (datetime.now() - datetime.fromtimestamp(0))

    with os.scandir(extract_folder_path) as folder:
        apsave = False
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

                            location_checks = decoded_apsave.get("location_checks", {})
                            checked = len(location_checks.get(player_tuple, set()))
                            player["checks_found"] = checked
                            total_checked += checked

                            player["percent_checked"] = checked/checks

                            if player_tuple in player_activity:
                                timediff = (datetime.now() - datetime.fromtimestamp(player_activity[player_tuple]))
                                total_seconds = int(timediff.total_seconds())
                                hours = total_seconds // 3600
                                minutes = (total_seconds % 3600) // 60
                                seconds = total_seconds % 60

                                player["last_activity"] = f"{hours:02}:{minutes:02}:{seconds:02}"
                                player["last_activity_num"] = total_seconds

                                if recent_activity_dt > timediff:
                                    recent_activity = f"{hours:02}:{minutes:02}:{seconds:02}"
                                    recent_activity_dt = timediff
                            else:
                                player["last_activity"] = "None"
                                player["last_activity_num"] = 2147483647
                            
                            if player_tuple in decoded_apsave["client_game_state"]:
                                player["status"] = decoded_apsave["client_game_state"][player_tuple]
                                if player["status"] == 30:
                                    games_complete += 1
                            else:
                                player["status"] = 0
                        
                        for player in decoded_apsave["hints"]:
                            for hint_info in decoded_apsave["hints"][player]:
                                if hint_info.receiving_player == player[1]:
                                    hint = {}
                                    hint["location"] = location_info[hint_info.location]["location_name"]
                                    hint["receiving_player"] = location_info[hint_info.location]["to"]
                                    hint["finding_player"] = location_info[hint_info.location]["from"]
                                    hint["item"] = location_info[hint_info.location]["item_name"]
                                    hint["game"] = location_info[hint_info.location]["game"]
                                    if hint_info.entrance.strip():
                                        hint["entrance"] = hint_info.entrance
                                    else:
                                        hint["entrance"] = "Vanilla"
                                    hint["found"] = hint_info.found

                                    hints.append(hint)
                        
                        apsave = True
        
        if not apsave:
            for player in players:
                checks = len(decoded_arch["locations"][player["slot"]])
                player["total_checks"] = checks
                total_checks += checks

                player["checks_found"] = 0
                player["last_activity"] = "None"
                player["last_activity_num"] = 2147483647
                player["status"] = 0
    
    totals = {"total_checks": total_checks, "total_checked": total_checked, "games_complete": games_complete, "num_players": len(players), "recent_activity": recent_activity}

    return jsonify({"players": players, "totals": totals, "hints": hints})

@app.route("/tracker/<int:slot>")
def individual_tracker_data(slot):
    if running_process is None:
        return jsonify({"error": "No archipelago server running"}), 404

    if arch_file_path is None:
        return jsonify({"error": "No file uploaded"}), 404

    with open(arch_file_path, "rb") as f:
        data = f.read()
    
    decoded_arch = restricted_loads(zlib.decompress(data[1:]))
    
    items = {}
    locations = []
    hints = []
    with os.scandir(extract_folder_path) as folder:
        for file in folder:
            if file.is_file():
                if file.name.endswith(".apsave"):
                    with open(file.path, "rb") as f:
                        decoded_apsave = restricted_loads(zlib.decompress(f.read()))

                        count = 1
                        if (0, slot, True) in decoded_apsave["received_items"]:
                            for item_info in decoded_apsave["received_items"][(0, slot, True)]: # hard codes team number to 0
                                item_name = ids[slotinfos[slot].game]["id_to_item_name"][item_info.item]
                                if item_name in items:
                                    items[item_name]["count"] += 1
                                else:
                                    items[item_name] = {}
                                    items[item_name]["count"] = 1
                                items[item_name]["last_order_received"] = count
                                count+=1
                        
                        for location_num in decoded_arch["locations"][slot]:
                            location = {}
                            location["name"] = location_info[location_num]["location_name"]
                            if (0, slot) in decoded_apsave["location_checks"]:
                                if location_num in decoded_apsave["location_checks"][(0, slot)]:
                                    location["checked"] = True
                                else:
                                    location["checked"] = False
                            else:
                                location["checked"] = False
                            locations.append(location)
                        
                        if (0, slot) in decoded_apsave["hints"]:
                            for hint_info in decoded_apsave["hints"][(0, slot)]: # Hard codes team to 0
                                hint = {}
                                hint["location"] = location_info[hint_info.location]["location_name"]
                                hint["receiving_player"] = location_info[hint_info.location]["to"]
                                hint["finding_player"] = location_info[hint_info.location]["from"]
                                hint["item"] = location_info[hint_info.location]["item_name"]
                                hint["game"] = location_info[hint_info.location]["game"]
                                if hint_info.entrance.strip():
                                    hint["entrance"] = hint_info.entrance
                                else:
                                    hint["entrance"] = "Vanilla"
                                hint["found"] = hint_info.found

                                hints.append(hint)
    
    return jsonify({"items": items, "locations": locations, "hints": hints})

@app.route("/spheres")
def sphere_items():
    if running_process is None:
        return jsonify({"error": "No archipelago server running"}), 404
    
    items = []
    with os.scandir(extract_folder_path) as folder:
        for file in folder:
            if file.is_file():
                if file.name.endswith(".apsave"):
                    with open(file.path, "rb") as f:
                        decoded_apsave = restricted_loads(zlib.decompress(f.read()))

                        for key in decoded_apsave["location_checks"]: # key is (team#, slotid) tuple
                            for location_id in decoded_apsave["location_checks"][key]:
                                item = location_info[location_id]
                                items.append(item)
    
    return jsonify({"items": items})



def write_log(process, filepath):
    with open(filepath, "w") as f:
        for line in process.stdout:
            f.write(line.decode())
            f.flush()

def cleanup():
    global running_process
    if running_process is not None:
        print("Shutting down Archipelago Server...")
        running_process.terminate()
        running_process.wait()

atexit.register(cleanup)

if __name__ == "__main__":
    app.run(debug=True, port=5001, use_reloader=False)
