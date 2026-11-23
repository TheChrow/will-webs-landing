import { useEffect, useRef } from "react";

declare global {
  interface Window {
    turnstile?: {
      render: (el: HTMLElement, opts: Record<string, unknown>) => string;
      reset: (id?: string) => void;
      remove: (id: string) => void;
    };
  }
}

const SCRIPT_SRC = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
export const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY as string | undefined;

let scriptPromise: Promise<void> | null = null;
function loadScript(): Promise<void> {
  scriptPromise ??= new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = SCRIPT_SRC;
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("No se pudo cargar Turnstile"));
    document.head.appendChild(s);
  });
  return scriptPromise;
}

/**
 * Widget de Cloudflare Turnstile. Solo se carga si hay VITE_TURNSTILE_SITE_KEY
 * (en dev sin clave el backend desactiva la verificación).
 */
export function Turnstile({
  onToken,
  resetSignal,
}: {
  onToken: (token: string | undefined) => void;
  resetSignal: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const widgetId = useRef<string | null>(null);

  useEffect(() => {
    if (!TURNSTILE_SITE_KEY || !ref.current) return;
    let cancelled = false;
    loadScript()
      .then(() => {
        if (cancelled || !ref.current || !window.turnstile) return;
        widgetId.current = window.turnstile.render(ref.current, {
          sitekey: TURNSTILE_SITE_KEY,
          language: "es",
          callback: (token: string) => onToken(token),
          "expired-callback": () => onToken(undefined),
          "error-callback": () => onToken(undefined),
        });
      })
      .catch(() => onToken(undefined));
    return () => {
      cancelled = true;
      if (widgetId.current && window.turnstile) window.turnstile.remove(widgetId.current);
      widgetId.current = null;
    };
  }, [onToken]);

  useEffect(() => {
    if (resetSignal > 0 && widgetId.current && window.turnstile) {
      window.turnstile.reset(widgetId.current);
      onToken(undefined);
    }
  }, [resetSignal, onToken]);

  if (!TURNSTILE_SITE_KEY) return null;
  return <div ref={ref} className="mb-1" />;
}
