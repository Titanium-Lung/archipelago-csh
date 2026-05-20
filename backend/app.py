from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import os
import subprocess
import atexit
import threading

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

UPLOAD_FOLDER = "uploads"
ARCHIPELAGO_SERVER = "Archipelago-0.6.7/MultiServer.py"
SERVER_PORT = 38281

running_process = None

@app.route("/upload", methods=["POST"])
def upload_file():
    global running_process

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if not file.filename.endswith(".archipelago"):
        return jsonify({"error": "File must be a .archipelago file"}), 400

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    if running_process is not None:
        running_process.terminate()
    
    running_process = subprocess.Popen(
        ["Archipelago-0.6.7/venv/bin/python3", ARCHIPELAGO_SERVER, save_path, f"--port={SERVER_PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
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
        print(SERVER_PORT)
        return jsonify({
            "port": SERVER_PORT
        })
    


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
