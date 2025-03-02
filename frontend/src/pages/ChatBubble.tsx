import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function ChatBubble({ sender, text, timestamp }: { sender: string; text: string; timestamp: string }) {
  return (
    <div
      style={{
        textAlign: sender === "You" ? "right" : "left",
        background: sender === "You" ? "#d1e7ff" : "#f1f1f1",
        padding: "8px",
        margin: "4px 0",
        borderRadius: "8px",
        maxWidth: "80%",
        display: "inline-block",
      }}
    >
      <b>{sender}:</b>
      {/* Render Markdown instead of plain text */}
      <div style={{ marginTop: "4px", whiteSpace: "pre-wrap" }}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {text}
        </ReactMarkdown>
      </div>
      <small style={{ display: "block", fontSize: "10px", color: "gray", marginTop: "4px" }}>
        {timestamp}
      </small>
    </div>
  );
}

export default ChatBubble;