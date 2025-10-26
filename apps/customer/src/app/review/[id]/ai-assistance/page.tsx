"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

interface Message {
  id: string;
  text: string;
  sender: "ai" | "user";
  timestamp: Date;
}

export default function AIAssistancePage() {
  const params = useParams();
  const reviewId = params.id as string;

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      text: "Hi! I'm sorry to hear your experience wasn't what we hoped for. I'm here to help make things right. Can you tell me more about what went wrong?",
      sender: "ai",
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [chatEnded, setChatEnded] = useState(false);

  const sendMessage = async () => {
    if (!inputText.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      sender: "user",
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputText("");
    setIsTyping(true);

    // Simulate AI response (in production, call your AI service API)
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "Thank you for explaining. I completely understand your frustration. Let me issue you a special discount coupon as an apology, and I'll make sure our team addresses this issue.",
        sender: "ai",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsTyping(false);

      // Issue coupon via API
      issueCoupon();
    }, 2000);
  };

  const issueCoupon = async () => {
    try {
      const response = await fetch("/api/reviews/ai/issue-coupon", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          review_id: reviewId,
          ai_interaction_notes: "Customer explained issues, coupon issued as resolution",
          discount_percentage: 10,
        }),
      });

      if (response.ok) {
        const data = await response.json();

        setTimeout(() => {
          const couponMessage: Message = {
            id: (Date.now() + 2).toString(),
            text: `Here's your discount code: ${data.coupon.code} - This gives you 10% off your next booking. It's valid for 90 days and can be used on orders over $50.`,
            sender: "ai",
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, couponMessage]);
          setChatEnded(true);
        }, 1000);
      }
    } catch (error) {
      console.error("Failed to issue coupon:", error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-red-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="text-6xl mb-4">🤖</div>
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            Let&apos;s Make This Right
          </h1>
          <p className="text-gray-600">
            Our AI assistant is here to help resolve your concerns immediately.
          </p>
        </motion.div>

        {/* Chat Container */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-2xl shadow-xl overflow-hidden"
        >
          {/* Chat Messages */}
          <div className="h-96 overflow-y-auto p-6 space-y-4">
            <AnimatePresence>
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
                      message.sender === "user"
                        ? "bg-red-600 text-white"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {message.text}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Typing Indicator */}
            {isTyping && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex justify-start"
              >
                <div className="bg-gray-100 px-4 py-3 rounded-2xl">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.4s" }}></div>
                  </div>
                </div>
              </motion.div>
            )}
          </div>

          {/* Input Area */}
          {!chatEnded ? (
            <div className="border-t border-gray-200 p-4">
              <div className="flex space-x-3">
                <input
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && sendMessage()}
                  placeholder="Type your message..."
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
                <button
                  onClick={sendMessage}
                  disabled={!inputText.trim()}
                  className={`px-6 py-3 rounded-lg font-semibold transition ${
                    inputText.trim()
                      ? "bg-red-600 text-white hover:bg-red-700"
                      : "bg-gray-300 text-gray-500 cursor-not-allowed"
                  }`}
                >
                  Send
                </button>
              </div>
            </div>
          ) : (
            <div className="border-t border-gray-200 p-6 bg-green-50">
              <div className="text-center">
                <div className="text-4xl mb-3">✅</div>
                <h3 className="text-xl font-semibold text-gray-800 mb-2">
                  Issue Resolved!
                </h3>
                <p className="text-gray-600 mb-4">
                  Your discount coupon has been issued. We hope to serve you better next time!
                </p>
                <a
                  href="/booking"
                  className="inline-block bg-red-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-red-700 transition"
                >
                  Book Your Next Event
                </a>
              </div>
            </div>
          )}
        </motion.div>

        {/* Info Box */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-6"
        >
          <h3 className="font-semibold text-gray-800 mb-2 flex items-center">
            <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            About Our AI Assistant
          </h3>
          <p className="text-sm text-gray-700">
            Our AI assistant can resolve most concerns immediately. If the issue requires human
            attention, it will automatically escalate to our customer service team. Your satisfaction
            is our priority! 🎯
          </p>
        </motion.div>
      </div>
    </div>
  );
}
