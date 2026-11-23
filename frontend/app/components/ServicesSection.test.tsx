import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { FALLBACK_SERVICES } from "~/lib/fallback";

import { ServicesGrid } from "./ServicesSection";

describe("ServicesGrid", () => {
  it("lista los 10 servicios y filtra por categoría", async () => {
    const user = userEvent.setup();
    render(<ServicesGrid services={FALLBACK_SERVICES} />);

    const list = screen.getAllByRole("list")[0];
    expect(within(list).getAllByRole("listitem")).toHaveLength(10);

    const chip = screen.getByRole("button", { name: "Infraestructura y seguridad" });
    await user.click(chip);
    expect(chip).toHaveAttribute("aria-pressed", "true");
    const titles = within(list)
      .getAllByRole("heading")
      .map((h) => h.textContent);
    expect(titles).toEqual(["Infraestructura", "Correo empresarial", "Respaldo y seguridad"]);

    await user.click(screen.getByRole("button", { name: "Todos" }));
    expect(within(list).getAllByRole("listitem")).toHaveLength(10);
  });
});
