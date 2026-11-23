import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import * as api from "./api";

type State =
  | { status: "loading" }
  | { status: "anonymous"; reason?: string }
  | { status: "authenticated"; user: api.AdminUser };

interface AuthValue {
  state: State;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (role: string) => boolean;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    api.setSessionLostHandler(() =>
      setState({ status: "anonymous", reason: "Tu sesión expiró. Ingresa nuevamente." }),
    );
    // Restaurar sesión desde la cookie HttpOnly (si existe).
    api.refreshSession().then((user) =>
      setState(user ? { status: "authenticated", user } : { status: "anonymous" }),
    );
    return () => api.setSessionLostHandler(null);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const user = await api.login(email, password);
    setState({ status: "authenticated", user });
  }, []);

  const logout = useCallback(async () => {
    await api.logout();
    setState({ status: "anonymous" });
  }, []);

  const value = useMemo<AuthValue>(
    () => ({
      state,
      login,
      logout,
      hasRole: (role) => state.status === "authenticated" && state.user.roles.includes(role),
    }),
    [state, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth fuera de AuthProvider");
  return ctx;
}
