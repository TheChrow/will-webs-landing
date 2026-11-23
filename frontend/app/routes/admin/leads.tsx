import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { adminApi, type Lead, type LeadStatus, type Page } from "~/admin/api";
import { ErrorAlert, PageTitle, fmtDate } from "~/admin/ui";

const STATUS: Record<LeadStatus, { label: string; cls: string }> = {
  new: { label: "Nuevo", cls: "text-bg-primary" },
  read: { label: "Leído", cls: "text-bg-secondary" },
  contacted: { label: "Contactado", cls: "text-bg-success" },
  archived: { label: "Archivado", cls: "text-bg-light" },
  spam: { label: "Spam", cls: "text-bg-danger" },
};

export default function Leads() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState<LeadStatus | "">("new");
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<Lead | null>(null);
  const limit = 25;

  const query = useQuery({
    queryKey: ["admin", "leads", filter, offset],
    queryFn: () =>
      adminApi.get<Page<Lead>>(
        `/leads?limit=${limit}&offset=${offset}${filter ? `&status=${filter}` : ""}`,
      ),
  });

  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: LeadStatus }) =>
      adminApi.patch<Lead>(`/leads/${id}`, { status }),
    onSuccess: (lead) => {
      setSelected(lead);
      qc.invalidateQueries({ queryKey: ["admin", "leads"] });
    },
  });

  const page = query.data;
  return (
    <>
      <PageTitle>Leads</PageTitle>
      <div className="d-flex flex-wrap gap-2 align-items-center mb-3">
        <label htmlFor="lead-filter" className="form-label mb-0">Estado</label>
        <select id="lead-filter" className="form-select form-select-sm w-auto" value={filter}
                onChange={(e) => { setFilter(e.target.value as LeadStatus | ""); setOffset(0); }}>
          <option value="">Todos</option>
          {Object.entries(STATUS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </select>
        {page && <span className="small text-secondary">{page.total} en total</span>}
      </div>
      <ErrorAlert error={query.error ?? setStatus.error} />

      <div className="row g-3">
        <div className={selected ? "col-lg-6" : "col-12"}>
          <div className="card border-0 shadow-sm">
            <div className="table-responsive">
              <table className="table table-hover mb-0 align-middle">
                <thead>
                  <tr><th>Fecha</th><th>Nombre</th><th>Servicio</th><th>Estado</th></tr>
                </thead>
                <tbody>
                  {page?.items.map((l) => (
                    <tr key={l.id} className={selected?.id === l.id ? "table-active" : undefined}>
                      <td className="small text-nowrap">{fmtDate(l.created_at)}</td>
                      <td>
                        <button type="button" className="btn btn-link p-0 text-start"
                                onClick={() => setSelected(l)}>
                          {l.name}
                        </button>
                        <div className="small text-secondary">{l.email}</div>
                      </td>
                      <td className="small">{l.service ?? "—"}</td>
                      <td><span className={`badge ${STATUS[l.status].cls}`}>{STATUS[l.status].label}</span></td>
                    </tr>
                  ))}
                  {page?.items.length === 0 && (
                    <tr><td colSpan={4} className="text-center text-secondary py-4">Sin leads</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
          {page && page.total > limit && (
            <div className="d-flex gap-2 mt-2">
              <button type="button" className="btn btn-sm btn-outline-secondary"
                      disabled={offset === 0} onClick={() => setOffset(offset - limit)}>Anterior</button>
              <button type="button" className="btn btn-sm btn-outline-secondary"
                      disabled={offset + limit >= page.total}
                      onClick={() => setOffset(offset + limit)}>Siguiente</button>
            </div>
          )}
        </div>

        {selected && (
          <div className="col-lg-6">
            <section className="card border-0 shadow-sm" aria-label="Detalle del lead">
              <div className="card-body">
                <div className="d-flex justify-content-between align-items-start mb-2">
                  <h2 className="h5 mb-0">{selected.name}</h2>
                  <button type="button" className="btn-close" aria-label="Cerrar detalle"
                          onClick={() => setSelected(null)} />
                </div>
                <dl className="row small mb-3">
                  <dt className="col-4">Correo</dt>
                  <dd className="col-8"><a href={`mailto:${selected.email}`}>{selected.email}</a></dd>
                  <dt className="col-4">Empresa</dt><dd className="col-8">{selected.company ?? "—"}</dd>
                  <dt className="col-4">Teléfono</dt><dd className="col-8">{selected.phone ?? "—"}</dd>
                  <dt className="col-4">Servicio</dt><dd className="col-8">{selected.service ?? "—"}</dd>
                  <dt className="col-4">Recibido</dt><dd className="col-8">{fmtDate(selected.created_at)}</dd>
                  <dt className="col-4">Retención</dt><dd className="col-8">hasta {selected.retention_until}</dd>
                </dl>
                {/* Texto plano: React escapa el contenido; nunca se interpreta como HTML. */}
                <p className="admin-pre border rounded p-3 bg-light">{selected.message ?? "[anonimizado]"}</p>
                <label htmlFor="lead-status" className="form-label">Cambiar estado</label>
                <select id="lead-status" className="form-select" value={selected.status}
                        disabled={setStatus.isPending}
                        onChange={(e) => setStatus.mutate({ id: selected.id, status: e.target.value as LeadStatus })}>
                  {Object.entries(STATUS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                </select>
              </div>
            </section>
          </div>
        )}
      </div>
    </>
  );
}
