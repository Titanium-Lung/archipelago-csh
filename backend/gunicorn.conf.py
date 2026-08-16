from gevent import monkey # type: ignore
monkey.patch_all()

import subprocess
import time
from app import restart_all, pool, apply_migrations
from process_manager_client import terminate_all

# Gunicorn configuration variables
workers = 3
bind = "0.0.0.0:5001"
worker_class = "gevent"
control_socket_disable = True

process_manager = None
fake_listener = None

def on_starting(server):
    global process_manager, fake_listener
    fake_listener = subprocess.Popen(["python3", "fake_listener.py"])
    process_manager = subprocess.Popen(["python3", "process_manager.py"])
    time.sleep(1)
    apply_migrations()
    restart_all()

def post_fork(server, worker):
    pool.open()

def on_exit(server):
    terminate_all()
    if process_manager:
        process_manager.terminate()
        process_manager.wait()
    if fake_listener:
        fake_listener.terminate()
        fake_listener.wait()