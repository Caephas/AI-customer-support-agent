import React, { createContext, useState, useContext, ReactNode, useEffect } from "react";

interface AuthContextType {
  uid: string | null;
  token: string | null;
  setUid: (uid: string | null) => void;
  setToken: (token: string | null) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [uid, setUid] = useState<string | null>(localStorage.getItem("uid"));
  const [token, setToken] = useState<string | null>(localStorage.getItem("token"));

  useEffect(() => {
    if (uid) localStorage.setItem("uid", uid);
    if (token) localStorage.setItem("token", token);
  }, [uid, token]);

  const logout = () => {
    setUid(null);
    setToken(null);
    localStorage.removeItem("uid");
    localStorage.removeItem("token");
    localStorage.removeItem("chatMessages");
    window.location.href = "/login";
  };

  return (
    <AuthContext.Provider value={{ uid, token, setUid, setToken, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
};