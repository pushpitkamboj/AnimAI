"use client"

import { useState } from "react"
import TopBar from "@/components/top-bar"
import ChatInterface from "@/components/chat-interface"
import VideoModal from "@/components/video-modal"

interface Message {
  id: string
  text: string
  timestamp: Date
  videoUrl?: string
  isResponse?: boolean
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [selectedVideoUrl, setSelectedVideoUrl] = useState<string | null>(null)

  const handleSendMessage = async (message: string) => {
    // Add user message to chat
    const userMessage: Message = {
      id: Date.now().toString(),
      text: message,
      timestamp: new Date(),
      isResponse: false,
    }
    setMessages((prev) => [...prev, userMessage])

    try {
      const response = await fetch("http://localhost:8000/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: message }),
      })

      const data = await response.json()

      if (data.status === 200 && data.result) {
        const responseMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: "Animation generated successfully",
          timestamp: new Date(),
          videoUrl: data.result,
          isResponse: true,
        }
        setMessages((prev) => [...prev, responseMessage])
      } else {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: "Failed to generate animation. Please try with smaller and consize prompts, sorry for inconvinience",
          timestamp: new Date(),
          isResponse: true,
        }
        setMessages((prev) => [...prev, errorMessage])
      }
    } catch (error) {
      console.error("Error fetching video:", error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "Error: Could not connect to the server.",
        timestamp: new Date(),
        isResponse: true,
      }
      setMessages((prev) => [...prev, errorMessage])
    }
  }

  const handleEditMessage = (id: string, newText: string) => {
    setMessages(messages.map((msg) => (msg.id === id ? { ...msg, text: newText } : msg)))
  }

  const handleDeleteMessage = (id: string) => {
    setMessages(messages.filter((msg) => msg.id !== id))
  }

  return (
    <div className="flex flex-col h-screen bg-slate-950">
      <TopBar />
      <div className="flex-1 overflow-hidden">
        <ChatInterface
          messages={messages}
          onSendMessage={handleSendMessage}
          onEditMessage={handleEditMessage}
          onDeleteMessage={handleDeleteMessage}
          onPlayVideo={setSelectedVideoUrl}
        />
      </div>

      {selectedVideoUrl && <VideoModal videoUrl={selectedVideoUrl} onClose={() => setSelectedVideoUrl(null)} />}
    </div>
  )
}
