import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { adminApi, login, setSessionLostHandler } from "./api";

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

const tokenResp = (token: string) =>
  json({ access_token: token, expires_in: 900, user: { id: "u", email: "a@b.cl", full_name: "A", roles: ["admin"] } });

describe("adminFetch", () => {
  let fetchMock: ReturnType<typeof vi.fn>;
  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    setSessionLostHandler(null);
  });

  it("envía el Bearer y renueva la sesión una vez ante un 401", async () => {
    fetchMock
      .mockResolvedValueOnce(tokenResp("viejo")) // login
      .mockResolvedValueOnce(json({ title: "No autenticado" }, 401)) // token expirado
      .mockResolvedValueOnce(tokenResp("nuevo")) // refresh con la cookie
      .mockResolvedValueOnce(json([{ key: "hero.title" }])); // reintento
    await login("a@b.cl", "x");

    const data = await adminApi.get<unknown[]>("/content");
    expect(data).toHaveLength(1);
    const [firstUrl, firstInit] = fetchMock.mock.calls[1];
    expect(firstUrl).toBe("/api/v1/admin/content");
    expect(new Headers(firstInit.headers).get("Authorization")).toBe("Bearer viejo");
    expect(fetchMock.mock.calls[2][0]).toBe("/api/v1/admin/auth/refresh");
    expect(new Headers(fetchMock.mock.calls[3][1].headers).get("Authorization")).toBe("Bearer nuevo");
  });

  it("avisa de sesión perdida si el refresh falla", async () => {
    const lost = vi.fn();
    setSessionLostHandler(lost);
    fetchMock
      .mockResolvedValueOnce(json({ title: "No autenticado" }, 401))
      .mockResolvedValueOnce(json({ title: "Sesión expirada" }, 401))
      ;
    await expect(adminApi.get("/leads")).rejects.toMatchObject({ status: 401 });
    expect(lost).toHaveBeenCalledOnce();
  });
});
