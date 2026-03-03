import { GraphQLClient } from "graphql-request";

export interface User {
  id: string;
  username: string;
  role: string;
}

export interface GraphSQLConfig {
  baseUrl: string;
  token?: string;
}

export class GraphSQLClient {
  private baseUrl: string;
  private token?: string;
  private graphqlClient: GraphQLClient;

  constructor(config: GraphSQLConfig) {
    this.baseUrl = config.baseUrl;
    this.token = config.token;
    this.graphqlClient = new GraphQLClient(`${this.baseUrl}/graphql`, {
      headers: this.token ? { Authorization: `Bearer ${this.token}` } : {},
    });
  }

  async login(username: string, password: string): Promise<{ token: string; user: User }> {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      throw new Error("Login failed");
    }

    const data = await response.json();
    const token = data.access_token ?? data.token;
    if (!token) {
      throw new Error("Login failed: missing token");
    }

    this.token = token;
    this.graphqlClient.setHeader("Authorization", `Bearer ${token}`);

    const user = data.user ?? { id: username, username, role: data.scope ?? "default" };

    return { token, user };
  }

  async graphql<T = Record<string, unknown>>(
    query: string,
    variables?: Record<string, unknown>,
  ): Promise<T> {
    return await this.graphqlClient.request<T>(query, variables);
  }
}

let client: GraphSQLClient | null = null;

export function getClient(token?: string): GraphSQLClient {
  const baseUrl = Deno.env.get("GRAPHSQL_URL") || "http://localhost:8000";

  if (!client || token) {
    client = new GraphSQLClient({ baseUrl, token });
  }

  return client;
}
