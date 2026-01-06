import { Handlers, PageProps } from "$fresh/server.ts";
import Layout from "../../components/Layout.tsx";
import LiveFeed from "../../islands/LiveFeed.tsx";
import { requireAuth } from "../../lib/auth.ts";

interface MonitoringData {
  user: Record<string, unknown>;
}

export const handler: Handlers<MonitoringData> = {
  GET(req, ctx) {
    try {
      const user = requireAuth(req);
      return ctx.render({ user });
    } catch {
      return new Response("", { status: 302, headers: { Location: "/login" } });
    }
  },
};

export default function MonitoringPage({ data }: PageProps<MonitoringData>) {
  return (
    <Layout user={data.user}>
      <div class="p-6 space-y-6">
        <h1 class="text-3xl font-bold">Monitoring</h1>
        <LiveFeed />
      </div>
    </Layout>
  );
}
