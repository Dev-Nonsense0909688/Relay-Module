
import os
import socket
import threading
import struct
import traceback
from cryptography.fernet import Fernet, InvalidToken

# ================= CONFIG =================
KEY = b'K91As-ZkDmIb5fKxD9cem6pOPxUnqApLJTpluzN63dQ='
cipher = Fernet(KEY)

PORT = int(os.environ.get("PORT", 10000))
MAX_MSG_SIZE = 64 * 1024  # 64 KB safety cap
# ==========================================

clients = []
clients_lock = threading.Lock()


def log(msg):
    print(f"[RELAY] {msg}", flush=True)


def recv_exact(conn, n):
    """Receive exactly n bytes or return None if connection drops"""
    data = b""
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def handle_client(conn, addr):
    log(f"Client connected: {addr}")

    with clients_lock:
        clients.append(conn)

    try:
        while True:
            # ---- read length prefix ----
            raw_len = recv_exact(conn, 4)
            if not raw_len:
                log(f"{addr} disconnected (no length)")
                break

            msg_len = struct.unpack("!I", raw_len)[0]

            if msg_len <= 0 or msg_len > MAX_MSG_SIZE:
                log(f"{addr} sent invalid size: {msg_len}")
                break

            # ---- read encrypted payload ----
            encrypted = recv_exact(conn, msg_len)
            if not encrypted:
                log(f"{addr} disconnected mid-packet")
                break

            # ---- decrypt safely ----
            try:
                plaintext = cipher.decrypt(encrypted)
            except InvalidToken:
                log(f"{addr} sent INVALID TOKEN (wrong key / corrupted data)")
                continue
            except Exception as e:
                log(f"{addr} decrypt error: {e}")
                continue

            log(f"{addr} -> {len(plaintext)} bytes")

            # ---- broadcast ----
            with clients_lock:
                for c in clients:
                    if c is not conn:
                        try:
                            out = cipher.encrypt(plaintext)
                            c.sendall(struct.pack("!I", len(out)) + out)
                        except Exception as e:
                            log(f"Send error, dropping client: {e}")
                            clients.remove(c)
                            c.close()

    except Exception:
        log(f"Unhandled error with {addr}")
        traceback.print_exc()

    finally:
        with clients_lock:
            if conn in clients:
                clients.remove(conn)
        conn.close()
        log(f"Client closed: {addr}")


def main():
    log("Starting relay server")
    log(f"Listening on port {PORT}")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", PORT))
    s.listen()

    while True:
        conn, addr = s.accept()
        t = threading.Thread(
            target=handle_client,
            args=(conn, addr),
            daemon=True
        )
        t.start()


if __name__ == "__main__":
    main()
