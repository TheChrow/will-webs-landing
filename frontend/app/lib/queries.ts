import { QueryClient, useQuery } from "@tanstack/react-query";

import { api, type ContentBlock, type LegalType } from "./api";
import { FALLBACK_CONTENT, FALLBACK_SERVICES, FALLBACK_SETTINGS } from "./fallback";

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // la API cachea 5 min
        retry: 1,
        refetchOnWindowFocus: false,
      },
    },
  });
}

// placeholderData (no initialData): el pre-render y la hidratación muestran el respaldo,
// y luego el cliente siempre consulta la API.
export const useServices = () =>
  useQuery({ queryKey: ["services"], queryFn: api.services, placeholderData: FALLBACK_SERVICES });

export const useBanners = () => useQuery({ queryKey: ["banners"], queryFn: api.banners });

export const useClients = () => useQuery({ queryKey: ["clients"], queryFn: api.clients });

export const useSettings = () =>
  useQuery({ queryKey: ["settings"], queryFn: api.settings, placeholderData: FALLBACK_SETTINGS });

export const useContent = () =>
  useQuery({
    queryKey: ["content"],
    queryFn: () => api.content(),
    placeholderData: FALLBACK_CONTENT,
    select: (blocks: ContentBlock[]) => Object.fromEntries(blocks.map((b) => [b.key, b])),
  });

export const useLegal = (type: LegalType) =>
  useQuery({ queryKey: ["legal", type], queryFn: () => api.legal(type), retry: false });
