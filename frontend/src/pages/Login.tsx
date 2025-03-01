import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api/auth";
import { useAuth } from "../context/AuthContext";

function Login() {
  const [uid, setUidInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { setUid, setToken, token } = useAuth();

  // Redirect if already logged in
  if (token) navigate("/chat");

  const handleLogin = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await login(uid);
      if (response.token && response.uid) {
        setToken(response.token);
        setUid(response.uid);
        localStorage.setItem("token", response.token);
        localStorage.setItem("uid", response.uid);
        navigate("/chat");
      }
    } catch (error) {
      setError("Login failed. Please check your UID.");
      console.error("Login failed", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Login</h1>
      {error && <p style={{ color: "red" }}>{error}</p>}
      <input type="text" placeholder="Enter UID" onChange={(e) => setUidInput(e.target.value)} />
      <button onClick={handleLogin} disabled={loading}>
        {loading ? "Logging in..." : "Login"}
      </button>
    </div>
  );
}

export default Login;