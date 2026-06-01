import { useEffect, useRef, useState } from 'react';

import { useAuthStore } from '../store/authStore';
import { getWsBaseUrl } from '../utils/apiUrl';

export interface UseSubmissionSocketResult {
  verdict: string;
  status: string;
  timeMs: number | null;
  memoryKb: number | null;
  isConnected: boolean;
}

export default function useSubmissionSocket(submissionId: number | null): UseSubmissionSocketResult {
  const [verdict, setVerdict] = useState<string>('');
  const [status, setStatus] = useState<string>('');
  const [timeMs, setTimeMs] = useState<number | null>(null);
  const [memoryKb, setMemoryKb] = useState<number | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);

  const token = useAuthStore((s) => s.accessToken);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectDelayRef = useRef<number>(1000);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const pingIntervalRef = useRef<number | null>(null);

  // Reset states when submissionId changes
  useEffect(() => {
    if (submissionId) {
      setVerdict('');
      setStatus('');
      setTimeMs(null);
      setMemoryKb(null);
    }
  }, [submissionId]);

  useEffect(() => {
    if (!submissionId) {
      if (socketRef.current) {
        socketRef.current.close();
      }
      setIsConnected(false);
      return;
    }

    const connect = () => {
      if (socketRef.current) {
        socketRef.current.close();
      }

      const params = token ? `?${new URLSearchParams({ token })}` : '';
      const wsUrl = `${getWsBaseUrl()}/ws/submissions/${submissionId}/${params}`;
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        setIsConnected(true);
        reconnectDelayRef.current = 1000; // Reset reconnect delay on successful connection

        // Start ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
        }
        pingIntervalRef.current = window.setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'verdict') {
            setVerdict(data.verdict || '');
            setStatus(data.status || '');
            setTimeMs(data.time_ms !== undefined ? data.time_ms : null);
            setMemoryKb(data.memory_kb !== undefined ? data.memory_kb : null);
          } else if (data.type === 'pong') {
            // Heartbeat pong received successfully
          }
        } catch (err) {
          console.error('Error parsing WS message:', err);
        }
      };

      socket.onclose = () => {
        setIsConnected(false);
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }

        // Only reconnect if submissionId is still active
        if (submissionId) {
          const nextDelay = reconnectDelayRef.current;
          reconnectDelayRef.current = Math.min(reconnectDelayRef.current * 2, 16000);
          reconnectTimeoutRef.current = window.setTimeout(() => {
            connect();
          }, nextDelay);
        }
      };

      socket.onerror = (err) => {
        console.error('WS Error:', err);
        socket.close();
      };
    };

    connect();

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
    };
  }, [submissionId, token]);

  return { verdict, status, timeMs, memoryKb, isConnected };
}
