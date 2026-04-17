"use client";

import { useState, useRef, useEffect } from "react";
import { Send, X, MessageCircle } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ChatbotProps {
  userId: string;
  charName?: string;
  isOpen?: boolean;
  onClose?: () => void;
}

export default function AIChatbot({
  userId,
  charName,
  isOpen: initialIsOpen = false,
  onClose,
}: ChatbotProps) {
  const [isOpen, setIsOpen] = useState(initialIsOpen);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 스크롤을 항상 최하단으로 유지
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 채팅창 열고 닫기
  const handleToggle = () => {
    setIsOpen(!isOpen);
  };

  const handleClose = () => {
    setIsOpen(false);
    onClose?.();
  };

  // 메시지 전송
  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    // 사용자 메시지 추가
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setError("");
    setIsLoading(true);

    try {
      // API 호출
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8002";
      const response = await fetch(`${apiUrl}/api/v1/ai/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
          message: input,
          char_name: charName || null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "요청 처리 실패");
      }

      const data = await response.json();

      // AI 응답 메시지 추가
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "요청 실패";
      setError(errorMsg);

      // 에러 메시지 표시
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: `죄송합니다. ${errorMsg}`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Enter 키로 전송
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* 채팅 버튼 (닫혀있을 때) */}
      {!isOpen && (
        <button
          onClick={handleToggle}
          className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center transition-all duration-200 hover:scale-110 z-40"
          aria-label="AI 챗봇 열기"
          title="AI 챗봇"
        >
          <MessageCircle size={24} />
        </button>
      )}

      {/* 채팅창 (열려있을 때) */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[500px] bg-white rounded-lg shadow-2xl flex flex-col z-50 border border-gray-200">
          {/* 헤더 */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 rounded-t-lg flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MessageCircle size={20} />
              <h3 className="font-semibold">메이플봇</h3>
            </div>
            <button
              onClick={handleClose}
              className="hover:bg-blue-800 p-1 rounded transition-colors"
              aria-label="닫기"
            >
              <X size={20} />
            </button>
          </div>

          {/* 메시지 영역 */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {messages.length === 0 && !error && (
              <div className="flex items-center justify-center h-full text-center">
                <div className="text-gray-500">
                  <MessageCircle size={32} className="mx-auto mb-2 opacity-50" />
                  <p className="text-sm mb-2">안녕하세요!</p>
                  <p className="text-xs">
                    보스 수익 분석, 체크리스트 복제 등
                    <br />
                    무엇을 도와드릴까요?
                  </p>
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-xs px-4 py-2 rounded-lg ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white rounded-br-none"
                      : "bg-gray-200 text-gray-800 rounded-bl-none"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap break-words">
                    {msg.content}
                  </p>
                  <p
                    className={`text-xs mt-1 ${
                      msg.role === "user"
                        ? "text-blue-100"
                        : "text-gray-500"
                    }`}
                  >
                    {msg.timestamp.toLocaleTimeString("ko-KR", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-200 text-gray-800 px-4 py-2 rounded-lg rounded-bl-none">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce delay-100"></div>
                    <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce delay-200"></div>
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
                {error}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* 입력 영역 */}
          <div className="border-t border-gray-200 p-4 bg-white rounded-b-lg">
            <div className="flex gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="메시지를 입력하세요... (Shift+Enter: 줄바꿈)"
                className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                rows={3}
                disabled={isLoading}
              />
              <button
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded px-4 py-2 flex items-center justify-center transition-colors"
                aria-label="전송"
              >
                <Send size={18} />
              </button>
            </div>
            {charName && (
              <p className="text-xs text-gray-500 mt-2">
                캐릭터: <span className="font-semibold">{charName}</span>
              </p>
            )}
          </div>
        </div>
      )}
    </>
  );
}
