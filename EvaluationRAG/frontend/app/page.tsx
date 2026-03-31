import Image from "next/image";
import UploadComponent from "@/components/Upload";
import ChatComponent from "@/components/Chat";
import DashboardComponent from "@/components/Dashboard";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-indigo-50 via-blue-50 to-white text-gray-800 p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        <header className="flex flex-col items-center text-center space-y-4 py-8">
          <div className="w-16 h-16 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/30 transform rotate-3">
            <span className="text-3xl font-bold text-white">R</span>
          </div>
          <div>
            <h1 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-700 to-indigo-700">
              智能评估 RAG 系统
            </h1>
            <p className="mt-2 text-gray-500 max-w-lg mx-auto">
              上传文档，进行对话，并自动生成专业的评估报告。
            </p>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Upload (Smaller) */}
          <div className="lg:col-span-4 space-y-8">
            <UploadComponent />
          </div>

          {/* Right Column: Chat (Larger) */}
          <div className="lg:col-span-8">
            <ChatComponent />
          </div>
        </div>

        {/* Bottom Section: Dashboard (Full Width) */}
        <div className="w-full">
          <DashboardComponent />
        </div>
      </div>
    </main>
  );
}
