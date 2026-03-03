import { deleteCookie, getCookies, setCookie } from "$std/http/cookie.ts";

const TOKEN_COOKIE_NAME = "graphsql_token";
const USER_COOKIE_NAME = "graphsql_user";

export interface User {
  id: string;
  username: string;
  email?: string;
  role: string;
}

export function setAuthCookies(headers: Headers, token: string, user: User): void {
  setCookie(headers, {
    name: TOKEN_COOKIE_NAME,
    value: token,
    maxAge: 60 * 60 * 24 * 7,
    sameSite: "Lax",
    path: "/",
    secure: false,
    httpOnly: false,
  });

  setCookie(headers, {
    name: USER_COOKIE_NAME,
    value: JSON.stringify(user),
    maxAge: 60 * 60 * 24 * 7,
    sameSite: "Lax",
    path: "/",
    secure: false,
  });
}

export function getAuthToken(req: Request): string | undefined {
  return getCookies(req.headers)[TOKEN_COOKIE_NAME];
}

export function getAuthUser(req: Request): User | null {
  const userCookie = getCookies(req.headers)[USER_COOKIE_NAME];
  if (!userCookie) return null;

  try {
    return JSON.parse(userCookie);
  } catch {
    return null;
  }
}

export function clearAuthCookies(headers: Headers): void {
  deleteCookie(headers, TOKEN_COOKIE_NAME, { path: "/" });
  deleteCookie(headers, USER_COOKIE_NAME, { path: "/" });
}

export function getAuthHeaders(req: Request): HeadersInit {
  const token = getAuthToken(req);
  const headers: HeadersInit = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

export function isAuthenticated(req: Request): boolean {
  return Boolean(getAuthUser(req));
}

export function requireAuth(req: Request): User {
  const user = getAuthUser(req);
  if (!user) {
    throw new Response("Unauthorized", { status: 401 });
  }
  return user;
}
