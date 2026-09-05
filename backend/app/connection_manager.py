from fastapi import WebSocket

from app.tripcode import Identity


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[WebSocket, Identity] = {}

    def register(self, websocket: WebSocket, identity: Identity) -> None:
        self.active_connections[websocket] = identity

    def unregister(self, websocket: WebSocket) -> None:
        self.active_connections.pop(websocket, None)

    async def broadcast(self, message: dict) -> None:
        for connection in list(self.active_connections):
            await connection.send_json(message)


manager = ConnectionManager()
