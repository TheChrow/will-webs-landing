import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useCallback, useId, useRef, useState } from "react";
import { type FieldError, useForm } from "react-hook-form";
import { Link } from "react-router";

import { ApiError, api, type Service } from "~/lib/api";
import { type ContactFormValues, contactSchema } from "~/lib/contact-schema";

import { TURNSTILE_SITE_KEY, Turnstile } from "./Turnstile";

type Status =
  | { kind: "idle" }
  | { kind: "success" }
  | { kind: "error"; message: string };

function errorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 429) {
      const minutes = err.retryAfter ? Math.ceil(err.retryAfter / 60) : null;
      return `Recibimos demasiados envíos desde tu conexión. Intenta de nuevo${minutes ? ` en ${minutes} min` : " más tarde"}.`;
    }
    if (err.status === 400) return "No pudimos verificar que no eres un robot. Inténtalo otra vez.";
    if (err.status === 422) return "Revisa los datos del formulario.";
    if (err.status === 503) return "El formulario no está disponible en este momento. Escríbenos por correo.";
  }
  return "No pudimos enviar tu mensaje. Revisa tu conexión e inténtalo de nuevo.";
}

const DEFAULTS: ContactFormValues = {
  name: "",
  email: "",
  company: "",
  phone: "",
  service: "",
  message: "",
  privacy_accepted: false as unknown as true,
  marketing_opt_in: false,
  website: "",
};

export function ContactForm({ services }: { services: Service[] }) {
  const uid = useId();
  const startedAt = useRef<number>(Date.now());
  const [status, setStatus] = useState<Status>({ kind: "idle" });
  const [captchaToken, setCaptchaToken] = useState<string | undefined>();
  const [captchaReset, setCaptchaReset] = useState(0);
  const onToken = useCallback((t: string | undefined) => setCaptchaToken(t), []);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ContactFormValues>({
    resolver: zodResolver(contactSchema),
    defaultValues: DEFAULTS,
    mode: "onTouched",
  });

  const mutation = useMutation({ mutationFn: api.contact });

  const onSubmit = handleSubmit(async (values) => {
    setStatus({ kind: "idle" });
    if (TURNSTILE_SITE_KEY && !captchaToken) {
      setStatus({ kind: "error", message: "Completa la verificación anti-robots." });
      return;
    }
    try {
      await mutation.mutateAsync({
        name: values.name,
        email: values.email,
        company: values.company || undefined,
        phone: values.phone || undefined,
        service: values.service || undefined,
        message: values.message,
        privacy_accepted: true,
        marketing_opt_in: values.marketing_opt_in,
        website: values.website,
        elapsed_ms: Date.now() - startedAt.current,
        captcha_token: captchaToken,
      });
      setStatus({ kind: "success" });
      reset(DEFAULTS);
      startedAt.current = Date.now();
    } catch (err) {
      setStatus({ kind: "error", message: errorMessage(err) });
    } finally {
      setCaptchaReset((n) => n + 1);
    }
  });

  const field = (name: keyof ContactFormValues) => {
    const error = errors[name] as FieldError | undefined;
    const id = `${uid}-${name}`;
    return {
      id,
      error,
      inputProps: {
        id,
        "aria-invalid": error ? true : undefined,
        "aria-describedby": error ? `${id}-error` : undefined,
      },
    };
  };

  const Err = ({ f }: { f: ReturnType<typeof field> }) =>
    f.error ? (
      <div id={`${f.id}-error`} className="invalid-feedback d-block">
        {f.error.message}
      </div>
    ) : null;

  const name = field("name");
  const email = field("email");
  const company = field("company");
  const phone = field("phone");
  const service = field("service");
  const message = field("message");
  const privacy = field("privacy_accepted");
  const marketing = field("marketing_opt_in");

  const cls = (f: ReturnType<typeof field>, base = "form-control") =>
    `${base}${f.error ? " is-invalid" : ""}`;

  return (
    <form className="row g-3 mx-auto contact-form" onSubmit={onSubmit} noValidate>
      <div role="status" aria-live="polite" className="col-12">
        {status.kind === "success" && (
          <div className="alert alert-success mb-0">
            ¡Gracias! Recibimos tu mensaje y te responderemos pronto.
          </div>
        )}
        {status.kind === "error" && (
          <div className="alert alert-danger mb-0">{status.message}</div>
        )}
      </div>

      <div className="col-md-6">
        <label htmlFor={name.id} className="form-label">
          Nombre <span aria-hidden="true">*</span>
        </label>
        <input
          {...register("name")}
          {...name.inputProps}
          className={cls(name)}
          autoComplete="name"
          aria-required="true"
        />
        <Err f={name} />
      </div>
      <div className="col-md-6">
        <label htmlFor={email.id} className="form-label">
          Correo electrónico <span aria-hidden="true">*</span>
        </label>
        <input
          {...register("email")}
          {...email.inputProps}
          type="email"
          className={cls(email)}
          autoComplete="email"
          aria-required="true"
        />
        <Err f={email} />
      </div>
      <div className="col-md-6">
        <label htmlFor={company.id} className="form-label">
          Empresa
        </label>
        <input
          {...register("company")}
          {...company.inputProps}
          className={cls(company)}
          autoComplete="organization"
        />
        <Err f={company} />
      </div>
      <div className="col-md-6">
        <label htmlFor={phone.id} className="form-label">
          Teléfono
        </label>
        <input
          {...register("phone")}
          {...phone.inputProps}
          type="tel"
          className={cls(phone)}
          autoComplete="tel"
          placeholder="+56 9 1234 5678"
        />
        <Err f={phone} />
      </div>
      <div className="col-12">
        <label htmlFor={service.id} className="form-label">
          Servicio de interés
        </label>
        <select {...register("service")} {...service.inputProps} className={cls(service, "form-select")}>
          <option value="">Selecciona una opción (opcional)</option>
          {services.map((s) => (
            <option key={s.slug} value={s.slug}>
              {s.title}
            </option>
          ))}
        </select>
      </div>
      <div className="col-12">
        <label htmlFor={message.id} className="form-label">
          Mensaje <span aria-hidden="true">*</span>
        </label>
        <textarea
          {...register("message")}
          {...message.inputProps}
          rows={5}
          className={cls(message)}
          aria-required="true"
        />
        <Err f={message} />
      </div>

      {/* Honeypot: invisible para personas, los bots lo completan. */}
      <div className="hp-field" aria-hidden="true">
        <label htmlFor={`${uid}-website`}>No completar</label>
        <input {...register("website")} id={`${uid}-website`} tabIndex={-1} autoComplete="off" />
      </div>

      <div className="col-12">
        <div className="form-check">
          <input
            {...register("privacy_accepted")}
            {...privacy.inputProps}
            type="checkbox"
            className={cls(privacy, "form-check-input")}
            aria-required="true"
          />
          <label htmlFor={privacy.id} className="form-check-label">
            He leído y acepto la <Link to="/privacidad">Política de Privacidad</Link>.{" "}
            <span aria-hidden="true">*</span>
          </label>
          <Err f={privacy} />
        </div>
        <div className="form-check mt-2">
          <input
            {...register("marketing_opt_in")}
            {...marketing.inputProps}
            type="checkbox"
            className="form-check-input"
          />
          <label htmlFor={marketing.id} className="form-check-label">
            Quiero recibir novedades y contenidos de Will-Webs (opcional).
          </label>
        </div>
        <p className="form-text mb-0 mt-2">
          Usamos tus datos solo para responder tu consulta. Puedes ejercer tus derechos de acceso,
          rectificación y supresión según la Política de Privacidad.
        </p>
      </div>

      <div className="col-12">
        <Turnstile onToken={onToken} resetSignal={captchaReset} />
      </div>

      <div className="col-12">
        <button type="submit" className="btn btn-brand btn-lg" disabled={mutation.isPending}>
          {mutation.isPending ? "Enviando…" : "Enviar mensaje"}
        </button>
        <p className="form-text mt-2 mb-0">
          <span aria-hidden="true">*</span> Campos obligatorios
        </p>
      </div>
    </form>
  );
}
