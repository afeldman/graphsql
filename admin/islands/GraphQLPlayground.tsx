import { useState } from "preact/hooks";
import { GraphSQLClient } from "../lib/api.ts";

interface Props {
  token?: string;
}

const sampleQuery = `query Ping { __typename }`;

export default function GraphQLPlayground({ token }: Props) {
  const [query, setQuery] = useState(sampleQuery);
  const [result, setResult] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const runQuery = async () => {
    setLoading(true);
    try {
      const client = new GraphSQLClient({ baseUrl: getBaseUrl(), token });
      const data = await client.graphql(query);
      setResult(JSON.stringify(data, null, 2));
    } catch (err) {
      setResult(`Error: ${(err as Error).message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div class="card bg-base-100 shadow-lg">
      <div class="card-body space-y-4">
        <div class="flex justify-between items-center">
          <h2 class="card-title">GraphQL Playground</h2>
          <button class={`btn btn-primary btn-sm ${loading ? "loading" : ""}`} onClick={runQuery}>
            Run
          </button>
        </div>
        <textarea
          class="textarea textarea-bordered font-mono h-40"
          value={query}
          onInput={(e) => setQuery((e.target as HTMLTextAreaElement).value)}
        />
        <pre class="bg-base-200 p-3 rounded text-sm whitespace-pre-wrap min-h-[120px]">
          {result || "Results will appear here"}
        </pre>
      </div>
    </div>
  );
}

function getBaseUrl(): string {
  const fromEnv = (globalThis as any)?.Deno?.env?.get?.("GRAPHSQL_URL");
  if (fromEnv) return fromEnv;
  const { origin } = window.location;
  return origin.replace(/\/admin$/, "") || origin;
}
