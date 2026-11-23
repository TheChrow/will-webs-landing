/** Cliente de la API Will-Webs. Mismo origen en todos los entornos (el proxy enruta /api). */

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

export interface Category {
  slug: string;
  name: string;
}

export interface Service {
  id: string;
  slug: string;
  title: string;
  summary: string;
  description: string | null;
  icon: string | null;
  category: Category | null;
}

export interface Banner {
  id: string;
  title: string;
  subtitle: string | null;
  image_url: string | null;
  image_alt: string;
  cta_label: string | null;
  cta_href: string | null;
}

export interface Client {
  id: string;
  name: string;
  logo_url: string | null;
  logo_alt: string;
  website_url: string | null;
}

export interface ContentBlock {
  key: string;
  locale: string;
  title: string | null;
  body: string;
}

export type LegalType = "privacy" | "cookies" | "terms" | "accessibility";

export interface LegalDocument {
  type: LegalType;
  slug: string;
  title: string;
  version: string;
  body: string;
  published_at: string | null;
}

export interface ContactPayload {
  name: string;
  email: string;
  company?: string;
  phone?: string;
  service?: string;
  message: string;
  privacy_accepted: true;
  marketing_opt_in: boolean;
  website: string;
  elapsed_ms: number;
  captcha_token?: string;
}

/** Error con el formato Problem Details (RFC 9457) que devuelve la API. */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly retryAfter?: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { Accept: "application/json", ...init?.headers },
    credentials: "same-origin",
  });
  if (!resp.ok) {
    let title = resp.statusText;
    try {
      title = ((await resp.json()) as { title?: string }).title ?? title;
    } catch {
      /* cuerpo no JSON */
    }
    const retry = Number(resp.headers.get("Retry-After"));
    throw new ApiError(resp.status, title, Number.isFinite(retry) && retry > 0 ? retry : undefined);
  }
  return (await resp.json()) as T;
}

export const api = {
  services: () => request<Service[]>("/services"),
  banners: () => request<Banner[]>("/banners"),
  clients: () => request<Client[]>("/clients"),
  content: (prefix?: string) =>
    request<ContentBlock[]>(`/content${prefix ? `?prefix=${encodeURIComponent(prefix)}` : ""}`),
  settings: () => request<Record<string, string>>("/settings"),
  legal: (type: LegalType) => request<LegalDocument>(`/legal/${type}`),
  contact: (payload: ContactPayload) =>
    request<{ status: "accepted" }>("/contact", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
};
