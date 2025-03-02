import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login as apiLogin } from "../api/auth"; // Alias to avoid conflict
import { useAuth } from "../context/AuthContext";

function Login() {
  const [uid, setUidInput] = useState("");
  const navigate = useNavigate();
  const { login } = useAuth(); // Correct function from AuthContext

  const handleLogin = async () => {
    try {
      const response = await apiLogin(uid);
      if (response.token && response.uid) {
        login(response.uid, response.token); // Use `login` instead of setUid/setToken
        localStorage.setItem("token", response.token);
        localStorage.setItem("uid", response.uid);
        navigate("/chat");
      }
    } catch (error) {
      console.error("Login failed", error);
    }
  };

  return (
    <div>
      <h1>Login</h1>
      <input
        type="text"
        placeholder="Enter UID"
        value={uid}
        onChange={(e) => setUidInput(e.target.value)}
      />
      <button onClick={handleLogin}>Login</button>
    </div>
  );
}

export default Login;