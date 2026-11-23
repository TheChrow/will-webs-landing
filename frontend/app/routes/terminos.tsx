import { LegalPage } from "~/components/LegalPage";
import { pageMeta } from "~/lib/seo";

import type { Route } from "./+types/terminos";

export const meta: Route.MetaFunction = () =>
  pageMeta({ title: "Términos y Condiciones", description: "Condiciones de uso del sitio web de Will-Webs.", path: "/terminos" });

export default function Page() {
  return <LegalPage type="terms" title="Términos y Condiciones" />;
}
