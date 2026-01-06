import { Handlers } from "$fresh/server.ts";
import { clearAuthCookies } from "../lib/auth.ts";

export const handler: Handlers = {
  GET() {
    const headers = new Headers({ Location: "/login" });
    clearAuthCookies(headers);
    return new Response("", { status: 302, headers });
  },
};
