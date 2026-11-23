import { LegalPage } from "~/components/LegalPage";
import { pageMeta } from "~/lib/seo";

import type { Route } from "./+types/cookies";

export const meta: Route.MetaFunction = () =>
  pageMeta({ title: "Política de Cookies", description: "Qué cookies usa el sitio de Will-Webs y cómo gestionarlas.", path: "/cookies" });

export default function Page() {
  return <LegalPage type="cookies" title="Política de Cookies" />;
}
