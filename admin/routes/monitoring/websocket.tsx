import { Handlers, PageProps } from "$fresh/server.ts";
import Layout from "../../components/Layout.tsx";
import { requireAuth, getAuthUser } from "../../lib/auth.ts";

interface Data {
  user: any;
}

export const handler: Handlers<Data> = {
  GET(req, ctx) {
    try {
      const user = requireAuth(req);
      return ctx.render({ user });
    } catch {
      return new Response("", { status: 302, headers: { Location: "/login" } });
    }
  },
};

export default function WebSocketMonitoring({ data }: PageProps<Data>) {
  return (
    <Layout user={data.user}>
      <div class="p-6 space-y-4">
        <h1 class="text-3xl font-bold">WebSocket Monitoring</h1>
        <div class="card bg-base-100 shadow">
          <div class="card-body space-y-2">
            <p class="text-base-content/70">
              WebSocket endpoint: <span class="font-mono">/ws</span>
            </p>
            <p class="text-sm text-base-content/60">
              Connections authenticate with the token query param when auth is enabled.
            </p>
            <a class="btn btn-outline btn-sm" href="/monitoring">Back to Live Feed</a>
          </div>
        </div>
      </div>
    </Layout>
  );
}
