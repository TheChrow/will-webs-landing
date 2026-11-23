import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { type AdminContentBlock, adminApi } from "~/admin/api";
import { ErrorAlert, PageTitle, fmtDate } from "~/admin/ui";

const LABELS: Record<string, string> = {
  "hero.title": "Hero — título",
  "hero.lead": "Hero — bajada",
  "cta.text": "Banda CTA",
  "about.mission": "Misión",
  "about.vision": "Visión",
};

function BlockEditor({ block }: { block: AdminContentBlock }) {
  const qc = useQueryClient();
  const save = useMutation({
    mutationFn: (body: { title: string | null; body: string; is_published: boolean }) =>
      adminApi.put<AdminContentBlock>(
        `/content/${block.key}?locale=${encodeURIComponent(block.locale)}`, body,
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "content"] });
      qc.invalidateQueries({ queryKey: ["content"] });
    },
  });

  function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const title = String(f.get("title") ?? "").trim();
    save.mutate({
      title: title || null,
      body: String(f.get("body")),
      is_published: f.get("is_published") === "on",
    });
  }

  const id = block.key.replace(/\./g, "-");
  return (
    <form onSubmit={onSubmit} className="card border-0 shadow-sm mb-3">
      <div className="card-body">
        <div className="d-flex justify-content-between align-items-center mb-2">
          <h2 className="h6 fw-bold mb-0">{LABELS[block.key] ?? block.key}</h2>
          <span className="small text-secondary">{block.key} · {fmtDate(block.updated_at)}</span>
        </div>
        <ErrorAlert error={save.error} />
        {save.isSuccess && <div className="alert alert-success py-1 small">Guardado</div>}
        <label className="form-label small" htmlFor={`${id}-title`}>Título (opcional)</label>
        <input id={`${id}-title`} name="title" className="form-control mb-2"
               defaultValue={block.title ?? ""} maxLength={200} />
        <label className="form-label small" htmlFor={`${id}-body`}>Texto</label>
        <textarea id={`${id}-body`} name="body" className="form-control mb-2" rows={3}
                  defaultValue={block.body} required maxLength={20000} />
        <div className="d-flex justify-content-between align-items-center">
          <div className="form-check form-switch">
            <input id={`${id}-pub`} name="is_published" type="checkbox" role="switch"
                   className="form-check-input" defaultChecked={block.is_published} />
            <label htmlFor={`${id}-pub`} className="form-check-label">Publicado</label>
          </div>
          <button type="submit" className="btn btn-brand btn-sm" disabled={save.isPending}>
            Guardar
          </button>
        </div>
      </div>
    </form>
  );
}

export default function Content() {
  const query = useQuery({
    queryKey: ["admin", "content"],
    queryFn: () => adminApi.get<AdminContentBlock[]>("/content"),
  });
  return (
    <>
      <PageTitle>Contenido del sitio</PageTitle>
      <ErrorAlert error={query.error} />
      {query.data?.map((b) => (
        <BlockEditor key={`${b.key}:${b.locale}:${b.updated_at}`} block={b} />
      ))}
    </>
  );
}
