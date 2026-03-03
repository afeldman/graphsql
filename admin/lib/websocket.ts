import { signal } from "@preact/signals";

export interface WSMessage {
  type: "insert" | "update" | "delete" | "ping";
  table?: string;
  data?: Record<string, unknown>;
  timestamp: number;
}

export class GraphSQLWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  public messages = signal<WSMessage[]>([]);
  public connected = signal<boolean>(false);
  public error = signal<string | null>(null);

  constructor(url: string) {
    this.url = url;
  }

  connect(token?: string): void {
    try {
      const wsUrl = new URL(this.url);
      if (token) {
        wsUrl.searchParams.set("token", token);
      }

      this.ws = new WebSocket(wsUrl.toString());

      this.ws.onopen = () => {
        console.log("WebSocket connected");
        this.connected.value = true;
        this.reconnectAttempts = 0;
        this.error.value = null;
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          this.messages.value = [...this.messages.value, message].slice(-100);
        } catch (err) {
          console.error("Failed to parse WebSocket message:", err);
        }
      };

      this.ws.onerror = (event) => {
        console.error("WebSocket error:", event);
        this.error.value = "WebSocket connection error";
      };

      this.ws.onclose = () => {
        console.log("WebSocket disconnected");
        this.connected.value = false;
        this.attemptReconnect();
      };
    } catch (err) {
      console.error("Failed to create WebSocket:", err);
      this.error.value = "Failed to create WebSocket connection";
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

      console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

      setTimeout(() => {
        this.connect();
      }, delay);
    } else {
      this.error.value = "Max reconnection attempts reached";
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.connected.value = false;
    }
  }

  send(data: Record<string, unknown>): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn("WebSocket is not connected");
    }
  }

  clearMessages(): void {
    this.messages.value = [];
  }
}

let wsClient: GraphSQLWebSocket | null = null;

export function getWebSocket(): GraphSQLWebSocket {
  if (!wsClient) {
    const baseUrl = typeof Deno !== "undefined" && Deno.env?.get
      ? Deno.env.get("GRAPHSQL_URL") || "http://localhost:8000"
      : typeof globalThis !== "undefined" && (globalThis as Record<string, unknown>).location
      ? (((globalThis as Record<string, unknown>).location as Record<string, unknown>)
        .origin as string).replace(/\/admin$/, "")
      : "http://localhost:8000";
    const wsUrl = baseUrl.replace(/^http/, "ws") + "/ws";
    wsClient = new GraphSQLWebSocket(wsUrl);
  }
  return wsClient;
}
