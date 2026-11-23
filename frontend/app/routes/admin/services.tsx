import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { type AdminService, adminApi } from "~/admin/api";
import { ErrorAlert, PageTitle, fmtDate } from "~/admin/ui";

function EditForm({ service, onDone }: { service: AdminService; onDone: () => void }) {
  const qc = useQueryClient();
  const save = useMutation({
    mutationFn: (body: Partial<AdminService>) =>
      adminApi.patch<AdminService>(`/services/${service.id}`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "services"] });
      qc.invalidateQueries({ queryKey: ["services"] });
      onDone();
    },
  });

  function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    save.mutate({
      title: String(f.get("title")),
      summary: String(f.get("summary")),
      sort_order: Number(f.get("sort_order")),
    });
  }

  return (
    <form onSubmit={onSubmit} className="card card-body border-0 shadow-sm mb-3">
      <h2 className="h6 fw-bold">Editar: {service.title}</h2>
      <ErrorAlert error={save.error} />
      <div className="row g-2">
        <div className="col-md-5">
          <label className="form-label small" htmlFor="svc-title">Título</label>
          <input id="svc-title" name="title" className="form-control" defaultValue={service.title}
                 required maxLength={120} />
        </div>
        <div className="col-md-5">
          <label className="form-label small" htmlFor="svc-summary">Resumen</label>
          <input id="svc-summary" name="summary" className="form-control"
                 defaultValue={service.summary} required maxLength={280} />
        </div>
        <div className="col-md-2">
          <label className="form-label small" htmlFor="svc-order">Orden</label>
          <input id="svc-order" name="sort_order" type="number" min={0} className="form-control"
                 defaultValue={service.sort_order} />
        </div>
      </div>
      <div className="d-flex gap-2 mt-3">
        <button type="submit" className="btn btn-brand btn-sm" disabled={save.isPending}>Guardar</button>
        <button type="button" className="btn btn-outline-secondary btn-sm" onClick={onDone}>Cancelar</button>
      </div>
    </form>
  );
}

export default function Services() {
  const qc = useQueryClient();
  const [editing, setEditing] = useState<AdminService | null>(null);
  const query = useQuery({
    queryKey: ["admin", "services"],
    queryFn: () => adminApi.get<AdminService[]>("/services"),
  });
  const toggle = useMutation({
    mutationFn: (s: AdminService) =>
      adminApi.patch<AdminService>(`/services/${s.id}`, { is_published: !s.is_published }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "services"] }),
  });

  return (
    <>
      <PageTitle>Servicios</PageTitle>
      <ErrorAlert error={query.error ?? toggle.error} />
      {editing && <EditForm key={editing.id} service={editing} onDone={() => setEditing(null)} />}
      <div className="card border-0 shadow-sm">
        <div className="table-responsive">
          <table className="table align-middle mb-0">
            <thead>
              <tr><th>Orden</th><th>Servicio</th><th>Categoría</th><th>Actualizado</th><th>Publicado</th><th /></tr>
            </thead>
            <tbody>
              {query.data?.map((s) => (
                <tr key={s.id}>
                  <td className="small">{s.sort_order}</td>
                  <td>
                    <div className="fw-semibold">{s.title}</div>
                    <div className="small text-secondary">{s.summary}</div>
                  </td>
                  <td className="small">{s.category ?? "—"}</td>
                  <td className="small text-nowrap">{fmtDate(s.updated_at)}</td>
                  <td>
                    <div className="form-check form-switch">
                      <input className="form-check-input" type="checkbox" role="switch"
                             id={`pub-${s.id}`} checked={s.is_published}
                             disabled={toggle.isPending} onChange={() => toggle.mutate(s)} />
                      <label className="visually-hidden" htmlFor={`pub-${s.id}`}>
                        Publicar {s.title}
                      </label>
                    </div>
                  </td>
                  <td>
                    <button type="button" className="btn btn-sm btn-outline-secondary"
                            onClick={() => setEditing(s)}>Editar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
