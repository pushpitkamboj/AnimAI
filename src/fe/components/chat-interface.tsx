"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import MessageItem from "./message-item"
import { Send } from "lucide-react"

interface Message {
  id: string
  text: string
  timestamp: Date
  videoUrl?: string
  isResponse?: boolean
}

interface ChatInterfaceProps {
  messages: Message[]
  onSendMessage: (message: string) => void
  onEditMessage: (id: string, newText: string) => void
  onDeleteMessage: (id: string) => void
  onPlayVideo: (url: string) => void
}

export default function ChatInterface({
  messages,
  onSendMessage,
  onEditMessage,
  onDeleteMessage,
  onPlayVideo,
}: ChatInterfaceProps) {
  const [inputValue, setInputValue] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!inputValue.trim()) return

    setIsLoading(true)
    const message = inputValue
    setInputValue("")

    try {
      await onSendMessage(message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-full bg-slate-950">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-2xl">✨</span>
              </div>
              <p className="text-slate-400 text-lg">Start creating animations</p>
              <p className="text-slate-500 text-sm mt-2">Describe what you want to animate</p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <MessageItem
              key={message.id}
              message={message}
              onEdit={onEditMessage}
              onDelete={onDeleteMessage}
              onPlayVideo={onPlayVideo}
            />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-slate-800 p-4 bg-slate-900">
        <div className="flex gap-3">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe your animation..."
            className="flex-1 bg-slate-800 text-white placeholder-slate-500 rounded-lg px-4 py-3 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 border border-slate-700"
            rows={3}
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !inputValue.trim()}
            className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg px-4 py-3 flex items-center justify-center transition-all"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  )
}
