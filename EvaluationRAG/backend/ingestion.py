import os
import shutil
from typing import List, Optional
from fastapi import UploadFile, File, HTTPException
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
    TextLoader,
    UnstructuredMarkdownLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import AzureOpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

# Configuration
PERSIST_DIRECTORY = "./chroma_db"
UPLOAD_DIRECTORY = "./uploaded_files"

os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

def get_embeddings():
    return AzureOpenAIEmbeddings(
        azure_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
        openai_api_version=os.getenv("AZURE_EMBEDDING_API_VERSION", "2023-05-15"),
        azure_endpoint=os.getenv("AZURE_EMBEDDING_ENDPOINT"),
        api_key=os.getenv("AZURE_EMBEDDING_API_KEY"),
    )

def get_vector_store():
    embeddings = get_embeddings()
    vector_store = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embeddings,
        collection_name="rag_collection"
    )
    return vector_store

async def save_upload_file(upload_file: UploadFile) -> str:
    file_path = os.path.join(UPLOAD_DIRECTORY, upload_file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return file_path

def load_document(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".docx":
        loader = Docx2txtLoader(file_path)
    elif ext in [".ppt", ".pptx"]:
        loader = UnstructuredPowerPointLoader(file_path)
    elif ext in [".xlsx", ".xls"]:
        loader = UnstructuredExcelLoader(file_path)
    elif ext == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
    elif ext == ".md":
        loader = UnstructuredMarkdownLoader(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
    
    return loader.load()

def process_document(file_path: str):
    docs = load_document(file_path)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    
    vector_store = get_vector_store()
    vector_store.add_documents(documents=splits)
    
    # Return count and list of content
    return len(splits), [doc.page_content for doc in splits]

def clear_vector_store():
    if os.path.exists(PERSIST_DIRECTORY):
        shutil.rmtree(PERSIST_DIRECTORY)
    if os.path.exists(UPLOAD_DIRECTORY):
        shutil.rmtree(UPLOAD_DIRECTORY)
        os.makedirs(UPLOAD_DIRECTORY)
    return True
