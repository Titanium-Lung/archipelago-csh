"""
As a subprocess, manages all running archipelago servers as subprocesses 
"""

import json
import os
import subprocess
import socket
import threading
import time
from app import UPLOAD_FOLDER, ARCHIPELAGO_SERVER, SHUTDOWN_TIME

HOST = "localhost"
PORT = 6000

processes = {}

"""
Handles a TCP connection, sending the message to handle_message
"""
def handle_client(conn):
    with conn:
        data = conn.recv(4096).decode()
        message = json.loads(data)
        response = handle_message(message)
        conn.sendall(json.dumps(response).encode())

"""
Different function based on what action the TCP message sent was
"""
def handle_message(message):
    action = message["action"]
    room_id = message.get("room_id")

    if action == "start":
        return start_server(room_id, message.get("args"))
    elif action == "send_command":
        server_message(room_id, message.get("command"))
    elif action == "is_running":
        return is_running(room_id)
    elif action == "exists":
        return exists(room_id)
    elif action == "terminate":
        terminate(room_id)
    elif action == "terminate_all":
        terminate_all()

"""
Starts up an archipelago server
Used by both new archipelago servers and restarting
"""
def start_server(room_id, args):
    arch_file_path = args["arch_file_path"]
    port = args["port"]
    extract_folder_path = args["extract_folder_path"]
    
    archipelago_server = subprocess.Popen(
        ["python3", ARCHIPELAGO_SERVER, arch_file_path, f"--port={port}", f"--auto_shutdown={SHUTDOWN_TIME}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
        env={**os.environ, "HOME": UPLOAD_FOLDER}
    )

    # If the subprocess failed to start, error
    time.sleep(1)
    if archipelago_server.poll() is not None:
        return {"result": 1}

    logpath = f"{extract_folder_path}/server-log.txt"

    # Separate thread to write stdout to a log file
    thread = threading.Thread(target=write_log, args=(archipelago_server, logpath, room_id))
    thread.daemon = True
    thread.start()

    processes[room_id] = archipelago_server

    return {"result": 0}

"""
Check if given room_id is currently running
"""
def is_running(room_id):
    if room_id not in processes or processes[room_id] is None:
        return {"running": False}
    if processes[room_id].poll() is None:
        return {"running": True}
    else:
        return {"running": False}

"""
Check if the given room_id currently exists in the processes 
"""
def exists(room_id):
    if room_id not in processes:
        return {"exists": False}
    else:
        return {"exists": True}

"""
Terminates the subprocess of given room id
"""
def terminate(room_id):
    if processes[room_id] is not None:
        processes[room_id].terminate()
        processes[room_id].wait()
    
    processes.pop(room_id)

"""
Puts a message in the given room's stdin
"""
def server_message(room_id, command):
    processes[room_id].stdin.write((command + '\n').encode())
    processes[room_id].stdin.flush()

"""
Terminates every room
"""
def terminate_all():
    for room_id in processes:
        if processes[room_id] is not None:
            processes[room_id].terminate()
            processes[room_id].wait()

"""
Writes the stdout of a process to a file
"""
def write_log(process, filepath, room_id):
    with open(filepath, "a") as f:
        for line in process.stdout:
            f.write(line.decode())
            f.flush()

        if room_id in processes:
            processes[room_id] = None

"""
Starts listening on TCP for connections
"""
def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        while True:
            conn, _ = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn,))
            thread.daemon = True
            thread.start()

if __name__ == "__main__":
    main()