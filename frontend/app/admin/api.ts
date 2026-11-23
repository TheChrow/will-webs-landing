/**
 * Cliente del API admin.
 * - Access token (JWT, 15 min) solo en memoria: nunca en localStorage (mitiga robo por XSS).
 * - Refresh token en cookie HttpOnly; se renueva automáticamente ante un 401.
 */
import { ApiError } from "~/lib/api";

const BASE = "/api/v1/admin";

export interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
}

interface TokenResponse {
  access_token: string;
  expires_in: number;
  user: AdminUser;
}

let accessToken: string | null = null;
let refreshing: Promise<AdminUser | null> | null = null;
let onSessionLost: (() => void) | null = null;

export function setSessionLostHandler(fn: (() => void) | null) {
  onSessionLost = fn;
}

async function parseError(resp: Response): Promise<ApiError> {
  let title = resp.statusText;
  try {
    const body = (await resp.json()) as { title?: string; errors?: { msg: string }[] };
    title = body.errors?.map((e) => e.msg).join("; ") || body.title || title;
  } catch {
    /* sin cuerpo JSON */
  }
  return new ApiError(resp.status, title);
}

async function tokenRequest(path: string, body?: unknown): Promise<AdminUser> {
  const resp = await fetch(`${BASE}/auth/${path}`, {
    method: "POST",
    credentials: "same-origin",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!resp.ok) throw await parseError(resp);
  const data = (await resp.json()) as TokenResponse;
  accessToken = data.access_token;
  return data.user;
}

export const login = (email: string, password: string) =>
  tokenRequest("login", { email, password });

/** Restaura/renueva la sesión con la cookie. Deduplica llamadas concurrentes. */
export function refreshSession(): Promise<AdminUser | null> {
  refreshing ??= tokenRequest("refresh")
    .catch(() => {
      accessToken = null;
      return null;
    })
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
}

export async function logout() {
  accessToken = null;
  await fetch(`${BASE}/auth/logout`, { method: "POST", credentials: "same-origin" });
}

export async function adminFetch<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(init.headers);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  if (init.body) headers.set("Content-Type", "application/json");
  const resp = await fetch(`${BASE}${path}`, { ...init, headers, credentials: "same-origin" });

  if (resp.status === 401 && retry) {
    const user = await refreshSession();
    if (user) return adminFetch<T>(path, init, false);
    onSessionLost?.();
  }
  if (!resp.ok) throw await parseError(resp);
  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

export const adminApi = {
  get: <T>(path: string) => adminFetch<T>(path),
  post: <T>(path: string, body?: unknown) =>
    adminFetch<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    adminFetch<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) =>
    adminFetch<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  del: (path: string) => adminFetch<void>(path, { method: "DELETE" }),
};

// ---- Tipos de respuesta ----
export type LeadStatus = "new" | "read" | "contacted" | "archived" | "spam";

export interface Lead {
  id: string;
  name: string;
  email: string;
  company: string | null;
  phone: string | null;
  service: string | null;
  message: string | null;
  status: LeadStatus;
  created_at: string;
  retention_until: string;
  anonymized_at: string | null;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface AdminService {
  id: string;
  slug: string;
  title: string;
  summary: string;
  description: string | null;
  icon: string | null;
  category: string | null;
  sort_order: number;
  is_published: boolean;
  updated_at: string;
}

export interface AdminContentBlock {
  key: string;
  locale: string;
  title: string | null;
  body: string;
  is_published: boolean;
  updated_at: string;
}

export interface LegalVersion {
  version: string;
  is_current: boolean;
  published_at: string | null;
  created_at: string;
  body: string | null;
}

export interface LegalDoc {
  type: "privacy" | "cookies" | "terms" | "accessibility";
  slug: string;
  title: string;
  versions: LegalVersion[];
}

export interface AuditEntry {
  action: string;
  entity: string;
  entity_id: string | null;
  actor: string | null;
  diff: Record<string, unknown> | null;
  created_at: string;
}
