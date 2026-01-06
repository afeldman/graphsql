import { useEffect, useState } from "preact/hooks";
import { getWebSocket, WSMessage } from "../lib/websocket.ts";

export default function LiveFeed() {
  const [messages, setMessages] = useState<WSMessage[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = getWebSocket();

    const token = document.cookie
      .split("; ")
      .find((row) => row.startsWith("graphsql_token="))
      ?.split("=")[1];

    ws.connect(token);

    const unsubscribe = ws.messages.subscribe((msgs) => {
      setMessages(msgs);
    });

    const connectedSub = ws.connected.subscribe((conn) => {
      setConnected(conn);
    });

    return () => {
      unsubscribe();
      connectedSub();
      ws.disconnect();
    };
  }, []);

  return (
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <div class="flex justify-between items-center mb-4">
          <h2 class="card-title">📡 Live Feed</h2>
          <div class={`badge ${connected ? "badge-success" : "badge-error"}`}>
            {connected ? "Connected" : "Disconnected"}
          </div>
        </div>

        <div class="overflow-y-auto max-h-96 space-y-2">
          {messages.length === 0
            ? (
              <div class="text-center text-gray-500 py-8">
                No events yet. Waiting for database changes...
              </div>
            )
            : (
              messages.slice().reverse().map((msg, idx) => (
                <div key={idx} class="alert shadow-lg">
                  <div>
                    <span
                      class={`badge badge-${msg.type === "insert"
                        ? "success"
                        : msg.type === "update"
                        ? "warning"
                        : msg.type === "delete"
                        ? "error"
                        : "info"}`}
                    >
                      {msg.type}
                    </span>
                    <span class="ml-2 font-mono text-sm">{msg.table}</span>
                    <span class="ml-2 text-xs text-gray-500">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))
            )}
        </div>

        <button
          class="btn btn-sm btn-ghost mt-4"
          onClick={() => getWebSocket().clearMessages()}
        >
          Clear
        </button>
      </div>
    </div>
  );
}
