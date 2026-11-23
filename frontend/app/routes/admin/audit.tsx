import { useQuery } from "@tanstack/react-query";

import { type AuditEntry, type Page, adminApi } from "~/admin/api";
import { useAuth } from "~/admin/auth";
import { ErrorAlert, PageTitle, fmtDate } from "~/admin/ui";

export default function Audit() {
  const { hasRole } = useAuth();
  const query = useQuery({
    queryKey: ["admin", "audit"],
    queryFn: () => adminApi.get<Page<AuditEntry>>("/audit?limit=100"),
    enabled: hasRole("admin"),
  });
  if (!hasRole("admin")) return <p>Esta sección es solo para administradores.</p>;

  return (
    <>
      <PageTitle>Auditoría</PageTitle>
      <ErrorAlert error={query.error} />
      <div className="card border-0 shadow-sm">
        <div className="table-responsive">
          <table className="table table-sm align-middle mb-0 small">
            <thead>
              <tr><th>Fecha</th><th>Actor</th><th>Acción</th><th>Entidad</th><th>Cambios</th></tr>
            </thead>
            <tbody>
              {query.data?.items.map((e, i) => (
                <tr key={`${e.created_at}-${i}`}>
                  <td className="text-nowrap">{fmtDate(e.created_at)}</td>
                  <td>{e.actor ?? "sistema"}</td>
                  <td><code>{e.action}</code></td>
                  <td>{e.entity}{e.entity_id && <div className="text-secondary">{e.entity_id}</div>}</td>
                  <td className="admin-pre">{e.diff ? JSON.stringify(e.diff) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
