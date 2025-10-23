export default function TopBar() {
  return (
    <div className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
          <span className="text-white font-bold text-lg">A</span>
        </div>
        <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
          AnimAI
        </h1>
      </div>
      <p className="text-slate-400 text-sm">AI-Powered Animation Generator</p>
    </div>
  )
}
