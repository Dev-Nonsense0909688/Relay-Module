import socket
import threading

HOST = "0.0.0.0"
PORT = 2222

backend_conn = None
frontend_conn = None
lock = threading.Lock()


def pipe(src, dst):
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            dst.sendall(data)
    except:
        pass
    finally:
        src.close()
        dst.close()


def handle_connection(conn, addr):
    global backend_conn, frontend_conn

    role = conn.recv(16).decode().strip()

    with lock:
        if role == "BACKEND":
            backend_conn = conn
            print("[+] Backend connected")
        elif role == "FRONTEND":
            frontend_conn = conn
            print("[+] Frontend connected")
        else:
            conn.close()
            return

        if backend_conn and frontend_conn:
            print("[*] Tunnel established")

            threading.Thread(
                target=pipe,
                args=(backend_conn, frontend_conn),
                daemon=True
            ).start()

            threading.Thread(
                target=pipe,
                args=(frontend_conn, backend_conn),
                daemon=True
            ).start()


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(5)

print("[render] relay listening")

while True:
    conn, addr = server.accept()
    threading.Thread(
        target=handle_connection,
        args=(conn, addr),
        daemon=True
    ).start()
