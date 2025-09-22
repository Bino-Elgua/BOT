"""
WebSocket router with 16KB message size enforcement.
Provides secure WebSocket communication with rate limiting and message validation.
"""
import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.rate_limiter import rate_limiter
from core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections with security and monitoring."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        """
        Accept WebSocket connection with validation.

        Args:
            websocket: WebSocket instance
            client_id: Unique client identifier

        Returns:
            bool: True if connection accepted
        """
        try:
            # Check rate limiting
            rate_check = await rate_limiter.is_allowed(f"ws_connect:{client_id}")
            if not rate_check["allowed"]:
                logger.warning(f"WebSocket connection rate limited for {client_id}")
                await websocket.close(code=4008, reason="Rate limit exceeded")
                return False

            await websocket.accept()

            # Store connection
            self.active_connections[client_id] = websocket
            self.connection_metadata[client_id] = {
                "connected_at": time.time(),
                "messages_sent": 0,
                "messages_received": 0,
                "bytes_sent": 0,
                "bytes_received": 0,
                "last_activity": time.time()
            }

            logger.info(f"WebSocket connection established for {client_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to establish WebSocket connection for {client_id}: {e}"
            )
            return False

    def disconnect(self, client_id: str):
        """Disconnect and cleanup client."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        if client_id in self.connection_metadata:
            metadata = self.connection_metadata[client_id]
            duration = time.time() - metadata["connected_at"]
            logger.info(
                f"WebSocket disconnected for {client_id}. "
                f"Duration: {duration:.2f}s, "
                f"Messages: {metadata['messages_received']}/"
                f"{metadata['messages_sent']}, "
                f"Bytes: {metadata['bytes_received']}/{metadata['bytes_sent']}"
            )
            del self.connection_metadata[client_id]

    async def send_personal_message(self, message: str, client_id: str) -> bool:
        """
        Send message to specific client.

        Args:
            message: Message to send
            client_id: Target client ID

        Returns:
            bool: True if message sent successfully
        """
        try:
            if client_id not in self.active_connections:
                return False

            websocket = self.active_connections[client_id]

            # Check message size
            message_bytes = len(message.encode('utf-8'))
            settings = get_settings()

            if message_bytes > settings.websocket_max_message_size:
                logger.warning(
                    f"Outgoing message too large for {client_id}: "
                    f"{message_bytes} > {settings.websocket_max_message_size} bytes"
                )
                await websocket.send_text(json.dumps({
                    "error": "Message too large",
                    "max_size": settings.websocket_max_message_size
                }))
                return False

            await websocket.send_text(message)

            # Update metrics
            if client_id in self.connection_metadata:
                metadata = self.connection_metadata[client_id]
                metadata["messages_sent"] += 1
                metadata["bytes_sent"] += message_bytes
                metadata["last_activity"] = time.time()

            return True

        except Exception as e:
            logger.error(f"Failed to send message to {client_id}: {e}")
            self.disconnect(client_id)
            return False

    async def broadcast(self, message: str, exclude_client: Optional[str] = None):
        """
        Broadcast message to all connected clients.

        Args:
            message: Message to broadcast
            exclude_client: Client ID to exclude from broadcast
        """
        disconnected_clients = []

        for client_id, _websocket in self.active_connections.items():
            if exclude_client and client_id == exclude_client:
                continue

            try:
                success = await self.send_personal_message(message, client_id)
                if not success:
                    disconnected_clients.append(client_id)
            except Exception as e:
                logger.error(f"Broadcast failed for {client_id}: {e}")
                disconnected_clients.append(client_id)

        # Cleanup disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": len(self.active_connections),
            "connections": {
                client_id: {
                    **metadata,
                    "connected_duration": time.time() - metadata["connected_at"]
                }
                for client_id, metadata in self.connection_metadata.items()
            }
        }


# Global connection manager
manager = ConnectionManager()


@router.websocket("/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint with 16KB message size enforcement and rate limiting.

    Args:
        websocket: WebSocket connection
        client_id: Unique client identifier
    """
    settings = get_settings()

    # Validate client_id
    if not client_id or len(client_id) > 100:
        await websocket.close(code=4000, reason="Invalid client ID")
        return

    # Establish connection
    connected = await manager.connect(websocket, client_id)
    if not connected:
        return

    try:
        while True:
            # Receive message with size check
            try:
                # Use receive_bytes to check size before text conversion
                data = await websocket.receive()

                if data["type"] == "websocket.disconnect":
                    break

                if data["type"] == "websocket.receive":
                    if "bytes" in data:
                        message_bytes = data["bytes"]
                    elif "text" in data:
                        message_bytes = data["text"].encode('utf-8')
                    else:
                        continue

                    # Check message size
                    if len(message_bytes) > settings.websocket_max_message_size:
                        logger.warning(
                            f"Message too large from {client_id}: "
                            f"{len(message_bytes)} > "
                            f"{settings.websocket_max_message_size} bytes"
                        )

                        await websocket.send_text(json.dumps({
                            "error": "Message too large",
                            "max_size_bytes": settings.websocket_max_message_size,
                            "received_size_bytes": len(message_bytes)
                        }))
                        continue

                    # Convert to text if received as bytes
                    if isinstance(message_bytes, bytes):
                        message_text = message_bytes.decode('utf-8')
                    else:
                        message_text = message_bytes

                    # Rate limiting check
                    rate_check = await rate_limiter.is_allowed(
                        f"ws_message:{client_id}"
                    )
                    if not rate_check["allowed"]:
                        await websocket.send_text(json.dumps({
                            "error": "Rate limit exceeded",
                            "retry_after": rate_check["reset_time"] - time.time()
                        }))
                        continue

                    # Update receive metrics
                    if client_id in manager.connection_metadata:
                        metadata = manager.connection_metadata[client_id]
                        metadata["messages_received"] += 1
                        metadata["bytes_received"] += len(message_bytes)
                        metadata["last_activity"] = time.time()

                    # Process message
                    try:
                        # Try to parse as JSON
                        message_data = json.loads(message_text)
                        await handle_message(client_id, message_data)
                    except json.JSONDecodeError:
                        # Handle as plain text
                        await handle_text_message(client_id, message_text)

            except asyncio.TimeoutError:
                # Send ping to check connection
                await websocket.ping()

    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
    finally:
        manager.disconnect(client_id)


async def handle_message(client_id: str, message_data: Dict[str, Any]):
    """
    Handle structured JSON message.

    Args:
        client_id: Client identifier
        message_data: Parsed JSON message
    """
    try:
        message_type = message_data.get("type", "unknown")

        if message_type == "ping":
            # Respond to ping
            await manager.send_personal_message(
                json.dumps({"type": "pong", "timestamp": time.time()}),
                client_id
            )

        elif message_type == "echo":
            # Echo message back
            response = {
                "type": "echo_response",
                "original_message": message_data,
                "timestamp": time.time()
            }
            await manager.send_personal_message(json.dumps(response), client_id)

        elif message_type == "broadcast":
            # Broadcast to all clients
            if "message" in message_data:
                broadcast_msg = json.dumps({
                    "type": "broadcast",
                    "from": client_id,
                    "message": message_data["message"],
                    "timestamp": time.time()
                })
                await manager.broadcast(broadcast_msg, exclude_client=client_id)

        else:
            # Unknown message type
            await manager.send_personal_message(
                json.dumps({
                    "error": f"Unknown message type: {message_type}",
                    "supported_types": ["ping", "echo", "broadcast"]
                }),
                client_id
            )

    except Exception as e:
        logger.error(f"Error handling message from {client_id}: {e}")
        await manager.send_personal_message(
            json.dumps({"error": "Failed to process message"}),
            client_id
        )


async def handle_text_message(client_id: str, message_text: str):
    """
    Handle plain text message.

    Args:
        client_id: Client identifier
        message_text: Plain text message
    """
    # Simple echo for text messages
    response = json.dumps({
        "type": "text_echo",
        "message": message_text,
        "from": client_id,
        "timestamp": time.time()
    })
    await manager.send_personal_message(response, client_id)


@router.get("/stats")
async def get_websocket_stats() -> Dict[str, Any]:
    """Get WebSocket connection statistics."""
    return manager.get_connection_stats()
