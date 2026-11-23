import { ApiError } from "~/lib/api";

const dt = new Intl.DateTimeFormat("es-CL", {
  dateStyle: "short",
  timeStyle: "short",
  timeZone: "America/Santiago",
});

/** Fechas de la API: UTC sin zona -> hora de Chile. */
export const fmtDate = (iso: string | null) => (iso ? dt.format(new Date(`${iso}Z`)) : "—");

export function ErrorAlert({ error }: { error: unknown }) {
  if (!error) return null;
  const msg = error instanceof ApiError ? `${error.message} (${error.status})` : "Error inesperado";
  return <div className="alert alert-danger py-2" role="alert">{msg}</div>;
}

export function PageTitle({ children }: { children: React.ReactNode }) {
  return <h1 className="h3 fw-bold text-brand mb-4">{children}</h1>;
}
