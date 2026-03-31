# 评估 RAG 系统

基于 FastAPI + Next.js 的智能评估 RAG 系统

## 快速启动

### 方法 1: 一键启动 (推荐)

**Windows 批处理:**
```bash
start.bat
```

**PowerShell:**
```powershell
.\start.ps1
```

### 方法 2: 手动启动

**后端:**
```bash
cd backend
python main.py
```

**前端:**
```bash
cd frontend
npm run dev
```

## 访问地址

- 前端界面: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 功能特性

- ✅ 文档上传 (PDF, DOCX, PPT, Excel, TXT, MD)
- ✅ RAG 智能问答 (基于 Azure OpenAI)
- ✅ RAGAS 自动评测
- ✅ 可视化评估仪表盘

## 技术栈

- **前端**: Next.js 16, Tailwind CSS, Recharts
- **后端**: Python 3.13, FastAPI, LangChain 1.2
- **向量库**: ChromaDB
- **评估**: RAGAS 0.4.2

## 环境要求

- Python 3.13+
- Node.js 18+
- Azure OpenAI API Key

## 配置

确保 `backend/.env` 文件包含正确的 Azure OpenAI 配置。

详细文档请查看 `walkthrough.md`
