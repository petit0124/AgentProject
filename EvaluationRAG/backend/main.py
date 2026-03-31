from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import ingestion
import rag
import evaluate_rag

app = FastAPI(title="Evaluation RAG API")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        file_path = await ingestion.save_upload_file(file)
        num_chunks, chunk_content = ingestion.process_document(file_path)
        return {
            "filename": file.filename, 
            "status": "processed", 
            "chunks": num_chunks,
            "chunk_content": chunk_content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        chain, retriever = rag.get_rag_chain()
        
        # Get relevant documents
        docs = retriever.invoke(request.message)
        
        # Get answer from chain
        answer = chain.invoke(request.message)
        
        # Save to history for evaluation
        rag.add_to_history(request.message, answer, docs)
        
        return {
            "answer": answer,
            "sources": [doc.metadata.get("source", "unknown") for doc in docs]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history():
    return rag.get_chat_history()

@app.post("/evaluate")
async def start_evaluation():
    try:
        history = rag.get_chat_history()
        if not history:
            return {"message": "No history to evaluate"}
        
        results = evaluate_rag.run_evaluation(history)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset")
async def reset_system():
    ingestion.clear_vector_store()
    rag.chat_history_storage.clear()
    return {"status": "System reset"}

import uvicorn
import asyncio

# Use uvicorn.Server directly to avoid 'loop_factory' argument issue with nest_asyncio
config = uvicorn.Config(app, host="0.0.0.0", port=8000)
server = uvicorn.Server(config)
asyncio.run(server.serve())
