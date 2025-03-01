import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { signup } from "../api/auth";

function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleSignup = async () => {
    try {
      const response = await signup(email, password);
      if (response.uid) {
        alert(`Signup successful! Your UID: ${response.uid}`);
        navigate("/login");
      }
    } catch (error) {
      console.error("Signup failed", error);
    }
  };

  return (
    <div>
      <h1>Signup</h1>
      <input type="email" placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
      <input type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} />
      <button onClick={handleSignup}>Signup</button>
    </div>
  );
}

export default Signup;