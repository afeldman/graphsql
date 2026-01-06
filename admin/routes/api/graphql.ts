import { Handlers } from "$fresh/server.ts";
import { getClient } from "../../lib/api.ts";
import { getAuthToken } from "../../lib/auth.ts";

export const handler: Handlers = {
  async POST(req) {
    const raw = await req.text();
    const body = JSON.parse(raw || "{}");
    const token = getAuthToken(req);
    const client = getClient(token ?? undefined);

    try {
      const json = await client.graphql(body.query, body.variables);
      return new Response(JSON.stringify(json), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    } catch (err) {
      return new Response(JSON.stringify({ error: (err as Error).message }), { status: 500 });
    }
  },
};
