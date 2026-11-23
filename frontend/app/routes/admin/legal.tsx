import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import Markdown from "react-markdown";

import { type LegalDoc, type LegalVersion, adminApi } from "~/admin/api";
import { useAuth } from "~/admin/auth";
import { ErrorAlert, PageTitle, fmtDate } from "~/admin/ui";

function VersionPanel({ doc, version }: { doc: LegalDoc; version: string }) {
  const qc = useQueryClient();
  const path = `/legal/${doc.type}/versions/${version}`;
  const query = useQuery({
    queryKey: ["admin", "legal", doc.type, version],
    queryFn: () => adminApi.get<LegalVersion>(path),
  });
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["admin", "legal"] });
    qc.invalidateQueries({ queryKey: ["legal", doc.type] });
  };
  const save = useMutation({
    mutationFn: (body: string) => adminApi.patch<LegalVersion>(path, { body }),
    onSuccess: invalidate,
  });
  const publish = useMutation({
    mutationFn: () => adminApi.post<LegalVersion>(`${path}/publish`),
    onSuccess: invalidate,
  });

  const v = query.data;
  if (!v) return <ErrorAlert error={query.error} />;
  const draft = v.published_at === null;
  const hasPlaceholders = /\[[A-ZÁÉÍÓÚÑ ]{3,}\]/.test(v.body ?? "");

  return (
    <div className="card border-0 shadow-sm">
      <div className="card-body">
        <h2 className="h5">{doc.title} · v{v.version}</h2>
        <ErrorAlert error={save.error ?? publish.error} />
        {draft ? (
          <form onSubmit={(e) => {
            e.preventDefault();
            save.mutate(String(new FormData(e.currentTarget).get("body")));
          }}>
            <label className="form-label small" htmlFor="legal-body">Texto (Markdown)</label>
            <textarea id="legal-body" name="body" className="form-control admin-textarea mb-2"
                      rows={16} defaultValue={v.body ?? ""} key={v.body} />
            {hasPlaceholders && (
              <div className="alert alert-warning py-2 small">
                El texto aún tiene datos entre corchetes (ej. [RUT]). Complétalos antes de publicar.
              </div>
            )}
            <div className="d-flex gap-2">
              <button type="submit" className="btn btn-outline-secondary btn-sm" disabled={save.isPending}>
                Guardar borrador
              </button>
              <button type="button" className="btn btn-brand btn-sm"
                      disabled={publish.isPending || hasPlaceholders}
                      onClick={() => {
                        if (window.confirm("Publicar esta versión? Una vez publicada no se puede modificar.")) {
                          publish.mutate();
                        }
                      }}>
                Publicar versión
              </button>
            </div>
          </form>
        ) : (
          <>
            <p className="small text-secondary">
              Publicada el {fmtDate(v.published_at)} · solo lectura (para cambiarla crea una versión nueva).
            </p>
            <div className="legal-body border rounded p-3 bg-light">
              <Markdown skipHtml>{v.body ?? ""}</Markdown>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function NewVersion({ doc }: { doc: LegalDoc }) {
  const qc = useQueryClient();
  const create = useMutation({
    mutationFn: async (version: string) => {
      // La nueva versión parte del texto de la más reciente.
      const latest = doc.versions[0]
        ? await adminApi.get<LegalVersion>(`/legal/${doc.type}/versions/${doc.versions[0].version}`)
        : null;
      return adminApi.post(`/legal/${doc.type}/versions`, {
        version,
        body: latest?.body ?? "> Borrador\n",
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "legal"] }),
  });
  return (
    <form className="d-flex gap-2 mt-2" onSubmit={(e) => {
      e.preventDefault();
      create.mutate(String(new FormData(e.currentTarget).get("version")));
    }}>
      <label className="visually-hidden" htmlFor={`nv-${doc.type}`}>Nueva versión</label>
      <input id={`nv-${doc.type}`} name="version" className="form-control form-control-sm"
             placeholder="1.0.0" pattern="\d{1,3}\.\d{1,3}\.\d{1,3}" required />
      <button type="submit" className="btn btn-sm btn-outline-secondary text-nowrap">Nueva versión</button>
      <ErrorAlert error={create.error} />
    </form>
  );
}

export default function Legal() {
  const { hasRole } = useAuth();
  const [selected, setSelected] = useState<{ doc: LegalDoc; version: string } | null>(null);
  const query = useQuery({
    queryKey: ["admin", "legal"],
    queryFn: () => adminApi.get<LegalDoc[]>("/legal"),
    enabled: hasRole("admin"),
  });

  if (!hasRole("admin")) return <p>Esta sección es solo para administradores.</p>;

  return (
    <>
      <PageTitle>Documentos legales</PageTitle>
      <ErrorAlert error={query.error} />
      <div className="row g-3">
        <div className="col-lg-4">
          {query.data?.map((doc) => (
            <section key={doc.type} className="card border-0 shadow-sm mb-3" aria-label={doc.title}>
              <div className="card-body">
                <h2 className="h6 fw-bold">{doc.title}</h2>
                <ul className="list-group list-group-flush small">
                  {doc.versions.map((v) => (
                    <li key={v.version} className="list-group-item px-0 d-flex justify-content-between align-items-center">
                      <button type="button" className="btn btn-link btn-sm p-0"
                              onClick={() => setSelected({ doc, version: v.version })}>
                        v{v.version}
                      </button>
                      {v.is_current ? (
                        <span className="badge text-bg-success">Vigente</span>
                      ) : v.published_at ? (
                        <span className="badge text-bg-secondary">Histórica</span>
                      ) : (
                        <span className="badge text-bg-warning">Borrador</span>
                      )}
                    </li>
                  ))}
                </ul>
                <NewVersion doc={doc} />
              </div>
            </section>
          ))}
        </div>
        <div className="col-lg-8">
          {selected ? (
            <VersionPanel key={`${selected.doc.type}-${selected.version}`} doc={selected.doc}
                          version={selected.version} />
          ) : (
            <p className="text-secondary">Selecciona una versión para verla o editarla.</p>
          )}
        </div>
      </div>
    </>
  );
}
