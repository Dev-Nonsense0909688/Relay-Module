import socket
import threading
import os

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 2222))

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
        try:
            src.close()
        except:
            pass
        try:
            dst.close()
        except:
            pass


def handle_connection(conn, addr):
    global backend_conn, frontend_conn

    try:
        role = conn.recv(16).decode().strip()
    except:
        conn.close()
        return

    with lock:
        if role == "BACKEND":
            backend_conn = conn
            print(f"[+] Backend connected from {addr}")

        elif role == "FRONTEND":
            frontend_conn = conn
            print(f"[+] Frontend connected from {addr}")

        else:
            print(f"[!] Unknown role from {addr}")
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


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"[render] TCP relay listening on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(
            target=handle_connection,
            args=(conn, addr),
            daemon=True
        ).start()


if __name__ == "__main__":
    main()
