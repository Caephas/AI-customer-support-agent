import { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface AuthContextType {
  user_id: string;
  token: string;
  login: (userId: string, jwtToken: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user_id, setUserId] = useState(localStorage.getItem("user_id") || "");
  const [token, setToken] = useState(localStorage.getItem("token") || "");

  useEffect(() => {
    localStorage.setItem("user_id", user_id);
    localStorage.setItem("token", token);
  }, [user_id, token]);

  const login = (userId: string, jwtToken: string) => {
    setUserId(userId);
    setToken(jwtToken);
  };

  const logout = () => {
    setUserId("");
    setToken("");
    localStorage.removeItem("user_id");
    localStorage.removeItem("token");
  };

  return (
    <AuthContext.Provider value={{ user_id, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};