import {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from "react";

interface AuthState {
  token: string | null;
  userType: string | null;
  permissions: string[];
  eventId: string | null;
  isAuthenticated: boolean;
  login: (token: string, userType: string, permissions: string[], eventId: string | null) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("session_token"));
  const [userType, setUserType] = useState<string | null>(() => localStorage.getItem("user_type"));
  const [eventId, setEventId] = useState<string | null>(() => localStorage.getItem("event_id"));
  const [permissions, setPermissions] = useState<string[]>(() => {
    const raw = localStorage.getItem("permissions");
    return raw ? JSON.parse(raw) : [];
  });

  const login = useCallback(
    (newToken: string, type: string, perms: string[], evId: string | null) => {
      localStorage.setItem("session_token", newToken);
      localStorage.setItem("user_type", type);
      localStorage.setItem("permissions", JSON.stringify(perms || []));
      if (evId) localStorage.setItem("event_id", evId);
      else localStorage.removeItem("event_id");
      setToken(newToken);
      setUserType(type);
      setPermissions(perms || []);
      setEventId(evId);
    },
    []
  );

  const logout = useCallback(() => {
    localStorage.removeItem("session_token");
    localStorage.removeItem("user_type");
    localStorage.removeItem("permissions");
    localStorage.removeItem("event_id");
    setToken(null);
    setUserType(null);
    setPermissions([]);
    setEventId(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        token,
        userType,
        permissions,
        eventId,
        isAuthenticated: Boolean(token),
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
