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
import psycopg # type: ignore
import pytz # type: ignore
from datetime import datetime
from babel.dates import format_datetime # type: ignore
from flask_pyoidc.flask_pyoidc import OIDCAuthentication # type: ignore
from flask_pyoidc.provider_configuration import ProviderConfiguration, ClientMetadata # type: ignore
sys.path.insert(0, "Archipelago-0.6.7")
import multidata
from server_state import ServerState
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
SERVER_PORT = app.config['SERVER_PORT']
PORT_RANGE = app.config['PORT_RANGE']
RETRY = app.config['RETRY']
SHUTDOWN_TIME = 7200

DB_HOST = app.config['DB_HOST']
DB_NAME = app.config['DB_NAME']
DB_USER = app.config['DB_USER']
DB_PASS = app.config['DB_PASS']
conn = None

# Everything is stored in a dictionary, which breaks when multiple worker threads are used (but I just use 1)
rooms = {}

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
    
    port = None
    
    # Generate random ports and find one that is available 
    ports = random.sample(range(SERVER_PORT, SERVER_PORT+PORT_RANGE), RETRY)
    for try_port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("localhost", try_port))
                port = try_port
                break
            except OSError:
                continue
    
    if port is None:
        return jsonify({"error": "Could not find an available port in range, try again later"}), 500
    
    if not os.path.isdir(UPLOAD_FOLDER):
        return jsonify({"error": "uploads folder does not exist"}), 500

    zip_save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    extract_folder_path = zip_save_path[:zip_save_path.index('.')]

    if os.path.isdir(extract_folder_path):
        return jsonify({"error": "Archipelago game with the same name already exists. Please change the name of your zip file."}), 409

    file.save(zip_save_path)

    room_id = str(uuid.uuid4())

    filename = None

    # Extract zip file and delete it
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

        # Build ids dict which contains what id goes to each item/location for each game
        ids = {}
        for game in decoded_arch["datapackage"]:
            subdict = decoded_arch["datapackage"][game]
            ids[game] = {}
            ids[game]['id_to_item_name'] = {v: k for k, v in subdict['item_name_to_id'].items()}
            ids[game]['id_to_location_name'] = {v: k for k, v in subdict['location_name_to_id'].items()}
        
        # Also build a list of every location and all the info about it to be inserted into the database
        # Also the name and game of every slot
        locations = []
        slotinfos = {}
        sphere_num = 1
        for sphere in decoded_arch["spheres"]:
            for slot in sphere:
                slotinfo = decoded_arch["slot_info"][slot]
                slotinfos[slot] = {"name": slotinfo.name, "game": slotinfo.game}
                for location_id in sphere[slot]:
                    location_tuple = decoded_arch["locations"][slot][location_id] # format is: (item_id, receiver_slot_id, unknown#)

                    to_name = decoded_arch["slot_info"][location_tuple[1]].name
                    location_name = ids[slotinfo.game]['id_to_location_name'][location_id]
                    if len(location_name) > 255:
                        location_name = location_name[:255]
                    item_name = ids[decoded_arch["slot_info"][location_tuple[1]].game]['id_to_item_name'][location_tuple[0]]

                    locations.append((slot, location_id, sphere_num, slotinfo.name, slotinfo.game, to_name, location_name, item_name, room_id))
            sphere_num+=1

    admin = session.get('userinfo').get('uuid')
    start = datetime.now()
    
    with conn.cursor() as cur:
        cur.execute("INSERT INTO rooms VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                    (room_id, try_port, admin, extract_folder_path, arch_file_path, False, start))

        with cur.copy("COPY locations (slot, location_id, sphere, from_name, game, to_name, location_name, item_name, room_id) FROM STDIN") as copy:
            for location in locations:
                copy.write_row(location)
        
        slots = []
        for slot in slotinfos:
            slots.append((slot, slotinfos[slot]['name'], slotinfos[slot]['game'], room_id))
        
        with cur.copy("COPY slots (id, name, game, room_id) FROM STDIN") as copy:
            for slot in slots:
                copy.write_row(slot)
        
        items = []
        for game in ids:
            for item_id in ids[game]['id_to_item_name']:
                items.append((game, ids[game]['id_to_item_name'][item_id], item_id, room_id))
        
        with cur.copy("COPY items (game, name, id, room_id) FROM STDIN") as copy:
            for item in items:
                copy.write_row(item)

        conn.commit()

    running_process = subprocess.Popen(
        ["python3", ARCHIPELAGO_SERVER, arch_file_path, f"--port={port}", f"--auto_shutdown={SHUTDOWN_TIME}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
        env={**os.environ, "HOME": UPLOAD_FOLDER}
    )

    logpath = f"{extract_folder_path}/server-log.txt"

    # Make the log file exist (don't know if I need to do this)
    with open(logpath, "w") as f:
        f.write("")

    # Separate thread to write stdout to a log file
    thread = threading.Thread(target=write_log, args=(running_process, logpath, room_id))
    thread.daemon = True
    thread.start()

    rooms[room_id] = running_process

    result = {
        "message": "Server started",
        "port": port,
        "room_id": room_id
    }

    return jsonify(result)

"""
Get all the running rooms and relevant info
"""
@api.route("/rooms", methods=["PUT"])
def get_all_rooms():
    current_rooms = []

    # user's timezone and locale data, as well as a couple of other things
    data = request.get_json().get("data")

    with conn.cursor() as cur:
        cur.execute("SELECT room_id, port, start, admin FROM rooms")
        db_rooms = cur.fetchall()
        for room in db_rooms:
            room_info = {}
            room_info['room_id'] = room[0]
            room_info['port'] = room[1]
            room_info['start'] = format_datetime(room[2].astimezone(pytz.timezone(data["timeZone"])), format='short', locale=data["locale"].replace('-', '_'))
            room_info['start_for_sorting'] = room[2]
            room_info['admin_uuid'] = room[3]
            if rooms[room[0]] is None:
                room_info['running'] = False
            else:
                room_info['running'] = True
            
            current_rooms.append(room_info)
    
    return jsonify({"rooms": sorted(current_rooms, key=lambda d: d['start_for_sorting'], reverse=True)})

"""
Stops specified room and deletes all files associated with it
"""
@api.route("/delete/<room_id>", methods=["DELETE"])
@_AUTH.oidc_auth('default')
def delete_room(room_id):
    if room_id not in rooms:
        return jsonify({"error": "No archipelago game with this id"}), 404

    with conn.cursor() as cur:
        cur.execute("SELECT admin, extract_folder_path FROM rooms WHERE room_id = %s", (room_id,))
        info = cur.fetchone()
        admin = info[0]
        extract_folder_path = info[1]

        if session.get('userinfo').get('uuid') != admin:
            return jsonify({"error": "you are not the admin of this server"}), 403
        
        if rooms[room_id] is not None:
            rooms[room_id].terminate()
            rooms[room_id].wait()
        
        shutil.rmtree(extract_folder_path)

        cur.execute("DELETE FROM rooms WHERE room_id = %s", (room_id,))

        conn.commit()

        rooms.pop(room_id, None)

    return jsonify({"message": "successfully deleted"})

"""
Request to restart the room. Does nothing if it's currently running 
"""
@api.route("/restart/<room_id>", methods=["PUT"])
def restart_server(room_id):
    if room_id not in rooms:
        return jsonify({"error": "No archipelago game with this id"}), 404

    with conn.cursor() as cur:
        cur.execute("SELECT arch_file_path, extract_folder_path, restarting, port FROM rooms WHERE room_id = %s", (room_id,))
        info = cur.fetchone()
        arch_file_path = info[0]
        extract_folder_path = info[1]
        restarting = info[2]
        port = info[3]
        running_process = rooms[room_id]

        if arch_file_path is None:
            return jsonify({"error": "no server to restart"}), 404
        
        if running_process is None:
            if restarting: # to handle multiple clients trying to restart at the same time
                return jsonify({"error": "Server is already restarting"}), 400
            
            cur.execute("UPDATE rooms SET restarting = %s WHERE room_id = %s", (True, room_id))
            conn.commit()
            
            # Ensure the port isn't taken by itself (perhaps unnecessary)
            if not wait_for_free_port(port):
                print("Timed out while waiting for port")
                cur.execute("UPDATE rooms SET restarting = %s WHERE room_id = %s", (False, room_id))
                conn.commit()

                return jsonify({"error": "Timed out while waiting for port"}), 500
            
            # Attempt to connect to the same port. If unavailable, try new ones
            ports = [port]
            first = True
            for try_port in ports:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    try:
                        s.bind(("localhost", try_port))
                        port = try_port
                    except OSError:
                        port = None
                        if first:
                            ports = ports + random.sample(range(SERVER_PORT, SERVER_PORT+PORT_RANGE), RETRY)
                            first = False
            
            if port is None:
                return jsonify({"error": "could not find a port to restart the server on"}), 500
            
            new_running_process = subprocess.Popen(
                ["python3", ARCHIPELAGO_SERVER, arch_file_path, f"--port={port}", f"--auto_shutdown={SHUTDOWN_TIME}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                env={**os.environ, "HOME": UPLOAD_FOLDER}
            )

            # If the subprocess failed to start, error
            time.sleep(1)
            if new_running_process.poll() is not None:
                cur.execute("UPDATE rooms SET restarting = %s WHERE room_id = %s", (False, room_id))
                conn.commit()
                
                return jsonify({"error": "the subprocess failed to start"}), 500

            logpath = f"{extract_folder_path}/server-log.txt"

            thread = threading.Thread(target=write_log, args=(new_running_process, logpath, room_id))
            thread.daemon = True
            thread.start()

            result = {
                "message": "Server started",
                "port": port
            }

            cur.execute("UPDATE rooms SET restarting = %s, port = %s WHERE room_id = %s", (False, port, room_id))
            conn.commit()
            rooms[room_id] = new_running_process

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
    
    with conn.cursor() as cur:
        cur.execute("SELECT extract_folder_path FROM rooms WHERE room_id = %s", (room_id,))
        extract_folder_path = cur.fetchone()[0]

        f = open(f"{extract_folder_path}/server-log.txt", "r")

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

    with conn.cursor() as cur:
        cur.execute("SELECT port, admin FROM rooms WHERE room_id = %s", (room_id,))
        info = cur.fetchone()
        
        return jsonify({
            "port": info[0],
            "admin": info[1]
        })

"""
Write the given command to stdin of the process of the specified room
"""
@api.route("/command/<room_id>", methods=["POST"])
@_AUTH.oidc_auth('default')
def server_command(room_id):
    if room_id not in rooms:
        return jsonify({"error": "No archipelago game with this id"}), 404

    if rooms[room_id] is None:
        return jsonify({"error": "Archipelago server not running"}), 404
    
    with conn.cursor() as cur:
        cur.execute("SELECT admin FROM rooms WHERE room_id = %s", (room_id,))
        admin = cur.fetchone()[0]

        if session.get('userinfo').get('uuid') != admin:
            return jsonify({"error": "user is not admin"}), 403
        
        data = request.get_json()
        command: str = data.get('command')
        rooms[room_id].stdin.write((command + '\n').encode())
        rooms[room_id].stdin.flush()

        if command.startswith('/release') and len(command.split(' ')) == 2:
            cur.execute("INSERT INTO released_games VALUES (%s, %s)", (command.split(' ')[1].lower(), room_id))
            conn.commit()

        return jsonify({"message": "ok"})

"""
Gets all the players participating in the multiworld and relevant data
"""
@api.route("/players/<room_id>")
def get_players(room_id):
    if room_id not in rooms:
        return jsonify({"error": "No archipelago game with this id"}), 404

    with conn.cursor() as cur:
        cur.execute("SELECT arch_file_path, extract_folder_path FROM rooms WHERE room_id = %s", (room_id,))
        info = cur.fetchone()
    
        players = multidata.get_players(info[0], info[1])

        return jsonify({"players": players})

"""
Sends the requested file 
"""
@api.route("/players/<room_id>/<filename>")
def send_patch_file(room_id, filename):
    if room_id not in rooms:
        return jsonify({"error": "No archipelago game with this id"}), 404

    with conn.cursor() as cur:
        cur.execute("SELECT extract_folder_path FROM rooms WHERE room_id = %s", (room_id,))
        extract_folder_path = cur.fetchone()[0]

        filepath = os.path.join(extract_folder_path, filename)

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

    with conn.cursor() as cur:
        cur.execute("SELECT arch_file_path, extract_folder_path, port FROM rooms WHERE room_id = %s", (room_id,))
        info = cur.fetchone()

        cur.execute("SELECT name FROM released_games WHERE room_id = %s", (room_id,))
        released_games = cur.fetchall()
        released_games_set = set()
        for game in released_games:
            released_games_set.add(game[0])

        players, totals, hints = multidata.multitracker_data(info[0], info[1], released_games_set, conn, room_id)

        return jsonify({"players": players, "totals": totals, "hints": hints, "port": info[2]})

"""
Gets received items, locations, and hints for given slot
"""
@api.route("/tracker/<room_id>/<int:slot>")
def individual_tracker_data(room_id, slot):
    if room_id not in rooms:
        return jsonify({"error": "No archipelago game with this id"}), 404

    with conn.cursor() as cur:
        cur.execute("SELECT extract_folder_path, arch_file_path FROM rooms WHERE room_id = %s", (room_id,))
        info = cur.fetchone()

        items, locations, hints = multidata.individual_player_data(info[0], info[1], room_id, slot)

        cur.execute("SELECT name FROM slots WHERE room_id = %s AND id = %s", (room_id, slot))
        name = cur.fetchone()[0]
        
        return jsonify({"items": items, "locations": locations, "hints": hints, "name": name})

"""
Gets every item received by every player
"""
@api.route("/spheres/<room_id>")
def sphere_items(room_id):
    if room_id not in rooms:
        return jsonify({"error": "No archipelago game with this id"}), 404

    with conn.cursor() as cur:
        cur.execute("SELECT extract_folder_path FROM rooms WHERE room_id = %s", (room_id,))
        extract_folder_path = cur.fetchone()[0]

        items = multidata.sphere_data(extract_folder_path, conn, room_id)
        
        return jsonify({"items": items})


"""
Starts up every archipelago server in the uploads folder
"""
def restart_all():
    global rooms
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    with conn.cursor() as cur:
        cur.execute("SELECT room_id, port, extract_folder_path, arch_file_path FROM rooms")
        rooms_db = cur.fetchall()
        
        for room in rooms_db:
            room_id = room[0]
            extract_folder_path = room[2]
            arch_file_path = room[3]

            if not os.path.isfile(arch_file_path):
                continue

            # Attempt to connect to the same port. If unavailable, try new ones
            ports = [room[1]]
            first = True
            port = None
            for try_port in ports:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    try:
                        s.bind(("localhost", try_port))
                        port = try_port
                    except OSError:
                        port = None
                        if first:
                            ports = ports + random.sample(range(SERVER_PORT, SERVER_PORT+PORT_RANGE), RETRY)
                            first = False
            
            if port is None:
                return jsonify({"error": "could not find a port to restart the server on"}), 500
            
            running_process = subprocess.Popen(
                ["python3", ARCHIPELAGO_SERVER, arch_file_path, f"--port={port}", f"--auto_shutdown={SHUTDOWN_TIME}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                env={**os.environ, "HOME": UPLOAD_FOLDER}
            )

            cur.execute("UPDATE rooms SET port = %s, restarting = %s WHERE room_id = %s", (port, False, room_id))

            logpath = f"{extract_folder_path}/server-log.txt"

            thread = threading.Thread(target=write_log, args=(running_process, logpath, room_id))
            thread.daemon = True
            thread.start()

            rooms[room_id] = running_process

        conn.commit()

"""
Writes the stdout of a process to a file
"""
def write_log(process, filepath, room_id):
    with open(filepath, "a") as f:
        for line in process.stdout:
            f.write(line.decode())
            f.flush()

        if room_id in rooms:
            if not conn:
                rooms[room_id].running_process = None
            else:
                rooms[room_id] = None

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
        if rooms[room_id] is not None:
            print(f"Shutting down Archipelago Server with id {room_id}...")
            rooms[room_id].terminate()
            rooms[room_id].wait()
    
    if conn:
        conn.close()

"""
Establishes the database connection
"""
def db_connection():
    global conn

    conn = psycopg.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)

"""
Creates schema of database if it doesn't exist already
"""
def apply_migrations():
    with conn.cursor() as cur:
        cur.execute("""CREATE TABLE IF NOT EXISTS migrations (
            id       serial
                constraint migrations_pk
                    primary key,
            filename text not null,
            applied  timestamp default now()
        );""")
        conn.commit()

        applied = set()
        cur.execute("SELECT filename FROM migrations")
        for row in cur.fetchall():
            applied.add(row[0])
        
        migration_files = sorted(os.listdir("migrations"))
        for filename in migration_files:
            if filename.endswith(".sql") and filename not in applied:
                with open(f"migrations/{filename}") as f:
                    cur.execute(f.read())
                cur.execute("INSERT INTO migrations (filename) VALUES (%s)", (filename,))
                conn.commit()

app.register_blueprint(api, url_prefix='/api')

if __name__ == "__main__":
    with app.app_context():
        conn = psycopg.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        apply_migrations()
        restart_all()
        atexit.register(cleanup)
    app.run(debug=True, port=5001, use_reloader=False, host="0.0.0.0")
