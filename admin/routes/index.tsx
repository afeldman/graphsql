import { Handlers, PageProps } from "$fresh/server.ts";
import { getAuthToken, requireAuth } from "../lib/auth.ts";
import { getClient } from "../lib/api.ts";
import Layout from "../components/Layout.tsx";
import StatsCard from "../components/StatsCard.tsx";

interface DashboardData {
  user: Record<string, unknown>;
  stats: Record<string, unknown>;
  tables: string[];
  health: Record<string, unknown>;
}

export const handler: Handlers<DashboardData> = {
  async GET(req, ctx) {
    try {
      const user = requireAuth(req);
      const token = getAuthToken(req);
      const client = getClient(token);

      const [stats, tables, health] = await Promise.all([
        client.getStats(),
        client.listTables(),
        client.getHealth(),
      ]);

      return await ctx.render({ user, stats, tables, health });
    } catch (_error) {
      return new Response("", {
        status: 302,
        headers: { Location: "/login" },
      });
    }
  },
};

export default function Dashboard({ data }: PageProps<DashboardData>) {
  return (
    <Layout user={data.user}>
      <div class="p-6">
        <h1 class="text-3xl font-bold mb-6">Dashboard</h1>

        {/* Stats Grid */}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatsCard
            title="Tables"
            value={data.tables.length}
            icon="📊"
            color="bg-blue-500"
          />
          <StatsCard
            title="Total Records"
            value={data.stats?.total_records || 0}
            icon="📝"
            color="bg-green-500"
          />
          <StatsCard
            title="API Calls"
            value={data.stats?.api_calls || 0}
            icon="🔌"
            color="bg-purple-500"
          />
          <StatsCard
            title="Status"
            value={data.health?.status || "Unknown"}
            icon={data.health?.status === "healthy" ? "✅" : "⚠️"}
            color={data.health?.status === "healthy" ? "bg-green-500" : "bg-yellow-500"}
          />
        </div>

        {/* Quick Actions */}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <a href="/tables" class="card bg-base-100 shadow-xl hover:shadow-2xl transition-shadow">
            <div class="card-body">
              <h2 class="card-title">📊 Browse Tables</h2>
              <p>View and manage all database tables</p>
            </div>
          </a>

          <a
            href="/tables?view=graphql"
            class="card bg-base-100 shadow-xl hover:shadow-2xl transition-shadow"
          >
            <div class="card-body">
              <h2 class="card-title">🎮 GraphQL Playground</h2>
              <p>Execute GraphQL queries</p>
            </div>
          </a>

          <a
            href="/monitoring"
            class="card bg-base-100 shadow-xl hover:shadow-2xl transition-shadow"
          >
            <div class="card-body">
              <h2 class="card-title">📈 Monitoring</h2>
              <p>Real-time system monitoring</p>
            </div>
          </a>
        </div>

        {/* Recent Tables */}
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <h2 class="card-title mb-4">Recent Tables</h2>
            <div class="overflow-x-auto">
              <table class="table table-zebra">
                <thead>
                  <tr>
                    <th>Table Name</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data.tables.slice(0, 10).map((table) => (
                    <tr key={table}>
                      <td>
                        <span class="font-mono">{table}</span>
                      </td>
                      <td>
                        <div class="flex gap-2">
                          <a href={`/tables/${table}`} class="btn btn-sm btn-primary">
                            View
                          </a>
                          <a href={`/tables/${table}?action=edit`} class="btn btn-sm btn-secondary">
                            Edit
                          </a>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
