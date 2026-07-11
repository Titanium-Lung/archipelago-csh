from app import restart_all, cleanup, db_connection

workers = 1
bind = "0.0.0.0:5001"

def when_ready(server):
    restart_all()

def on_exit(server):
    cleanup()

def post_fork(server, worker):
    db_connection()