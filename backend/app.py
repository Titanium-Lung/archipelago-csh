from gevent import monkey # type: ignore
monkey.patch_all() 
from flask import Flask, request, jsonify, send_file, redirect, session, Blueprint, Response, stream_with_context # type: ignore
from flask_cors import CORS # type: ignore
import os
import subprocess
import atexit
import sys
import zlib
import zipfile
import socket
import time
import uuid
import random
import shutil
import psycopg
import psycopg_pool
import pytz
from datetime import datetime
from babel.dates import format_datetime # type: ignore
from flask_pyoidc.flask_pyoidc import OIDCAuthentication # type: ignore
from flask_pyoidc.provider_configuration import ProviderConfiguration, ClientMetadata # type: ignore
sys.path.insert(0, "Archipelago-0.6.7")
import multidata
from process_manager_client import start_server, send_command, is_running, exists, terminate, terminate_all
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
pool = psycopg_pool.ConnectionPool(f"dbname={DB_NAME} user={DB_USER} password={DB_PASS} host={DB_HOST}", open=False)

# Only for local development
process_manager = None

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
    admin = session.get('userinfo').get('uuid')
    start = datetime.now()

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
    
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO rooms VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                            (room_id, port, admin, extract_folder_path, arch_file_path, False, start))

                # Build a list of every location and all the info about it to be inserted into the database
                # Also the name and game of every slot
                slotinfos = {}
                with cur.copy("COPY locations (slot, location_id, sphere, from_name, game, to_name, location_name, item_name, room_id) FROM STDIN") as copy:
                    sphere_num = 1
                    for sphere in decoded_arch["spheres"]:
                        for slot in sphere:
                            slotinfo = decoded_arch["slot_info"][slot]
                            slotinfos[slot] = {"name": slotinfo.name, "game": slotinfo.game}
                            for location_id in sphere[slot]:
                                location_tuple = decoded_arch["locations"][slot][location_id] # format is: (item_id, receiver_slot_id, unknown#)

                                to_name = decoded_arch["slot_info"][location_tuple[1]].name
                                location_name = ids[slotinfo.game]['id_to_location_name'][location_id]
                                item_name = ids[decoded_arch["slot_info"][location_tuple[1]].game]['id_to_item_name'][location_tuple[0]]

                                copy.write_row((slot, location_id, sphere_num, slotinfo.name, slotinfo.game, to_name, location_name, item_name, room_id))
                        sphere_num+=1
                
                with cur.copy("COPY slots (id, name, game, room_id) FROM STDIN") as copy:
                    for slot in slotinfos:
                        copy.write_row((slot, slotinfos[slot]['name'], slotinfos[slot]['game'], room_id))

                with cur.copy("COPY items (game, name, id, room_id) FROM STDIN") as copy:
                    for game in ids:
                        for item_id in ids[game]['id_to_item_name']:
                            copy.write_row((game, ids[game]['id_to_item_name'][item_id], item_id, room_id))
        
        args = {"arch_file_path": arch_file_path, "port": port, "extract_folder_path": extract_folder_path}

        result = start_server(room_id, args)

        if result.get("result", None):
            return jsonify({"error": "The server failed to start"}), 500
    
        conn.commit()

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

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT room_id, port, start, admin FROM rooms WHERE port >= %s AND port < %s", (SERVER_PORT, SERVER_PORT+PORT_RANGE))
            db_rooms = cur.fetchall()
            for room in db_rooms:
                room_info = {}
                room_info['room_id'] = room[0]
                room_info['port'] = room[1]
                room_info['start'] = format_datetime(room[2].astimezone(pytz.timezone(data["timeZone"])), format='short', locale=data["locale"].replace('-', '_'))
                room_info['start_for_sorting'] = room[2]
                room_info['admin_uuid'] = room[3]
                if is_running(room[0]).get("running"):
                    room_info['running'] = True
                else:
                    room_info['running'] = False
                
                current_rooms.append(room_info)
    
    return jsonify({"rooms": sorted(current_rooms, key=lambda d: d['start_for_sorting'], reverse=True)})

"""
Stops specified room and deletes all files associated with it
"""
@api.route("/delete/<room_id>", methods=["DELETE"])
@_AUTH.oidc_auth('default')
def delete_room(room_id):
    if not exists(room_id).get("exists"):
        return jsonify({"error": "No archipelago game with this id"}), 404

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT admin, extract_folder_path FROM rooms WHERE room_id = %s", (room_id,))
            info = cur.fetchone()
            admin = info[0]
            extract_folder_path = info[1]

            if session.get('userinfo').get('uuid') != admin:
                return jsonify({"error": "you are not the admin of this server"}), 403
            
            terminate(room_id)
            
            shutil.rmtree(extract_folder_path)

            cur.execute("DELETE FROM rooms WHERE room_id = %s", (room_id,))

        conn.commit()

    return jsonify({"message": "successfully deleted"})

"""
Request to restart the room. Does nothing if it's currently running 
"""
@api.route("/restart/<room_id>", methods=["PUT"])
def restart_server(room_id):
    if not exists(room_id).get("exists"):
        return jsonify({"error": "No archipelago game with this id"}), 404

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT arch_file_path, extract_folder_path, restarting, port FROM rooms WHERE room_id = %s", (room_id,))
            info = cur.fetchone()
            arch_file_path = info[0]
            extract_folder_path = info[1]
            restarting = info[2]
            port = info[3]

            if arch_file_path is None:
                return jsonify({"error": "no server to restart"}), 404
            
            if not is_running(room_id).get("running"):
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
                
                args = {"arch_file_path": arch_file_path, "port": port, "extract_folder_path": extract_folder_path}

                result = start_server(room_id, args)

                if result.get("result", None):
                    cur.execute("UPDATE rooms SET restarting = %s WHERE room_id = %s", (False, room_id))
                    conn.commit()
                    
                    return jsonify({"error": "the subprocess failed to start"}), 500

                result = {
                    "message": "Server started",
                    "port": port
                }

                cur.execute("UPDATE rooms SET restarting = %s, port = %s WHERE room_id = %s", (False, port, room_id))
                conn.commit()

                return jsonify(result)
            else:
                return jsonify({"error": "server already running"}), 400

"""
Get the contents of the log file of the specified room
"""
@api.route("/log/<room_id>")
def get_log(room_id):
    if not exists(room_id).get("exists"):
        return jsonify({"error": "No archipelago game with this id"}), 404
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT extract_folder_path FROM rooms WHERE room_id = %s", (room_id,))
            extract_folder_path = cur.fetchone()[0]

            f = open(f"{extract_folder_path}/server-log.txt", "r")

            result = { 
                "lines": f.readlines()
            }

            return jsonify(result)

"""
Set up a stream that sends new lines in the log to the frontend
"""
@api.route("/log/stream/<room_id>")
def get_log_stream(room_id):
    if not exists(room_id).get("exists"):
        return jsonify({"error": "No archipelago game with this id"}), 404
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT extract_folder_path FROM rooms WHERE room_id = %s", (room_id,))
            extract_folder_path = cur.fetchone()[0]

            logpath = f"{extract_folder_path}/server-log.txt"

            return Response(
                stream_with_context(stream_log(logpath)),
                mimetype="text/event-stream",
                headers={"X-Accel-Buffering": "no"}
            )

"""
Get the port and admin of the specified room
"""
@api.route("/room/<room_id>")
def room_info(room_id):
    if not exists(room_id).get("exists"):
        return jsonify({"error": "No archipelago game with this id"}), 404

    with pool.connection() as conn:
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
    if not exists(room_id).get("exists"):
        return jsonify({"error": "No archipelago game with this id"}), 404

    if not is_running(room_id).get("running"):
        return jsonify({"error": "Archipelago server not running"}), 404
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT admin FROM rooms WHERE room_id = %s", (room_id,))
            admin = cur.fetchone()[0]

            if session.get('userinfo').get('uuid') != admin:
                return jsonify({"error": "user is not admin"}), 403
            
            data = request.get_json()
            command: str = data.get('command')
            send_command(room_id, command)

            if command.startswith('/release') and len(command.split(' ')) == 2:
                cur.execute("INSERT INTO released_games VALUES (%s, %s)", (command.split(' ')[1].lower(), room_id))
                conn.commit()

            return jsonify({"message": "ok"})

"""
Gets all the players participating in the multiworld and relevant data
"""
@api.route("/players/<room_id>")
def get_players(room_id):
    if not exists(room_id).get("exists"):
        return jsonify({"error": "No archipelago game with this id"}), 404

    with pool.connection() as conn:
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
    if not exists(room_id).get("exists"):
        return jsonify({"error": "No archipelago game with this id"}), 404

    with pool.connection() as conn:
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
    if not exists(room_id).get("exists"):
        return jsonify({"error": "No archipelago game with this id"}), 404

    with pool.connection() as conn:
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
    if not exists(room_id).get("exists"):
        return jsonify({"error": "No archipelago game with this id"}), 404

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT extract_folder_path, arch_file_path FROM rooms WHERE room_id = %s", (room_id,))
            info = cur.fetchone()

            items, locations, hints, name, player_uuid = multidata.individual_player_data(info[0], info[1], room_id, slot, conn)
            
            return jsonify({"items": items, "locations": locations, "hints": hints, "name": name, "uuid": player_uuid})

"""
Assigns the current logged in user to the requested slot
"""
@api.route("/assign/<room_id>/<int:slot>", methods=["PUT", "DELETE"])
def assign_to_slot(room_id, slot):
    if not exists(room_id).get("exists"):
        return jsonify({"error": "No archipelago game with this id"}), 404

    if 'userinfo' not in session:
        return jsonify({"error": "User is not logged in"}), 403

    uuid = None
    if session.get('userinfo').get('preferred_username'):
        uuid = session.get('userinfo').get('uuid')
    else:
        uuid = session.get('userinfo').get('sub')
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            if request.method == 'PUT':
                cur.execute("UPDATE slots SET player_uuid = %s WHERE room_id = %s AND id = %s", (uuid, room_id, slot))

                conn.commit()

                return jsonify({"message": "Successfully assigned"})
            elif request.method == 'DELETE':
                cur.execute("UPDATE slots SET player_uuid = %s WHERE room_id = %s AND id = %s", (None, room_id, slot))

                conn.commit()

                return jsonify({"message": "Sucecssfully UNassigned"})

"""
Gets every item received by every player
"""
@api.route("/spheres/<room_id>")
def sphere_items(room_id):
    if not exists(room_id).get("exists"):
        return jsonify({"error": "No archipelago game with this id"}), 404

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT extract_folder_path FROM rooms WHERE room_id = %s", (room_id,))
            extract_folder_path = cur.fetchone()[0]

            items = multidata.sphere_data(extract_folder_path, conn, room_id)
            
            return jsonify({"items": items})

@api.route("/history")
def get_history():
    if 'userinfo' not in session:
        return jsonify({"error": "User is not logged in"}), 403

    uuid = None
    if session.get('userinfo').get('preferred_username'):
        uuid = session.get('userinfo').get('uuid')
    else:
        uuid = session.get('userinfo').get('sub')

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name, game, checks FROM slots WHERE player_uuid = %s", (uuid,))
            slots_db = cur.fetchall()

            slots = []
            for slot_info in slots_db:
                slot = {}
                slot['name'] = slot_info[0]
                slot['game'] = slot_info[1]
                slot['checks'] = slot_info[2]
                slots.append(slot)

            return jsonify({"slots": slots})


"""
Starts up every archipelago server in the uploads folder
"""
def restart_all():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    with psycopg.connect(f"dbname={DB_NAME} user={DB_USER} password={DB_PASS} host={DB_HOST}") as conn: # Connection pool isn't open yet. Should be okay since it runs once at the start
        with conn.cursor() as cur:
            cur.execute("SELECT room_id, port, extract_folder_path, arch_file_path FROM rooms WHERE port >= %s AND port < %s", (SERVER_PORT, SERVER_PORT+PORT_RANGE))
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
                
                args = {"arch_file_path": arch_file_path, "port": port, "extract_folder_path": extract_folder_path}

                start_server(room_id, args)

                if room[1] != port:
                    cur.execute("UPDATE rooms SET port = %s WHERE room_id = %s", (port, room_id))

        conn.commit()

def stream_log(filepath):
    with open(filepath, "r") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if line:
                yield f"data: {line.rstrip()}\n\n"
            else:
                time.sleep(0.5)

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
Terminate all running rooms, the process manager, and close the database connection
Only used for local development
"""
def cleanup():
    terminate_all()
    if process_manager:
        process_manager.terminate()
        process_manager.wait()

"""
Creates schema of database if it doesn't exist already
"""
def apply_migrations():
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS migrations (
                id       serial
                    constraint migrations_pk
                        primary key,
                filename text not null
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

atexit.register(pool.close)

if __name__ == "__main__":
    with app.app_context(): # Only used for local development
        pool.open()
        apply_migrations()

        process_manager = subprocess.Popen(["python3", "process_manager.py"])
        time.sleep(1)

        restart_all()
        atexit.register(cleanup)

    app.run(debug=True, port=5001, use_reloader=False, host="0.0.0.0")
