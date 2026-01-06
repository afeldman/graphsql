import { Handlers, PageProps } from "$fresh/server.ts";
import { getClient } from "../lib/api.ts";
import { getAuthUser, setAuthCookies } from "../lib/auth.ts";

export const handler: Handlers = {
  async GET(req, ctx) {
    // Redirect if already logged in
    const user = getAuthUser(req);
    if (user) {
      return new Response("", {
        status: 302,
        headers: { Location: "/" },
      });
    }
    return await ctx.render();
  },

  async POST(req) {
    const form = await req.formData();
    const username = form.get("username")?.toString();
    const password = form.get("password")?.toString();

    if (!username || !password) {
      return new Response("Missing credentials", { status: 400 });
    }

    try {
      const client = getClient();
      const { token, user } = await client.login(username, password);

      const headers = new Headers();
      setAuthCookies(headers, token, user);
      headers.set("Location", "/");

      return new Response("", {
        status: 302,
        headers,
      });
    } catch (_error) {
      return await ctx.render({ error: "Invalid credentials" });
    }
  },
};

export default function Login({ data }: PageProps) {
  return (
    <div class="min-h-screen flex items-center justify-center bg-base-200">
      <div class="card w-96 bg-base-100 shadow-xl">
        <div class="card-body">
          <h2 class="card-title text-2xl font-bold text-center">
            GraphSQL Admin
          </h2>

          {data?.error && (
            <div class="alert alert-error">
              <span>{data.error}</span>
            </div>
          )}

          <form method="POST">
            <div class="form-control">
              <label class="label">
                <span class="label-text">Username</span>
              </label>
              <input
                type="text"
                name="username"
                placeholder="username"
                class="input input-bordered"
                required
                autofocus
              />
            </div>

            <div class="form-control mt-4">
              <label class="label">
                <span class="label-text">Password</span>
              </label>
              <input
                type="password"
                name="password"
                placeholder="••••••••"
                class="input input-bordered"
                required
              />
            </div>

            <div class="form-control mt-6">
              <button type="submit" class="btn btn-primary">
                Login
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
