'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { useStore } from '@/store';

export interface WebSocketMessage {
  type: 'task_update' | 'agent_status' | 'system_event' | 'notification';
  payload: Record<string, unknown>;
  timestamp: string;
}

interface UseWebSocketOptions {
  url?: string;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    url = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options;

  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<NodeJS.Timeout>();

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  const { setConnected, updateTask, setAgents, agents } = useStore();

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnected(true);
        reconnectAttempts.current = 0;
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setConnected(false);

        // Attempt reconnection
        if (reconnect && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          console.log(`Reconnecting... (attempt ${reconnectAttempts.current})`);
          reconnectTimeout.current = setTimeout(connect, reconnectInterval);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }, [url, reconnect, reconnectInterval, maxReconnectAttempts, setConnected]);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'task_update':
        const { task_id, ...updates } = message.payload as { task_id: string; [key: string]: unknown };
        updateTask(task_id, updates);
        break;

      case 'agent_status':
        // Handle agent status updates - update the agent in the store
        const { agent: agentName, status: agentStatus, ...agentUpdates } = message.payload as { agent: string; status: string; [key: string]: unknown };
        const updatedAgents = agents.map((a) =>
          a.name === agentName
            ? { ...a, status: agentStatus as 'online' | 'busy' | 'offline', ...agentUpdates }
            : a
        );
        setAgents(updatedAgents);
        break;

      case 'system_event':
        // Handle system events
        console.log('System event:', message.payload);
        break;

      case 'notification':
        // Handle notifications (could show toast)
        console.log('Notification:', message.payload);
        break;
    }
  }, [updateTask, setAgents, agents]);

  const send = useCallback((message: Record<string, unknown>) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected');
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    send,
    connect,
    disconnect,
  };
}
