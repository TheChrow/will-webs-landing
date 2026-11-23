import { LegalPage } from "~/components/LegalPage";
import { pageMeta } from "~/lib/seo";

import type { Route } from "./+types/accesibilidad";

export const meta: Route.MetaFunction = () =>
  pageMeta({ title: "Declaración de Accesibilidad", description: "Compromiso de accesibilidad del sitio de Will-Webs (WCAG 2.2 AA).", path: "/accesibilidad" });

export default function Page() {
  return <LegalPage type="accessibility" title="Declaración de Accesibilidad" />;
}
