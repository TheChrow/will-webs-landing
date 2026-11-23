import { z } from "zod";

/** Espejo de backend/app/schemas/contact.py (la validación del servidor es la que manda). */
const singleLine = /^[^\r\n\u0000-\u001f\u007f]*$/;

export const contactSchema = z.object({
  name: z
    .string()
    .trim()
    .min(2, "Ingresa tu nombre.")
    .max(120, "Máximo 120 caracteres.")
    .regex(singleLine, "Sin saltos de línea."),
  email: z.string().trim().max(254).email("Ingresa un correo válido."),
  company: z.string().trim().max(160, "Máximo 160 caracteres.").regex(singleLine).optional(),
  phone: z
    .string()
    .trim()
    .refine((v) => v === "" || /^\+?[0-9]{7,15}$/.test(v.replace(/[\s\-().]/g, "")), {
      message: "Ingresa un teléfono válido (ej. +56 9 1234 5678).",
    })
    .optional(),
  service: z.string().optional(),
  message: z
    .string()
    .trim()
    .min(10, "Cuéntanos un poco más (mínimo 10 caracteres).")
    .max(5000, "Máximo 5000 caracteres."),
  privacy_accepted: z.literal(true, { error: "Debes aceptar la Política de Privacidad." }),
  marketing_opt_in: z.boolean(),
  website: z.string().max(200), // honeypot
});

export type ContactFormValues = z.input<typeof contactSchema>;
