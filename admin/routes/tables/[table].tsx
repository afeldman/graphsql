import { Handlers, PageProps } from "$fresh/server.ts";
import Layout from "../../components/Layout.tsx";
import { getClient } from "../../lib/api.ts";
import { getAuthToken, requireAuth } from "../../lib/auth.ts";
import TableBrowser from "../../islands/TableBrowser.tsx";
import type { TableInfo } from "../../lib/types.ts";

interface TableDetailData {
  user: Record<string, unknown>;
  table: string;
  rows: Record<string, unknown>[];
  info: TableInfo | null;
  token?: string;
}

export const handler: Handlers<TableDetailData> = {
  async GET(req, ctx) {
    const table = ctx.params.table;
    try {
      const user = requireAuth(req);
      const token = getAuthToken(req);
      const client = getClient(token);

      const [info, records] = await Promise.all([
        client.getTableInfo(table).catch(() => null),
        client.getRecords(table, { limit: 20, offset: 0 }).catch(() => ({ data: [] })),
      ]);

      return await ctx.render({
        user,
        table,
        rows: records.data ?? records ?? [],
        info,
        token,
      });
    } catch (err) {
      console.error(err);
      return new Response("", { status: 302, headers: { Location: "/login" } });
    }
  },
};

export default function TableDetail({ data }: PageProps<TableDetailData>) {
  return (
    <Layout user={data.user}>
      <div class="p-6 space-y-6">
        <div class="card bg-base-100 shadow">
          <div class="card-body">
            <h1 class="text-3xl font-bold">{data.table}</h1>
            {data.info && (
              <div class="overflow-x-auto">
                <table class="table table-compact">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Type</th>
                      <th>Nullable</th>
                      <th>PK</th>
                      <th>Default</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.info.columns.map((col) => (
                      <tr key={col.name}>
                        <td class="font-mono text-xs">{col.name}</td>
                        <td>{col.type}</td>
                        <td>{col.nullable ? "Yes" : "No"}</td>
                        <td>{col.primary_key ? "Yes" : "No"}</td>
                        <td class="font-mono text-xs">{col.default ?? ""}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        <TableBrowser table={data.table} initialRows={data.rows} token={data.token} />
      </div>
    </Layout>
  );
}
