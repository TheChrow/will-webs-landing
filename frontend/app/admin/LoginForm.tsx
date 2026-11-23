import { useState } from "react";

import { ApiError } from "~/lib/api";

import { useAuth } from "./auth";

export function LoginForm({ notice }: { notice?: string }) {
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setPending(true);
    setError(null);
    try {
      await login(String(form.get("email")), String(form.get("password")));
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 429
          ? "Demasiados intentos. Espera unos minutos."
          : "Correo o contraseña incorrectos.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="admin-shell d-flex align-items-center justify-content-center p-3">
      <form className="card shadow-sm border-0 p-4 w-100 login-card" onSubmit={onSubmit}>
        <h1 className="h4 fw-bold text-brand mb-1">Panel Will-Webs</h1>
        <p className="text-secondary small mb-4">Acceso solo para personal autorizado.</p>
        <div role="status" aria-live="polite">
          {(error || notice) && (
            <div className={`alert ${error ? "alert-danger" : "alert-info"} py-2`}>
              {error ?? notice}
            </div>
          )}
        </div>
        <div className="mb-3">
          <label htmlFor="admin-email" className="form-label">
            Correo
          </label>
          <input id="admin-email" name="email" type="email" className="form-control"
                 autoComplete="username" required />
        </div>
        <div className="mb-4">
          <label htmlFor="admin-password" className="form-label">
            Contraseña
          </label>
          <input id="admin-password" name="password" type="password" className="form-control"
                 autoComplete="current-password" required />
        </div>
        <button type="submit" className="btn btn-brand w-100" disabled={pending}>
          {pending ? "Ingresando…" : "Ingresar"}
        </button>
      </form>
    </main>
  );
}
