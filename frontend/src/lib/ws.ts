import { useEffect, useRef, useState } from "react";
import type { TelemetryReading } from "./types";

const WS_URL = () => {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${window.location.host}/ws/telemetry`;
};

export type ConnectionState = "connecting" | "open" | "closed" | "error";

export function useTelemetryStream() {
  const [latest, setLatest] = useState<TelemetryReading | null>(null);
  const [history, setHistory] = useState<TelemetryReading[]>([]);
  const [connectionState, setConnectionState] = useState<ConnectionState>("connecting");
  // Wall-clock time this client actually received the last reading -- used for staleness
  // detection instead of the payload's `timestamp` field, which (in scripted demo mode)
  // holds a fixed simulated time once the scenario reaches its final stage and stops
  // advancing, so it does not reflect whether readings are still actually arriving.
  const [lastReceivedAt, setLastReceivedAt] = useState<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<number | null>(null);

  useEffect(() => {
    let cancelled = false;

    function connect() {
      if (cancelled) return;
      setConnectionState("connecting");
      const ws = new WebSocket(WS_URL());
      wsRef.current = ws;

      ws.onopen = () => setConnectionState("open");

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "status") return; // heartbeat, not a telemetry reading
          setLatest(data as TelemetryReading);
          setLastReceivedAt(Date.now());
          setHistory((prev) => [...prev.slice(-59), data as TelemetryReading]);
        } catch {
          // ignore malformed frame
        }
      };

      ws.onerror = () => setConnectionState("error");

      ws.onclose = () => {
        setConnectionState("closed");
        if (!cancelled) {
          reconnectTimer.current = window.setTimeout(connect, 2000);
        }
      };
    }

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimer.current) window.clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, []);

  return { latest, history, connectionState, lastReceivedAt };
}
