"""
Test WebSocket functionality and security.
"""
import json

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_websocket_connection():
    """Test basic WebSocket connection."""
    client = TestClient(app)

    with client.websocket_connect("/ws/test-client") as websocket:
        # Test ping message
        websocket.send_text(json.dumps({"type": "ping"}))
        data = websocket.receive_text()
        response = json.loads(data)

        assert response["type"] == "pong"
        assert "timestamp" in response


def test_websocket_echo():
    """Test WebSocket echo functionality."""
    client = TestClient(app)

    with client.websocket_connect("/ws/test-client") as websocket:
        test_message = {"type": "echo", "data": "test message"}
        websocket.send_text(json.dumps(test_message))

        data = websocket.receive_text()
        response = json.loads(data)

        assert response["type"] == "echo_response"
        assert response["original_message"] == test_message


def test_websocket_message_size_limit():
    """Test WebSocket message size enforcement."""
    client = TestClient(app)

    with client.websocket_connect("/ws/test-client") as websocket:
        # Create message larger than 16KB
        large_message = "x" * (17 * 1024)  # 17KB
        websocket.send_text(large_message)

        data = websocket.receive_text()
        response = json.loads(data)

        assert "error" in response
        assert "Message too large" in response["error"]
        assert response["max_size_bytes"] == 16384


def test_websocket_text_message():
    """Test plain text WebSocket message handling."""
    client = TestClient(app)

    with client.websocket_connect("/ws/test-client") as websocket:
        websocket.send_text("Hello, WebSocket!")

        data = websocket.receive_text()
        response = json.loads(data)

        assert response["type"] == "text_echo"
        assert response["message"] == "Hello, WebSocket!"


def test_websocket_invalid_client_id():
    """Test WebSocket with invalid client ID."""
    client = TestClient(app)

    # Empty client ID should be rejected
    with pytest.raises(
        (ValueError, ConnectionError, RuntimeError)
    ), client.websocket_connect("/ws/"):
        pass

    # Very long client ID should be rejected
    long_id = "x" * 200
    with pytest.raises(
        (ValueError, ConnectionError, RuntimeError)
    ), client.websocket_connect(f"/ws/{long_id}"):
        pass


def test_websocket_broadcast():
    """Test WebSocket broadcast functionality."""
    client = TestClient(app)

    # Create two connections
    with client.websocket_connect("/ws/client1") as ws1, \
         client.websocket_connect("/ws/client2") as ws2:

        # Send broadcast from client1
        broadcast_msg = {
            "type": "broadcast",
            "message": "Hello everyone!"
        }
        ws1.send_text(json.dumps(broadcast_msg))

        # Client2 should receive the broadcast
        data = ws2.receive_text()
        response = json.loads(data)

        assert response["type"] == "broadcast"
        assert response["from"] == "client1"
        assert response["message"] == "Hello everyone!"


@pytest.mark.asyncio
async def test_websocket_stats_endpoint(client):
    """Test WebSocket statistics endpoint."""
    response = await client.get("/ws/stats")

    assert response.status_code == 200
    data = response.json()

    assert "total_connections" in data
    assert "connections" in data
    assert isinstance(data["total_connections"], int)
    assert isinstance(data["connections"], dict)
