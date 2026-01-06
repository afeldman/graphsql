import { useEffect, useState } from "preact/hooks";
import { GraphSQLClient } from "../lib/api.ts";
import TableView from "../components/TableView.tsx";

interface TableBrowserProps {
  table: string;
  initialRows: Record<string, unknown>[];
  token?: string;
}

export default function TableBrowser({ table, initialRows, token }: TableBrowserProps) {
  const [rows, setRows] = useState(initialRows);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // no-op initial
  }, []);

  const refresh = async () => {
    try {
      setLoading(true);
      setError(null);
      const client = new GraphSQLClient({
        baseUrl: getBaseUrl(),
        token,
      });
      const data = await client.getRecords(table, { limit: 50, offset: 0 });
      setRows(data.data ?? data ?? []);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div class="space-y-4">
      <div class="flex justify-between items-center">
        <h2 class="text-2xl font-bold">Table: {table}</h2>
        <button
          type="button"
          class={`btn btn-sm ${loading ? "loading" : "btn-outline"}`}
          onClick={refresh}
        >
          Refresh
        </button>
      </div>
      {error && <div class="alert alert-error">{error}</div>}
      <TableView table={table} rows={rows} />
    </div>
  );
}

function getBaseUrl(): string {
  const fromEnv = (globalThis as Record<string, unknown>)?.Deno?.env?.get?.("GRAPHSQL_URL");
  if (fromEnv) return fromEnv;
  const { origin } = globalThis.location as { origin: string };
  return origin.replace(/\/admin$/, "") || origin;
}
