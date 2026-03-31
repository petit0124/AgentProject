import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { Send, Upload, FileText, Bot, User, Loader2 } from 'lucide-react'
import './App.css'

const API_BASE = 'http://localhost:8000/api'

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '你好！我是你的智能助手。你可以上传文档，或者直接向我提问。我会结合文档内容和网络搜索为你寻找答案。' }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Prepare history for backend (excluding current message which is sent separately in this specialized backend, 
      // but typically we send all. The backend expects {message, history})
      const history = messages.map(m => ({ role: m.role, content: m.content }))

      const response = await axios.post(`${API_BASE}/chat`, {
        message: userMessage.content,
        history: history
      })

      const aiMessage = { role: 'assistant', content: response.data.response }
      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      setMessages(prev => [...prev, { role: 'assistant', content: '抱歉，遇到了一些问题，请稍后再试。' }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      await axios.post(`${API_BASE}/upload`, formData)
      setMessages(prev => [...prev, { role: 'assistant', content: `📄 文档 "${file.name}" 上传成功并已处理完毕。` }])
    } catch (error) {
      console.error('Error uploading file:', error)
      setMessages(prev => [...prev, { role: 'assistant', content: `❌ 文档 "${file.name}" 上传失败。` }])
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  return (
    <div className="chat-container">
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <h1 style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '1.5rem', fontWeight: 'bold' }}>
          <Bot size={32} className="text-blue-500" />
          Agentic RAG 助手
        </h1>
        <div>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleUpload}
            style={{ display: 'none' }}
            id="file-upload"
          />
          <label htmlFor="file-upload">
            <button
              as="span"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              {uploading ? <Loader2 className="animate-spin" size={18} /> : <Upload size={18} />}
              上传文档
            </button>
          </label>
        </div>
      </header>

      <div className="messages-area">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div style={{ marginTop: '4px' }}>
              {msg.role === 'user' ? <User size={24} /> : <Bot size={24} className="text-blue-500" />}
            </div>
            <div className="message-bubble">
              <div className="markdown-content">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message assistant">
            <div style={{ marginTop: '4px' }}><Bot size={24} className="text-blue-500" /></div>
            <div className="message-bubble">
              <Loader2 className="animate-spin" size={20} />
              <span style={{ marginLeft: '8px' }}>思考中...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="请输入你的问题..."
          disabled={isLoading}
        />
        <button onClick={handleSend} disabled={isLoading || !input.trim()}>
          <Send size={18} />
        </button>
      </div>
    </div>
  )
}

export default App
