from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess
import atexit

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

UPLOAD_FOLDER = "uploads"
ARCHIPELAGO_SERVER = "/Users/cooper/Archipelago-0.6.7/MultiServer.py"
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
        ["/Users/cooper/Archipelago-0.6.7/venv/bin/python3", ARCHIPELAGO_SERVER, save_path, f"--port={SERVER_PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    for line in running_process.stdout:
        print(line)

    return jsonify({
        "message": "Server started",
        "filename": file.filename,
        "port": SERVER_PORT,
    })

def cleanup():
    global running_process
    if running_process is not None:
        print("Shutting down Archipelago Server...")
        running_process.terminate()
        running_process.wait()

atexit.register(cleanup)

if __name__ == "__main__":
    app.run(debug=True, port=5001, use_reloader=False)
