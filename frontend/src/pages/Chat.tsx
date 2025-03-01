import { useState, useEffect, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import axios from "axios";

function Chat() {
  const { uid, token, logout } = useAuth();
  const [messages, setMessages] = useState<{ sender: string; text: string; timestamp: string }[]>([]);
  const [input, setInput] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to latest message
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);
  useEffect(() => {
    const storedMessages = localStorage.getItem("chatMessages");
    if (storedMessages) {
      setMessages(JSON.parse(storedMessages));
    }
  }, []);
  
  useEffect(() => {
    localStorage.setItem("chatMessages", JSON.stringify(messages));
  }, [messages]);
  const sendMessage = async () => {
    if (!input.trim()) return;

    const timestamp = new Date().toLocaleTimeString();
    setMessages((prev) => [...prev, { sender: "You", text: input, timestamp }]);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/api/v1/chat",
        { message: input, uid },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setMessages((prev) => [...prev, { sender: "Bot", text: response.data.reply, timestamp }]);
    } catch (error) {
      console.error("Error sending message:", error);
    }

    setInput("");
  };

  return (
    <div>
      <h1>Chat</h1>
      <button onClick={logout} style={{ float: "right" }}>Logout</button>
      <div style={{ height: "300px", overflowY: "scroll", border: "1px solid #ddd", padding: "10px" }}>
        {messages.map((msg, index) => (
          <div key={index} style={{
            textAlign: msg.sender === "You" ? "right" : "left",
            background: msg.sender === "You" ? "#d1e7ff" : "#f1f1f1",
            padding: "8px",
            margin: "4px 0",
            borderRadius: "8px",
            maxWidth: "70%",
            display: "inline-block"
          }}>
            <b>{msg.sender}:</b> {msg.text}
            <small style={{ display: "block", fontSize: "10px", color: "gray" }}>{msg.timestamp}</small>
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>
      <input type="text" placeholder="Type a message..." value={input} onChange={(e) => setInput(e.target.value)} />
      <button onClick={sendMessage}>Send</button>
    </div>
  );
}

export default Chat;