import { useServices } from "~/lib/queries";

import { ContactForm } from "./ContactForm";

export function ContactSection() {
  const { data: services } = useServices();
  return (
    <section className="py-5" id="contacto" aria-labelledby="contacto-title">
      <div className="container py-4 contact-container">
        <h2 id="contacto-title" className="text-center fw-bold mb-2 text-brand">
          Conversemos
        </h2>
        <p className="text-center text-secondary mb-5">
          Cuéntanos qué necesitas y te responderemos a la brevedad.
        </p>
        <ContactForm services={services ?? []} />
      </div>
    </section>
  );
}
