"""
WebSocket Support for DevOps Brain

Real-time updates for tasks, agents, and system events.
"""

import asyncio
import json
from datetime import datetime
from typing import Set, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect
import structlog

logger = structlog.get_logger(__name__)


class MessageType(str, Enum):
    """WebSocket message types."""
    TASK_UPDATE = "task_update"
    AGENT_STATUS = "agent_status"
    SYSTEM_EVENT = "system_event"
    NOTIFICATION = "notification"
    PING = "ping"
    PONG = "pong"


@dataclass
class WSMessage:
    """WebSocket message structure."""
    type: MessageType
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type.value,
            "payload": self.payload,
            "timestamp": self.timestamp,
        })


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.
    
    Features:
    - Connection tracking
    - Broadcast to all clients
    - Subscription-based messaging
    - Heartbeat/ping support
    """
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.subscriptions: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            self.active_connections.discard(websocket)
            # Remove from all subscriptions
            for topic in self.subscriptions:
                self.subscriptions[topic].discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def subscribe(self, websocket: WebSocket, topic: str) -> None:
        """Subscribe a connection to a topic."""
        async with self._lock:
            if topic not in self.subscriptions:
                self.subscriptions[topic] = set()
            self.subscriptions[topic].add(websocket)
        logger.debug(f"WebSocket subscribed to topic: {topic}")
    
    async def unsubscribe(self, websocket: WebSocket, topic: str) -> None:
        """Unsubscribe a connection from a topic."""
        async with self._lock:
            if topic in self.subscriptions:
                self.subscriptions[topic].discard(websocket)
    
    async def send_personal(self, websocket: WebSocket, message: WSMessage) -> None:
        """Send a message to a specific connection."""
        try:
            await websocket.send_text(message.to_json())
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            await self.disconnect(websocket)
    
    async def broadcast(self, message: WSMessage) -> None:
        """Broadcast a message to all connected clients."""
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message.to_json())
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            await self.disconnect(conn)
    
    async def broadcast_to_topic(self, topic: str, message: WSMessage) -> None:
        """Broadcast a message to all subscribers of a topic."""
        if topic not in self.subscriptions:
            return
        
        disconnected = set()
        
        for connection in self.subscriptions[topic]:
            try:
                await connection.send_text(message.to_json())
            except Exception as e:
                logger.error(f"Failed to broadcast to topic subscriber: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            await self.disconnect(conn)
    
    @property
    def connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint handler.
    
    Protocol:
    - Client sends JSON messages with {type, payload}
    - Server broadcasts updates for tasks, agents, system events
    - Supports subscriptions to specific topics
    """
    await manager.connect(websocket)
    
    # Send welcome message
    welcome = WSMessage(
        type=MessageType.SYSTEM_EVENT,
        payload={
            "event": "connected",
            "message": "Connected to DevOps Brain WebSocket",
            "connection_id": id(websocket),
        }
    )
    await manager.send_personal(websocket, welcome)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_client_message(websocket, message)
            except json.JSONDecodeError:
                error_msg = WSMessage(
                    type=MessageType.SYSTEM_EVENT,
                    payload={"error": "Invalid JSON"}
                )
                await manager.send_personal(websocket, error_msg)
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle incoming client messages."""
    msg_type = message.get("type", "")
    payload = message.get("payload", {})
    
    if msg_type == "ping":
        # Respond to ping
        pong = WSMessage(type=MessageType.PONG, payload={"echo": payload})
        await manager.send_personal(websocket, pong)
    
    elif msg_type == "subscribe":
        # Subscribe to a topic
        topic = payload.get("topic")
        if topic:
            await manager.subscribe(websocket, topic)
            ack = WSMessage(
                type=MessageType.SYSTEM_EVENT,
                payload={"event": "subscribed", "topic": topic}
            )
            await manager.send_personal(websocket, ack)
    
    elif msg_type == "unsubscribe":
        # Unsubscribe from a topic
        topic = payload.get("topic")
        if topic:
            await manager.unsubscribe(websocket, topic)
            ack = WSMessage(
                type=MessageType.SYSTEM_EVENT,
                payload={"event": "unsubscribed", "topic": topic}
            )
            await manager.send_personal(websocket, ack)


# Helper functions for broadcasting updates

async def broadcast_task_update(task_id: str, status: str, **kwargs) -> None:
    """Broadcast a task status update."""
    message = WSMessage(
        type=MessageType.TASK_UPDATE,
        payload={
            "task_id": task_id,
            "status": status,
            **kwargs
        }
    )
    await manager.broadcast(message)
    await manager.broadcast_to_topic(f"task:{task_id}", message)


async def broadcast_agent_status(agent_name: str, status: str, **kwargs) -> None:
    """Broadcast an agent status update."""
    message = WSMessage(
        type=MessageType.AGENT_STATUS,
        payload={
            "agent": agent_name,
            "status": status,
            **kwargs
        }
    )
    await manager.broadcast(message)
    await manager.broadcast_to_topic(f"agent:{agent_name}", message)


async def broadcast_notification(title: str, body: str, level: str = "info") -> None:
    """Broadcast a notification to all clients."""
    message = WSMessage(
        type=MessageType.NOTIFICATION,
        payload={
            "title": title,
            "body": body,
            "level": level,
        }
    )
    await manager.broadcast(message)


async def broadcast_system_event(event: str, data: Dict[str, Any] = None) -> None:
    """Broadcast a system event."""
    message = WSMessage(
        type=MessageType.SYSTEM_EVENT,
        payload={
            "event": event,
            "data": data or {},
        }
    )
    await manager.broadcast(message)
