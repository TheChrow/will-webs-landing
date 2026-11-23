export const SITE_NAME = "Will-Webs";
export const SITE_URL = (import.meta.env.VITE_SITE_URL as string | undefined)?.replace(/\/$/, "");

/** Meta tags comunes (title, description, Open Graph, canonical si hay dominio). */
export function pageMeta({
  title,
  description,
  path,
  noindex = false,
}: {
  title: string;
  description: string;
  path: string;
  noindex?: boolean;
}) {
  const fullTitle = title.includes(SITE_NAME) ? title : `${title} | ${SITE_NAME}`;
  const tags: Record<string, string>[] = [
    { title: fullTitle },
    { name: "description", content: description },
    { property: "og:type", content: "website" },
    { property: "og:site_name", content: SITE_NAME },
    { property: "og:locale", content: "es_CL" },
    { property: "og:title", content: fullTitle },
    { property: "og:description", content: description },
    { name: "twitter:card", content: "summary" },
  ];
  if (SITE_URL) {
    tags.push({ property: "og:url", content: `${SITE_URL}${path}` });
    tags.push({ tagName: "link", rel: "canonical", href: `${SITE_URL}${path}` });
  }
  if (noindex) tags.push({ name: "robots", content: "noindex" });
  return tags;
}
