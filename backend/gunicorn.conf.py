import subprocess
import time
from app import restart_all
from process_manager_client import terminate_all

# Gunicorn configuration variables
workers = 3
bind = "0.0.0.0:5001"

process_manager = None

def when_ready(server):
    restart_all()

def on_starting(server):
    global process_manager
    process_manager = subprocess.Popen(["python3", "process_manager.py"])
    time.sleep(1)

def on_exit(server):
    terminate_all()
    if process_manager:
        process_manager.terminate()
        process_manager.wait()