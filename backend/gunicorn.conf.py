from gevent import monkey # type: ignore
monkey.patch_all()

import subprocess
import time
from app import restart_all, pool
from process_manager_client import terminate_all

# Gunicorn configuration variables
workers = 3
bind = "0.0.0.0:5001"
worker_class = "gevent"

process_manager = None

def on_starting(server):
    global process_manager
    process_manager = subprocess.Popen(["python3", "process_manager.py"])
    time.sleep(1)
    restart_all()

def post_fork(server, worker):
    pool.open()

def on_exit(server):
    terminate_all()
    if process_manager:
        process_manager.terminate()
        process_manager.wait()