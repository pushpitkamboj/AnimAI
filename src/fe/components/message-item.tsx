"use client"

import { useState } from "react"
import { Edit2, Trash2, Check, X, Copy, Play } from "lucide-react"

interface Message {
  id: string
  text: string
  timestamp: Date
  videoUrl?: string
  isResponse?: boolean
}

interface MessageItemProps {
  message: Message
  onEdit: (id: string, newText: string) => void
  onDelete: (id: string) => void
  onPlayVideo: (url: string) => void
}

export default function MessageItem({ message, onEdit, onDelete, onPlayVideo }: MessageItemProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editText, setEditText] = useState(message.text)
  const [copied, setCopied] = useState(false)

  const handleSaveEdit = () => {
    if (editText.trim()) {
      onEdit(message.id, editText)
      setIsEditing(false)
    }
  }

  const handleCancelEdit = () => {
    setEditText(message.text)
    setIsEditing(false)
  }

  const handleCopyUrl = () => {
    if (message.videoUrl) {
      navigator.clipboard.writeText(message.videoUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  return (
    <div className={`rounded-lg p-4 transition-colors group ${message.isResponse ? "bg-slate-800" : "bg-slate-700"}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          {isEditing ? (
            <textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              className="w-full bg-slate-900 text-white rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 border border-slate-600"
              rows={2}
            />
          ) : (
            <p className="text-white text-sm leading-relaxed">{message.text}</p>
          )}
          <p className="text-slate-500 text-xs mt-2">{formatTime(message.timestamp)}</p>

          {message.isResponse && message.videoUrl && (
            <div className="flex gap-2 mt-3">
              <button
                onClick={handleCopyUrl}
                className="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 text-white px-3 py-2 rounded-lg transition-colors text-sm"
              >
                {copied ? (
                  <>
                    <Check size={16} />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy size={16} />
                    Copy URL
                  </>
                )}
              </button>
              <button
                onClick={() => onPlayVideo(message.videoUrl!)}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg transition-colors text-sm"
              >
                <Play size={16} />
                Display Video
              </button>
            </div>
          )}
        </div>

        {/* Edit/Delete buttons for user messages */}
        {!message.isResponse && (
          <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            {isEditing ? (
              <>
                <button
                  onClick={handleSaveEdit}
                  className="p-2 hover:bg-slate-600 rounded transition-colors text-green-400"
                >
                  <Check size={16} />
                </button>
                <button
                  onClick={handleCancelEdit}
                  className="p-2 hover:bg-slate-600 rounded transition-colors text-red-400"
                >
                  <X size={16} />
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setIsEditing(true)}
                  className="p-2 hover:bg-slate-600 rounded transition-colors text-blue-400"
                >
                  <Edit2 size={16} />
                </button>
                <button
                  onClick={() => onDelete(message.id)}
                  className="p-2 hover:bg-slate-600 rounded transition-colors text-red-400"
                >
                  <Trash2 size={16} />
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
