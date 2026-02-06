import asyncio
import websockets
import os

PORT = int(os.environ.get("PORT", 8000))

backend = None
frontend = None


async def process_request(path, request_headers):
    # Handle Render health checks (HEAD / GET without websocket upgrade)
    if request_headers.get("Upgrade", "").lower() != "websocket":
        return 200, [], b"OK"


async def handler(ws, path):
    global backend, frontend

    role = await ws.recv()

    if role == "BACKEND":
        backend = ws
        print("[+] Backend connected")

    elif role == "FRONTEND":
        frontend = ws
        print("[+] Frontend connected")

    else:
        await ws.close()
        return

    if backend and frontend:
        print("[*] Tunnel established")

        async def pipe(src, dst):
            try:
                async for msg in src:
                    await dst.send(msg)
            except:
                pass

        await asyncio.gather(
            pipe(backend, frontend),
            pipe(frontend, backend),
        )


async def main():
    async with websockets.serve(
        handler,
        "0.0.0.0",
        PORT,
        process_request=process_request,
    ):
        print(f"[render] WebSocket relay listening on {PORT}")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
