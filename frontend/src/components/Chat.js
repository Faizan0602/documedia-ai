import React, { useState } from "react";
import axios from "axios";
import { BASE_URL } from "../config";

function Chat({ docId }) { // ✅ Add docId prop
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    if (!docId) {
      setMessages((prev) => [...prev, { role: "bot", text: "Please upload a document first!" }]);
      return;
    }

    const userMessage = { role: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const res = await axios.post(`${BASE_URL}/api/v1/chat/`, {
        doc_id: docId,       // ✅ Send doc_id 
        question: input,     // ✅ Send question
      });

      const botMessage = {
        role: "bot",
        text: res.data.answer,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [...prev, { role: "bot", text: "Error getting response" }]);
    }

    setInput("");
    setLoading(false);
  };

  return (
    <div style={{ marginTop: "30px" }}>
      <h2>Chat</h2>
      <div
        style={{
          border: "1px solid #ccc",
          padding: "10px",
          height: "250px",
          overflowY: "auto",
          marginBottom: "10px",
        }}
      >
        {messages.length === 0 && <p>Ask something about your document</p>}
        {messages.map((msg, index) => (
          <div key={index}>
            <strong>{msg.role === "user" ? "You: " : "Bot: "}</strong>
            <pre style={{ whiteSpace: "pre-wrap", display: 'inline' }}>
              {msg.text}
            </pre>
          </div>
        ))}
        {loading && <p>Bot is typing...</p>}
      </div>

      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask something..."
        disabled={!docId}
      />
      <button onClick={handleSend} disabled={!docId}>Send</button>
    </div>
  );
}

export default Chat;