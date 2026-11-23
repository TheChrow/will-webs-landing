import Markdown from "react-markdown";

import { ApiError, type LegalType } from "~/lib/api";
import { useLegal } from "~/lib/queries";

const dateFmt = new Intl.DateTimeFormat("es-CL", { dateStyle: "long", timeZone: "America/Santiago" });

/**
 * Documento legal servido por la API (versión vigente).
 * react-markdown no renderiza HTML crudo: el contenido no puede inyectar scripts.
 */
export function LegalPage({ type, title }: { type: LegalType; title: string }) {
  const { data, isPending, error } = useLegal(type);
  const notPublished = error instanceof ApiError && error.status === 404;

  return (
    <div className="container py-5">
      <h1 className="fw-bold text-brand mb-2">{data?.title ?? title}</h1>
      {data && (
        <p className="text-secondary small mb-4">
          Versión {data.version}
          {data.published_at && ` · vigente desde el ${dateFmt.format(new Date(`${data.published_at}Z`))}`}
        </p>
      )}
      {isPending && <p className="text-secondary">Cargando…</p>}
      {notPublished && (
        <div className="alert alert-info">
          Este documento se encuentra en preparación y será publicado próximamente.
        </div>
      )}
      {error && !notPublished && (
        <div className="alert alert-warning">
          No pudimos cargar el documento. Intenta recargar la página.
        </div>
      )}
      {data && (
        <div className="legal-body">
          <Markdown skipHtml>{data.body}</Markdown>
        </div>
      )}
    </div>
  );
}
