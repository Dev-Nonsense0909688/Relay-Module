import socket, threading
from cryptography.fernet import Fernet

KEY = b'K91As-ZkDmIb5fKxD9cem6pOPxUnqApLJTpluzN63dQ='
cipher = Fernet(KEY)

clients = []

def handle(conn):
    clients.append(conn)
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            decrypted = cipher.decrypt(data)
            for c in clients:
                if c != conn:
                    c.sendall(cipher.encrypt(decrypted))
    finally:
        clients.remove(conn)
        conn.close()

s = socket.socket()
s.bind(("0.0.0.0", 10000))
s.listen()

while True:
    conn, _ = s.accept()
    threading.Thread(target=handle, args=(conn,), daemon=True).start()
