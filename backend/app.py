from flask import Flask, request, jsonify, abort, send_file
from flask_cors import CORS
import os
import subprocess
import atexit
import threading
import sys
import zlib
import zipfile
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

@app.route("/upload", methods=["POST"])
def upload_file():
    global running_process
    global arch_file_path
    global extract_folder_path

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

@app.route("/log")
def stream_log():
    if running_process is None: 
        return

    f = open("logs/serverlog.txt", "r")
    
    result = { 
        "lines": f.readlines()
    }

    return jsonify(result)

@app.route("/log/last")
def stream_log_bottom():
    if running_process is None: 
        abort(404)

    f = open("logs/serverlog.txt", "r")
    
    result = { 
        "lines": f.readlines()[-25:]
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
