import { ContactSection } from "~/components/ContactSection";
import { Hero } from "~/components/Hero";
import { AboutSection, ClientsMarquee, CtaBand } from "~/components/Sections";
import { ServicesSection } from "~/components/ServicesSection";
import { SITE_NAME, SITE_URL, pageMeta } from "~/lib/seo";

import type { Route } from "./+types/home";

export const meta: Route.MetaFunction = () => [
  ...pageMeta({
    title: "Will-Webs — Transformación digital y software a medida",
    description:
      "Automatizamos procesos, creamos software a medida e integramos tus plataformas con inteligencia artificial.",
    path: "/",
  }),
  {
    "script:ld+json": {
      "@context": "https://schema.org",
      "@type": "Organization",
      name: SITE_NAME,
      ...(SITE_URL ? { url: SITE_URL } : {}),
      description: "Transformación digital, software a medida, automatización e integraciones.",
      areaServed: "CL",
    },
  },
];

export default function Home() {
  return (
    <>
      <Hero />
      <ServicesSection />
      <CtaBand />
      <AboutSection />
      <ClientsMarquee />
      <ContactSection />
    </>
  );
}
