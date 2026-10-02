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
  isAuthenticated: boolean;
  login: (token: string, userType: string, permissions: string[]) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem("session_token")
  );
  const [userType, setUserType] = useState<string | null>(
    () => localStorage.getItem("user_type")
  );
  const [permissions, setPermissions] = useState<string[]>(() => {
    const raw = localStorage.getItem("permissions");
    return raw ? JSON.parse(raw) : [];
  });

  const login = useCallback((newToken: string, type: string, perms: string[]) => {
    localStorage.setItem("session_token", newToken);
    localStorage.setItem("user_type", type);
    localStorage.setItem("permissions", JSON.stringify(perms || []));
    setToken(newToken);
    setUserType(type);
    setPermissions(perms || []);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("session_token");
    localStorage.removeItem("user_type");
    localStorage.removeItem("permissions");
    setToken(null);
    setUserType(null);
    setPermissions([]);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        token,
        userType,
        permissions,
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
