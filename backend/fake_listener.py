import socket
import threading

HOST = "localhost"
PORT = 38280

def handle_connection(conn):
    with conn:
        pass

"""
Starts listening on TCP for connections
"""
def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        while True:
            conn, _ = server.accept()
            thread = threading.Thread(target=handle_connection, args=(conn,))
            thread.daemon = True
            thread.start()

if __name__ == "__main__":
    main()