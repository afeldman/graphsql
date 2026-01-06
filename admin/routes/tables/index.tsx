import { Handlers, PageProps } from "$fresh/server.ts";
import Layout from "../../components/Layout.tsx";
import { getClient } from "../../lib/api.ts";
import { getAuthToken, requireAuth } from "../../lib/auth.ts";
import GraphQLPlayground from "../../islands/GraphQLPlayground.tsx";

interface TablesPageData {
  user: any;
  tables: string[];
  view: string;
  token?: string;
}

export const handler: Handlers<TablesPageData> = {
  async GET(req, ctx) {
    try {
      const user = requireAuth(req);
      const token = getAuthToken(req);
      const view = new URL(req.url).searchParams.get("view") ?? "list";
      const client = getClient(token);
      const tables = await client.listTables();
      return await ctx.render({ user, tables, view, token });
    } catch (err) {
      console.error(err);
      return new Response("", { status: 302, headers: { Location: "/login" } });
    }
  },
};

export default function TablesPage({ data }: PageProps<TablesPageData>) {
  return (
    <Layout user={data.user}>
      <div class="p-6 space-y-4">
        <div class="flex justify-between items-center">
          <h1 class="text-3xl font-bold">Tables</h1>
          <div class="join">
            <a href="/tables" class={`btn join-item ${data.view === "list" ? "btn-primary" : "btn-ghost"}`}>
              List
            </a>
            <a href="/tables?view=graphql" class={`btn join-item ${data.view === "graphql" ? "btn-primary" : "btn-ghost"}`}>
              GraphQL
            </a>
          </div>
        </div>

        {data.view === "graphql"
          ? (
            <div class="grid grid-cols-1 gap-4">
              <div class="alert alert-info text-sm">
                Authenticated GraphQL requests are proxied to the GraphSQL backend. Adjust the query and run.
              </div>
              <GraphQLPlayground token={data.token} />
            </div>
          )
          : (
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.tables.map((table) => (
                <a key={table} href={`/tables/${table}`} class="card bg-base-100 shadow hover:shadow-lg">
                  <div class="card-body">
                    <h2 class="card-title font-mono">{table}</h2>
                    <p class="text-sm text-base-content/70">View records and schema</p>
                  </div>
                </a>
              ))}
            </div>
          )}
      </div>
    </Layout>
  );
}
