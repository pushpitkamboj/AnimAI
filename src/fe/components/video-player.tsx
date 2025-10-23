"use client"

import { useState } from "react"
import ReactPlayer from "react-player"
import { Copy, Check } from "lucide-react"

interface VideoPlayerProps {
  videoUrl: string | null
}

export default function VideoPlayer({ videoUrl }: VideoPlayerProps) {
  const [copied, setCopied] = useState(false)

  const handleCopyUrl = () => {
    if (videoUrl) {
      navigator.clipboard.writeText(videoUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="flex flex-col h-full bg-slate-900">
      {/* Header with Copy Button */}
      <div className="border-b border-slate-800 px-4 py-3 flex items-center justify-between">
        <h2 className="text-white font-semibold">Generated Animation</h2>
        {videoUrl && (
          <button
            onClick={handleCopyUrl}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-3 py-2 rounded-lg transition-colors text-sm"
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
        )}
      </div>

      {/* Video Player Area */}
      <div className="flex-1 flex items-center justify-center bg-black">
        {videoUrl ? (
          <div className="w-full h-full flex items-center justify-center">
            <ReactPlayer
              url={videoUrl}
              controls
              width="100%"
              height="100%"
              playing={false}
              config={{
                file: {
                  attributes: {
                    controlsList: "nodownload",
                  },
                },
              }}
            />
          </div>
        ) : (
          <div className="text-center">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-white text-3xl">🎬</span>
            </div>
            <p className="text-slate-400 text-lg">No animation yet</p>
            <p className="text-slate-500 text-sm mt-2">Send a prompt to generate an animation</p>
          </div>
        )}
      </div>
    </div>
  )
}
