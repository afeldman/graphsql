import { Handlers } from "$fresh/server.ts";
import { getClient } from "../../lib/api.ts";
import { clearAuthCookies, setAuthCookies } from "../../lib/auth.ts";

export const handler: Handlers = {
  async POST(req) {
    const { username, password } = await req.json();
    if (!username || !password) {
      return new Response(JSON.stringify({ error: "Missing credentials" }), { status: 400 });
    }

    try {
      const client = getClient();
      const { token, user } = await client.login(username, password);

      const headers = new Headers({ "Content-Type": "application/json" });
      setAuthCookies(headers, token, user);
      return new Response(JSON.stringify({ token, user }), { status: 200, headers });
    } catch (err) {
      return new Response(JSON.stringify({ error: (err as Error).message }), { status: 401 });
    }
  },

  async DELETE(_req) {
    const headers = new Headers();
    clearAuthCookies(headers);
    return new Response("", { status: 204, headers });
  },
};
