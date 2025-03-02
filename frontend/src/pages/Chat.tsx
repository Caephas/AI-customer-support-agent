import { useState, useEffect, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import ChatBubble from "./ChatBubble";

const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

function Chat() {
  const { user_id, token, logout } = useAuth();
  const [messages, setMessages] = useState<{ sender: string; text: string; timestamp: string }[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const storedMessages = localStorage.getItem("chatMessages");
    if (storedMessages) {
      setMessages(JSON.parse(storedMessages));
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("chatMessages", JSON.stringify(messages));
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const timestamp = new Date().toLocaleTimeString();
    setMessages((prev) => [...prev, { sender: "You", text: input, timestamp }]);
    setLoading(true);

    // Show typing indicator
    setMessages((prev) => [...prev, { sender: "Bot", text: "Processing your request...", timestamp }]);

    try {
      const initialRes = await axios.post(
        `${API_BASE_URL}/chat/query`,
        { user_id, message: input },
        {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        }
      );

      // If there's a task_id, poll; else it's a cached response
      if (initialRes.data.task_id) {
        const finalReply = await pollForResult(initialRes.data.task_id);
        replaceTypingIndicator(finalReply, timestamp);
      } else {
        // It's cached
        const cachedReply = initialRes.data.response || "No cached response found.";
        replaceTypingIndicator(cachedReply, timestamp);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      replaceTypingIndicator("Oops! Something went wrong.", timestamp);
    } finally {
      setLoading(false);
      setInput("");
    }
  };

  const pollForResult = async (taskId: string, interval = 1000, timeout = 30000) => {
    const startTime = Date.now();
    while (true) {
      const statusRes = await axios.get(`${API_BASE_URL}/chat/query/status/${taskId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (statusRes.data.status === "completed") {
        return statusRes.data.response.response || "No final text found.";
      }
      if (Date.now() - startTime > timeout) {
        throw new Error("Timed out waiting for Celery task to complete.");
      }
      await new Promise((resolve) => setTimeout(resolve, interval));
    }
  };

  const replaceTypingIndicator = (reply: string, timestamp: string) => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.text === "Processing your request..."
          ? { sender: "Bot", text: reply, timestamp }
          : msg
      )
    );
  };

  return (
    <div style={{ maxWidth: "600px", margin: "0 auto", fontFamily: "sans-serif" }}>
      <h1>Chat</h1>
      <button onClick={logout} style={{ float: "right", marginBottom: "10px" }}>
        Logout
      </button>

      <div
        style={{
          height: "400px",
          overflowY: "scroll",
          border: "1px solid #ddd",
          padding: "10px",
          borderRadius: "5px",
          marginBottom: "10px",
        }}
      >
        {messages.map((msg, index) => (
          <ChatBubble
            key={index}
            sender={msg.sender}
            text={msg.text}
            timestamp={msg.timestamp}
          />
        ))}
        <div ref={chatEndRef} />
      </div>

      {/* Input + Send button */}
      <div style={{ display: "flex", gap: "10px" }}>
        <input
          type="text"
          placeholder="Type a message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          style={{
            flex: 1,
            padding: "8px",
            borderRadius: "5px",
            border: "1px solid #ccc",
          }}
        />
        <button
          onClick={sendMessage}
          disabled={loading}
          style={{ padding: "8px 16px", borderRadius: "5px" }}
        >
          {loading ? "Thinking..." : "Send"}
        </button>
      </div>
    </div>
  );
}

export default Chat;