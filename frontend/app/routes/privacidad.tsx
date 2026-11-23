import { LegalPage } from "~/components/LegalPage";
import { pageMeta } from "~/lib/seo";

import type { Route } from "./+types/privacidad";

export const meta: Route.MetaFunction = () =>
  pageMeta({ title: "Política de Privacidad", description: "Cómo Will-Webs trata tus datos personales y cómo ejercer tus derechos.", path: "/privacidad" });

export default function Page() {
  return <LegalPage type="privacy" title="Política de Privacidad" />;
}
