import os
import shutil
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from core.agent import get_agent_graph
from core.rag import process_document
from langchain_core.messages import HumanMessage, AIMessage

# Create uploads directory
os.makedirs("uploads", exist_ok=True)

app = FastAPI(title="Agentic RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = [] # List of {"role": "user"|"assistant", "content": "..."}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    
    # Process the file (Vectorize)
    try:
        num_chunks = await process_document(file_location, file.filename)
        return {"filename": file.filename, "chunks": num_chunks, "status": "indexed"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(request: ChatRequest):
    graph = get_agent_graph()
    
    # Convert history to LangChain messages
    messages = []
    for msg in request.history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    
    messages.append(HumanMessage(content=request.message))
    
    # Run the graph
    inputs = {"messages": messages}
    result = await graph.ainvoke(inputs)
    
    last_message = result["messages"][-1]
    return {"response": last_message.content}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
