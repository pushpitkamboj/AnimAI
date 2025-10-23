"use client"

import { X } from "lucide-react"
import ReactPlayer from "react-player"

interface VideoModalProps {
  videoUrl: string
  onClose: () => void
}

export default function VideoModal({ videoUrl, onClose }: VideoModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-900 rounded-lg w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header with Close Button */}
        <div className="border-b border-slate-800 px-6 py-4 flex items-center justify-between">
          <h2 className="text-white font-semibold">Animation Player</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-white"
          >
            <X size={24} />
          </button>
        </div>

        {/* Video Player */}
        <div className="flex-1 flex items-center justify-center bg-black overflow-hidden">
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
      </div>
    </div>
  )
}
