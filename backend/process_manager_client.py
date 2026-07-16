"""
Client that Flask workers use to communicate with the process_manager subprocess (through TCP)
"""

import socket
import json

HOST = "localhost"
PORT = 6000

"""
Sends a message through TCP to the listening process_manager subprocess
"""
def send_message(message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(json.dumps(message).encode())
        response = s.recv(4096).decode()
        return json.loads(response)

def start_server(room_id, args):
    return send_message({"action": "start", "room_id": room_id, "args": args})

def send_command(room_id, command):
    return send_message({"action": "send_command", "room_id": room_id, "command": command})

def is_running(room_id):
    return send_message({"action": "is_running", "room_id": room_id})

def exists(room_id):
    return send_message({"action": "exists", "room_id": room_id})

def terminate(room_id):
     return send_message({"action": "terminate", "room_id": room_id})

def terminate_all():
     return send_message({"action": "terminate_all"})