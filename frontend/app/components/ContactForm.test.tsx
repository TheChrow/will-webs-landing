import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRoutesStub } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { FALLBACK_SERVICES } from "~/lib/fallback";

import { ContactForm } from "./ContactForm";

function renderForm() {
  const Stub = createRoutesStub([
    { path: "/", Component: () => <ContactForm services={FALLBACK_SERVICES} /> },
  ]);
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <Stub />
    </QueryClientProvider>,
  );
}

async function fillValid(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText(/^Nombre/), "Ana Pérez");
  await user.type(screen.getByLabelText(/Correo electrónico/), "ana@example.com");
  await user.type(screen.getByLabelText(/^Mensaje/), "Necesitamos un sistema de inventario.");
  await user.selectOptions(screen.getByLabelText(/Servicio de interés/), "software-a-medida");
  await user.click(screen.getByLabelText(/He leído y acepto/));
}

describe("ContactForm", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });
  afterEach(() => vi.unstubAllGlobals());

  it("muestra errores accesibles y no envía si faltan datos", async () => {
    const user = userEvent.setup();
    renderForm();
    await user.click(screen.getByRole("button", { name: /Enviar mensaje/ }));

    const name = screen.getByLabelText(/^Nombre/);
    expect(name).toHaveAttribute("aria-invalid", "true");
    expect(name).toHaveAccessibleDescription("Ingresa tu nombre.");
    expect(screen.getByText("Debes aceptar la Política de Privacidad.")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("envía el payload esperado por la API y confirma", async () => {
    fetchMock.mockResolvedValue(new Response(JSON.stringify({ status: "accepted" }), { status: 202 }));
    const user = userEvent.setup();
    renderForm();
    await fillValid(user);
    await user.click(screen.getByRole("button", { name: /Enviar mensaje/ }));

    expect(await screen.findByText(/Recibimos tu mensaje/)).toBeInTheDocument();
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/v1/contact");
    const body = JSON.parse(init.body);
    expect(body).toMatchObject({
      name: "Ana Pérez",
      email: "ana@example.com",
      service: "software-a-medida",
      privacy_accepted: true,
      marketing_opt_in: false,
      website: "",
    });
    expect(typeof body.elapsed_ms).toBe("number");
    expect(body).not.toHaveProperty("company"); // vacíos no se envían
  });

  it("informa el rate limit con el tiempo de espera", async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ title: "Demasiados envíos" }), {
        status: 429,
        headers: { "Retry-After": "600" },
      }),
    );
    const user = userEvent.setup();
    renderForm();
    await fillValid(user);
    await user.click(screen.getByRole("button", { name: /Enviar mensaje/ }));

    expect(await screen.findByRole("status")).toHaveTextContent("en 10 min");
  });

  it("valida el teléfono", async () => {
    const user = userEvent.setup();
    renderForm();
    const phone = screen.getByLabelText(/Teléfono/);
    await user.type(phone, "abc");
    await user.tab();
    expect(phone).toHaveAttribute("aria-invalid", "true");
  });
});
