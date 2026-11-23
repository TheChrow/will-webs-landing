import {
  Code,
  Globe,
  LifeBuoy,
  type LucideIcon,
  Mail,
  Plug,
  Server,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Workflow,
} from "lucide-react";

// Solo se importan los íconos usados (tree-shaking).
const ICONS: Record<string, LucideIcon> = {
  workflow: Workflow,
  code: Code,
  plug: Plug,
  sparkles: Sparkles,
  server: Server,
  mail: Mail,
  globe: Globe,
  "shield-check": ShieldCheck,
  "trending-up": TrendingUp,
  "life-buoy": LifeBuoy,
};

export function ServiceIcon({ name }: { name: string | null }) {
  const Icon = (name && ICONS[name]) || Sparkles;
  return (
    <span className="service-icon mb-3" aria-hidden="true">
      <Icon size={22} strokeWidth={2} />
    </span>
  );
}
