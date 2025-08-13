"use client";
import { useEffect, useState } from "react";
import { setTawkVisitor } from "@/lib/tawk";

const KEY = "mh_tawk_email";

export default function TawkEmailPrompt() {
  const [email, setEmail] = useState("");
  const [show, setShow] = useState(false);

  useEffect(() => {
    const saved = typeof window !== "undefined" ? localStorage.getItem(KEY) : null;
    if (!saved) setShow(true);
  }, []);

  function save() {
    if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return;
    localStorage.setItem(KEY, email);
    setTawkVisitor({ email });
    setShow(false);
  }

  if (!show) return null;

  // MyHibachi branded styling
  return (
    <div 
      className="tawk-email-prompt"
      style={{
        position: "fixed", 
        bottom: 80, // Above the tawk widget
        right: 16, 
        padding: 16, 
        background: "#fff", 
        boxShadow: "0 8px 20px rgba(219, 43, 40, 0.15)", 
        borderRadius: 12, 
        zIndex: 9999,
        border: "2px solid rgba(219, 43, 40, 0.1)",
        maxWidth: 280
      }}
    >
      <div style={{
        fontWeight: 600, 
        marginBottom: 8, 
        color: "#db2b28",
        fontSize: "14px"
      }}>
        📧 Get replies by email
      </div>
      <div style={{fontSize: "12px", color: "#666", marginBottom: 12}}>
        We&apos;ll send chat responses to your inbox
      </div>
      <div style={{display: "flex", flexDirection: "column", gap: 8}}>
        <input
          placeholder="your@email.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{
            padding: "8px 12px", 
            border: "1px solid #ddd", 
            borderRadius: 8,
            fontSize: "14px",
            outline: "none",
            borderColor: email ? "#db2b28" : "#ddd"
          }}
          onKeyDown={(e) => e.key === "Enter" && save()}
        />
        <div style={{display: "flex", gap: 8}}>
          <button 
            onClick={save} 
            disabled={!email}
            style={{
              flex: 1,
              padding: "8px 12px", 
              borderRadius: 8, 
              border: "none", 
              background: email ? "#db2b28" : "#ccc",
              color: "#fff",
              fontSize: "12px",
              fontWeight: "600",
              cursor: email ? "pointer" : "not-allowed",
              transition: "all 0.2s ease"
            }}
          >
            Save
          </button>
          <button 
            onClick={() => setShow(false)}
            style={{
              padding: "8px 12px", 
              borderRadius: 8, 
              border: "1px solid #ddd", 
              background: "#f6f6f6",
              color: "#666",
              fontSize: "12px",
              cursor: "pointer"
            }}
          >
            Skip
          </button>
        </div>
      </div>
    </div>
  );
}
