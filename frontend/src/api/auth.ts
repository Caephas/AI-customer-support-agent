import axios from "axios";

const API_BASE = "http://127.0.0.1:8000/api/v1/auth";

export const signup = async (email: string, password: string) => {
  const response = await axios.post(`${API_BASE}/signup`, { email, password });
  return response.data; // Should return { uid }
};

export const login = async (uid: string) => {
  const response = await axios.post(`${API_BASE}/login`, { uid });
  return response.data; // Should return { token, uid }
};