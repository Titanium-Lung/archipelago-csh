from flask import Flask, request, jsonify, send_file, redirect, session, Blueprint
from flask_cors import CORS
import os
import subprocess
import atexit
import threading
import sys
import zlib
import zipfile
import socket
import time
import uuid
import random
import shutil
import json
from datetime import datetime
from flask_pyoidc.flask_pyoidc import OIDCAuthentication # type: ignore
from flask_pyoidc.provider_configuration import ProviderConfiguration, ClientMetadata # type: ignore
sys.path.insert(0, "Archipelago-0.6.7")
import multidata
from Utils import restricted_loads # type: ignore
from dotenv import load_dotenv # type: ignore
load_dotenv()

app = Flask(__name__)

api = Blueprint('api', __name__)

app.config.from_pyfile(os.path.join(os.getcwd(), 'config.env.py'))

CORS(app, resources={r"/*": {"origins": app.config['FRONTEND_URL']}}, supports_credentials=True)

app.secret_key = app.config['SECRET_KEY']

_CONFIG = ProviderConfiguration(
    app.config['OIDC_ISSUER'],
    client_metadata=ClientMetadata(**app.config['OIDC_CLIENT_CONFIG']))

_GOOGLE_CONFIG = ProviderConfiguration(
    issuer="https://accounts.google.com",
    client_metadata=ClientMetadata(**app.config['GOOGLE_CLIENT_CONFIG']),
    auth_request_params={
        'scope': ['profile']
    })

_AUTH = OIDCAuthentication({'default': _CONFIG, 'google': _GOOGLE_CONFIG}, app)

UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']
ARCHIPELAGO_SERVER = "Archipelago-0.6.7/MultiServer.py"
SERVER_PORT = 38281
PORT_RANGE = 1
RETRY = 1
SHUTDOWN_TIME = 7200

rooms = {}

class ServerState():
    def __init__(self):
        self.running_process = None
        self.extract_folder_path = None
        self.arch_file_path = None
        self.location_info = {}
        self.ids = {}
        self.slotinfos = {}
        self.port = None
        self.restarting = False
        self.admin = None
        self.start = None
        self.released_games = {} # dictionary and not set for json encoding lol

"""
Login with CSH 
"""
@api.route("/login")
@_AUTH.oidc_auth('default')
def login():
    return redirect(app.config['FRONTEND_URL'])

"""
Login with Google
"""
@api.route("/googlelogin")
@_AUTH.oidc_auth('google')
def google_login():
    return redirect(app.config['FRONTEND_URL'])

"""
Logout 
"""
@api.route("/logout")
@_AUTH.oidc_logout
def logout():
    return redirect(app.config['FRONTEND_URL'])

"""
Gets data of user if they are logged in
"""
@api.route("/user")
def user_info():
    user = session.get('userinfo')
    if user is None:
        return jsonify({"error":"not logged in"}), 401
    
    if user.get('preferred_username'):
        return jsonify({"username": user.get('preferred_username'), "uuid": user.get('uuid'), "picture_url": "https://profiles.csh.rit.edu/image/"+user.get('preferred_username'), "csh": True})
    elif user.get('name'):
        return jsonify({"username": user.get('name'), "uuid": user.get('sub'), "picture_url": user.get('picture'), "csh": False})
    else:
        return jsonify({"error": "could not find name"}), 400

"""
Handles upload of zip file to start an archipelago server 
"""
@api.route("/upload", methods=["POST"])
@_AUTH.oidc_auth('default')
def upload_file():
    global rooms

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if not file.filename.endswith(".zip"):
        return jsonify({"error": "File must be a .zip file"}), 400
    
    room_port = None
    
    # Generate random ports and find one that is available 
    ports = random.sample(range(SERVER_PORT, SERVER_PORT+PORT_RANGE), RETRY)
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("localhost", port))
                print(f"Port is {port}")
                room_port = port
                break
            except OSError:
                print(f"Failed to bind port: {port}")
                continue
    
    if room_port is None:
        return jsonify({"error": "Could not find an available port in range, try again later"}), 500
    
    # Check if folders exist for testing
    if not os.path.isdir(UPLOAD_FOLDER):
        return jsonify({"error": "uploads folder does not exist"}), 500

    zip_save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    extract_folder_path = zip_save_path[:zip_save_path.index('.')]

    if os.path.isdir(extract_folder_path):
        return jsonify({"warning": "folder with the same name already exists"}), 409

    file.save(zip_save_path)

    room_id = str(uuid.uuid4())
    state: ServerState = ServerState()

    state.port = room_port
    state.extract_folder_path = extract_folder_path

    filename = None

    # Extract zip file and delete it
    with zipfile.ZipFile(zip_save_path) as zf:
        for name in zf.namelist():
            if name.endswith(".archipelago"):
                filename = name

        zf.extractall(path=state.extract_folder_path)
        os.remove(zip_save_path)
    
    if filename is None:
        return jsonify({"error": "No archipelago file found in zip"}), 400

    state.arch_file_path = os.path.join(state.extract_folder_path, filename)

    with open(state.arch_file_path, "rb") as f:
        data = f.read()
        decoded_arch = restricted_loads(zlib.decompress(data[1:]))

        # Build ids dict which contains what id goes to each item/location for each game
        state.ids = {}
        for game in decoded_arch["datapackage"]:
            subdict = decoded_arch["datapackage"][game]
            state.ids[game] = {}
            state.ids[game]['id_to_item_name'] = {v: k for k, v in subdict['item_name_to_id'].items()}
            state.ids[game]['id_to_location_name'] = {v: k for k, v in subdict['location_name_to_id'].items()}
        
        # Build location_info dict which contains every location and all the info about it
        # Structure is: location_info = {slot#: {location_id: {name, sphere, from, game, to, location_name, item_name}}}
        sphere_num = 1
        for sphere in decoded_arch["spheres"]:
            for slot in sphere:
                slotinfo = decoded_arch["slot_info"][slot]
                state.slotinfos[slot] = {"name": slotinfo.name, "game": slotinfo.game}
                if slot not in state.location_info:
                    state.location_info[slot] = {}

                for location_id in sphere[slot]:
                    state.location_info[slot][location_id] = {}

                    state.location_info[slot][location_id]["sphere"] = sphere_num
                    state.location_info[slot][location_id]["from"] = slotinfo.name
                    state.location_info[slot][location_id]["game"] = slotinfo.game

                    location_tuple = decoded_arch["locations"][slot][location_id] # format is: (item_id, receiver_slot_id, unknown#)
                    state.location_info[slot][location_id]["to"] = decoded_arch["slot_info"][location_tuple[1]].name
                    state.location_info[slot][location_id]["location_name"] = state.ids[slotinfo.game]['id_to_location_name'][location_id]
                    state.location_info[slot][location_id]["item_name"] = state.ids[decoded_arch["slot_info"][location_tuple[1]].game]['id_to_item_name'][location_tuple[0]]
            sphere_num+=1

        # Id to location name is not used anywhere else
        for game in state.ids:
            state.ids[game].pop('id_to_location_name', None)

    if state.running_process is not None:
        state.running_process.terminate()
    
    state.running_process = subprocess.Popen(
        ["python3", ARCHIPELAGO_SERVER, state.arch_file_path, f"--port={state.port}", f"--auto_shutdown={SHUTDOWN_TIME}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
        env={**os.environ, "HOME": UPLOAD_FOLDER}
    )

    logpath = f"{state.extract_folder_path}/server-log.txt"

    # Make the log file exist (don't know if I need to do this)
    with open(logpath, "w") as f:
        f.write("")

    # Separate thread to write stdout to a log file
    thread = threading.Thread(target=write_log, args=(state.running_process, logpath, room_id))
    thread.daemon = True
    thread.start()

    state.admin = session.get('userinfo').get('uuid')
    state.start = datetime.now()

    rooms[room_id] = state

    save_state(room_id, state)

    result = {
        "message": "Server started",
        "filename": file.filename,
        "port": state.port,
        "room_id": room_id
    }

    return jsonify(result)

"""
Get all the running rooms and relevant info
"""
@api.route("/rooms")
def get_all_rooms():
    current_rooms = []
    
    for room_id in rooms:
        room_info = {}
        room_info['room_id'] = room_id
        room_info['port'] = rooms[room_id].port
        room_info["start"] = rooms[room_id].start.strftime('%d/%m/%y %H:%M')
        room_info['admin_uuid'] = rooms[room_id].admin
        current_rooms.append(room_info)
    
    return jsonify({"rooms": current_rooms})

"""
Stops specified room and deletes all files associated with it
"""
@api.route("/delete/<room_id>", methods=["DELETE"])
@_AUTH.oidc_auth('default')
def delete_room(room_id):
    if room_id not in rooms:
        return jsonify({"error": "No archipelago game with this id"}), 404

    state: ServerState = rooms[room_id]

    if session.get('userinfo').get('uuid') != state.admin:
        return jsonify({"error": "you are not the admin of this server"}), 403
    
    if state.running_process is not None:
        state.running_process.terminate()
        state.running_process.wait()
    
    shutil.rmtree(state.extract_folder_path)

    rooms.pop(room_id)

    return jsonify({"message": "successfully deleted"})

"""
Request to restart the room. Does nothing if it's currently running 
"""
@api.route("/restart/<room_id>", methods=["PUT"])
def restart_server(room_id):
    if room_id not in rooms:
        return jsonify({"error": "No archipelago game with this id"}), 404

    state: ServerState = rooms[room_id]

    if state.arch_file_path is None:
        return jsonify({"error": "no server to restart"}), 404
    
    if state.running_process is None:
        if state.restarting: # to handle multiple clients trying to restart at the same time
            return jsonify({"error": "Server is already restarting"}), 400
        
        state.restarting = True
        
        # Ensure the port isn't taken by itself (perhaps unnecessary)
        if not wait_for_free_port(state.port):
            print("Timed out while waiting for port")
            state.restarting = False
            return jsonify({"error": "Timed out while waiting for port"}), 500
        
        # Attempt to connect to the same port. If unavailable, try new ones
        ports = [state.port]
        first = True
        for port in ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    s.bind(("localhost", port))
                    print(f"Port is {port}")
                    state.port = port
                except OSError:
                    print(f"Failed to bind port {port}")
                    state.port = None
                    if first:
                        ports = ports + random.sample(range(SERVER_PORT, SERVER_PORT+PORT_RANGE), RETRY)
                        first = False
        
        if state.port is None:
            return jsonify({"error": "could not find a port to restart the server on"}), 500
        
        state.running_process = subprocess.Popen(
            ["python3", ARCHIPELAGO_SERVER, state.arch_file_path, f"--port={state.port}", f"--auto_shutdown={SHUTDOWN_TIME}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            env={**os.environ, "HOME": UPLOAD_FOLDER}
        )

        logpath = f"{state.extract_folder_path}/server-log.txt"

        thread = threading.Thread(target=write_log, args=(state.running_process, logpath, room_id))
        thread.daemon = True
        thread.start()

        save_state(room_id, state)

        result = {
            "message": "Server started",
            "port": state.port
        }

        state.restarting = False

        return jsonify(result)
    else:
        return jsonify({"error": "server already running"}), 400

"""
Get the contents of the log file of the specified room
"""
@api.route("/log/<room_id>")
def stream_log(room_id):
    if room_id not in rooms:
        return jsonify({"error": "No archipelago game with this id"}), 404

    state: ServerState = rooms[room_id]

    if state.arch_file_path is None: 
        return jsonify({"error": "no archipelago game loaded"}), 404

    f = open(f"{state.extract_folder_path}/server-log.txt", "r")
    
    result = { 
        "lines": f.readlines()
    }

    return jsonify(result)

"""
Get the port and admin of the specified room
"""
@api.route("/room/<room_id>")
def room_info(room_id):
    if room_id not in rooms:
            return jsonify({"error": "No archipelago game with this id"}), 404

    state: ServerState = rooms[room_id]

    if state.arch_file_path is None:
        return jsonify({"error": "no archipelago game uploaded"}), 404
    
    return jsonify({
        "port": state.port,
        "admin": state.admin
    })

"""
Write the given command to stdin of the process of the specified room
"""
@api.route("/command/<room_id>", methods=["POST"])
@_AUTH.oidc_auth('default')
def server_command(room_id):
    if room_id not in rooms:
        return jsonify({"error": "No archipelago game with this id"}), 404

    state: ServerState = rooms[room_id]

    if state.running_process is None:
        return jsonify({"error": "Archipelago server not running"}), 404

    if session.get('userinfo').get('uuid') != state.admin:
        return jsonify({"error": "user is not admin"}), 400
    
    data = request.get_json()
    command: str = data.get('command')
    state.running_process.stdin.write((command + '\n').encode())
    state.running_process.stdin.flush()

    if command.startswith('/release') and len(command.split(' ')) == 2:
        state.released_games[command.split(' ')[1].lower()] = ""
        save_state(room_id, state)

    return jsonify({"message": "ok"})

"""
Gets all the players participating in the multiworld and relevant data
"""
@api.route("/players/<room_id>")
def get_players(room_id):
    if room_id not in rooms:
        return jsonify({"error": "No archipelago game with this id"}), 404

    state: ServerState = rooms[room_id]

    if state.arch_file_path is None:
        return jsonify({"error": "No archipelago game uploaded"}), 404

    players = multidata.get_players(state)

    return jsonify({"players": players})

"""
Sends the requested file 
"""
@api.route("/players/<room_id>/<filename>")
def send_patch_file(room_id, filename):
    if room_id not in rooms:
        return jsonify({"error": "No archipelago game with this id"}), 404

    state: ServerState = rooms[room_id]

    if state.arch_file_path is None: 
        return jsonify({"error": "no archipelago game loaded"}), 404
    
    filepath = os.path.join(state.extract_folder_path, filename)

    if not os.path.exists(filepath):
        return jsonify({"error":"requested file does not exist"})

    return send_file(filepath)

"""
Gets the data for each player in the multiworld 
Data includes slot id, name, game, checks gotten, total checks, and last activity (most recent check)
Also gets all hints
"""
@api.route("/tracker/<room_id>")
def multiworld_data(room_id): 
    if room_id not in rooms:
        return jsonify({"error": "No archipelago game with this id"}), 404

    state: ServerState = rooms[room_id]

    if state.arch_file_path is None: 
        return jsonify({"error": "no archipelago game loaded"}), 404

    players, totals, hints = multidata.multitracker_data(state)

    return jsonify({"players": players, "totals": totals, "hints": hints, "port": state.port})

"""
Gets received items, locations, and hints for given slot
"""
@api.route("/tracker/<room_id>/<int:slot>")
def individual_tracker_data(room_id, slot):
    if room_id not in rooms:
        return jsonify({"error": "No archipelago game with this id"}), 404

    state: ServerState = rooms[room_id]

    if state.arch_file_path is None: 
        return jsonify({"error": "no archipelago game loaded"}), 404

    items, locations, hints = multidata.individual_player_data(state, slot)
    
    return jsonify({"items": items, "locations": locations, "hints": hints, "name": state.slotinfos[slot]["name"]})

"""
Gets every item received by every player
"""
@api.route("/spheres/<room_id>")
def sphere_items(room_id):
    if room_id not in rooms:
        return jsonify({"error": "No archipelago game with this id"}), 404

    state: ServerState = rooms[room_id]

    if state.arch_file_path is None: 
        return jsonify({"error": "no archipelago game loaded"}), 404

    items = multidata.sphere_data(state)
    
    return jsonify({"items": items})


"""
Starts up every archipelago server in the uploads folder
"""
def restart_all():
    global rooms

    with os.scandir(UPLOAD_FOLDER) as uploads:
        for server in uploads:
            if server.is_dir():
                if os.path.isfile(f"{server.path}/state.json"):
                    with open(f"{server.path}/state.json") as f:
                        data = json.load(f)

                        room_id = data["room_id"]
                        state: ServerState = ServerState()
                        state.arch_file_path = data["arch_file_path"]
                        state.extract_folder_path = data["extract_folder_path"]
                        
                        # Integer keys get changed to strings when serialised
                        location_info = {}
                        for slot in data["location_info"]: 
                            location_info[int(slot)] = {int(k): v for k, v in data["location_info"][slot].items()}
                        state.location_info = location_info

                        ids = {}
                        for game in data["ids"]:
                            ids[game] = {}
                            ids[game]["id_to_item_name"] = {int(k): v for k, v in data["ids"][game]["id_to_item_name"].items()}
                        state.ids = ids

                        state.slotinfos = {int(k): v for k, v in data["slotinfos"].items()}
                        state.port = data["port"]
                        state.admin = data["admin"]
                        state.start = datetime.fromtimestamp(data["start"])
                        state.released_games = data["released_games"]

                        # Attempt to connect to the same port. If unavailable, try new ones
                        ports = [state.port]
                        first = True
                        for port in ports:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                                try:
                                    s.bind(("localhost", port))
                                    print(f"Port is {port}")
                                    state.port = port
                                except OSError:
                                    print(f"Failed to bind port {port}")
                                    state.port = None
                                    if first:
                                        ports = ports + random.sample(range(SERVER_PORT, SERVER_PORT+PORT_RANGE), RETRY)
                                        first = False
                        
                        if state.port is None:
                            return jsonify({"error": "could not find a port to restart the server on"}), 500
                        
                        state.running_process = subprocess.Popen(
                            ["python3", ARCHIPELAGO_SERVER, state.arch_file_path, f"--port={state.port}", f"--auto_shutdown={SHUTDOWN_TIME}"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            stdin=subprocess.PIPE,
                            env={**os.environ, "HOME": UPLOAD_FOLDER}
                        )

                        logpath = f"{state.extract_folder_path}/server-log.txt"

                        thread = threading.Thread(target=write_log, args=(state.running_process, logpath, room_id))
                        thread.daemon = True
                        thread.start()

                        save_state(room_id, state)

                        rooms[room_id] = state

"""
Saves the current server state into a json file
"""
def save_state(room_id, state: ServerState):
    data = {
        "room_id": room_id,
        "arch_file_path": state.arch_file_path,
        "extract_folder_path": state.extract_folder_path,
        "location_info": state.location_info,
        "ids": state.ids,
        "slotinfos": state.slotinfos,
        "port": state.port,
        "admin": state.admin,
        "start": state.start.timestamp(),
        "released_games": state.released_games
    }
    with open(f"{state.extract_folder_path}/state.json", "w") as f:
        json.dump(data, f)

"""
Writes the stdout of a process to a file
"""
def write_log(process, filepath, room_id):
    with open(filepath, "a") as f:
        for line in process.stdout:
            f.write(line.decode())
            f.flush()

        if room_id in rooms:
            rooms[room_id].running_process = None

"""
Check if certain port is free for 10 seconds
"""
def wait_for_free_port(port, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("localhost", port))
                return True
            except OSError:
                time.sleep(0.5)
    return False

"""
When program closes, stop all running rooms
"""
def cleanup():
    global rooms
    for room_id in rooms:
        state = rooms[room_id]
        if state.running_process is not None:
            print(f"Shutting down Archipelago Server with id {room_id}...")
            state.running_process.terminate()
            state.running_process.wait()

atexit.register(cleanup)

app.register_blueprint(api, url_prefix='/api')

if __name__ == "__main__":
    with app.app_context():
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        restart_all()
    app.run(debug=True, port=5001, use_reloader=False, host="0.0.0.0")
