import { Handlers, PageProps } from "$fresh/server.ts";
import Layout from "../../components/Layout.tsx";
import { requireAuth } from "../../lib/auth.ts";

interface SettingsData {
  user: Record<string, unknown>;
  config: Record<string, string | number | boolean>;
}

export const handler: Handlers<SettingsData> = {
  GET(req, ctx) {
    try {
      const user = requireAuth(req);
      const config = {
        apiBase: Deno.env.get("GRAPHSQL_URL") ?? "http://localhost:8000",
        deployTarget: Deno.env.get("DENO_REGION") ?? "local",
      };
      return ctx.render({ user, config });
    } catch {
      return new Response("", { status: 302, headers: { Location: "/login" } });
    }
  },
};

export default function SettingsPage({ data }: PageProps<SettingsData>) {
  return (
    <Layout user={data.user}>
      <div class="p-6 space-y-4">
        <h1 class="text-3xl font-bold">Settings</h1>
        <div class="card bg-base-100 shadow">
          <div class="card-body">
            <h2 class="card-title">Deployment</h2>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span>API Base</span>
                <span class="font-mono">{data.config.apiBase}</span>
              </div>
              <div class="flex justify-between">
                <span>Region</span>
                <span class="font-mono">{data.config.deployTarget}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
