"""文档处理器 - 支持多种格式的文档读取"""
import os
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger

try:
    from docx import Document
except ImportError:
    Document = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None


class DocumentProcessor:
    """文档处理器 - 统一处理多种格式的文档"""
    
    SUPPORTED_EXTENSIONS = {'.txt', '.md', '.docx', '.pdf'}
    
    def __init__(self):
        """初始化文档处理器"""
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查依赖库是否安装"""
        if Document is None:
            logger.warning("python-docx 未安装，无法处理 .docx 文件")
        if pdfplumber is None and PdfReader is None:
            logger.warning("pdfplumber 和 PyPDF2 都未安装，无法处理 .pdf 文件")
    
    def load_txt(self, file_path: Path) -> str:
        """读取文本文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"成功读取 TXT 文件: {file_path.name}")
            return content
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
            logger.info(f"成功读取 TXT 文件 (GBK): {file_path.name}")
            return content
    
    def load_markdown(self, file_path: Path) -> str:
        """读取 Markdown 文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容
        """
        return self.load_txt(file_path)
    
    def load_docx(self, file_path: Path) -> str:
        """读取 Word 文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档内容
        """
        if Document is None:
            raise ImportError("请安装 python-docx: pip install python-docx")
        
        try:
            doc = Document(file_path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            content = '\n\n'.join(paragraphs)
            logger.info(f"成功读取 DOCX 文件: {file_path.name} ({len(paragraphs)} 段落)")
            return content
        except Exception as e:
            logger.error(f"读取 DOCX 文件失败 {file_path.name}: {e}")
            raise
    
    def load_pdf(self, file_path: Path) -> str:
        """读取 PDF 文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档内容
        """
        # 优先使用 pdfplumber
        if pdfplumber is not None:
            return self._load_pdf_with_pdfplumber(file_path)
        elif PdfReader is not None:
            return self._load_pdf_with_pypdf2(file_path)
        else:
            raise ImportError("请安装 pdfplumber 或 PyPDF2: pip install pdfplumber")
    
    def _load_pdf_with_pdfplumber(self, file_path: Path) -> str:
        """使用 pdfplumber 读取 PDF
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档内容
        """
        try:
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            
            content = '\n\n'.join(text_parts)
            logger.info(f"成功读取 PDF 文件 (pdfplumber): {file_path.name} ({len(pdf.pages)} 页)")
            return content
        except Exception as e:
            logger.error(f"使用 pdfplumber 读取 PDF 失败 {file_path.name}: {e}")
            raise
    
    def _load_pdf_with_pypdf2(self, file_path: Path) -> str:
        """使用 PyPDF2 读取 PDF
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档内容
        """
        try:
            text_parts = []
            reader = PdfReader(file_path)
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            content = '\n\n'.join(text_parts)
            logger.info(f"成功读取 PDF 文件 (PyPDF2): {file_path.name} ({len(reader.pages)} 页)")
            return content
        except Exception as e:
            logger.error(f"使用 PyPDF2 读取 PDF 失败 {file_path.name}: {e}")
            raise
    
    def load_document(self, file_path: Path) -> Optional[Dict[str, str]]:
        """加载单个文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档信息字典 {"filename": str, "content": str, "extension": str}
            如果失败返回 None
        """
        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            return None
        
        extension = file_path.suffix.lower()
        
        if extension not in self.SUPPORTED_EXTENSIONS:
            logger.warning(f"不支持的文件格式: {extension}")
            return None
        
        try:
            # 根据扩展名选择处理方法
            if extension == '.txt':
                content = self.load_txt(file_path)
            elif extension == '.md':
                content = self.load_markdown(file_path)
            elif extension == '.docx':
                content = self.load_docx(file_path)
            elif extension == '.pdf':
                content = self.load_pdf(file_path)
            else:
                logger.error(f"未实现的文件格式处理: {extension}")
                return None
            
            return {
                "filename": file_path.name,
                "content": content,
                "extension": extension,
                "size": len(content),
            }
            
        except Exception as e:
            logger.error(f"加载文档失败 {file_path.name}: {e}")
            return None
    
    def load_documents_from_directory(self, directory: Path) -> List[Dict[str, str]]:
        """从目录加载所有支持的文档
        
        Args:
            directory: 目录路径
            
        Returns:
            文档信息列表
        """
        if not directory.exists():
            logger.error(f"目录不存在: {directory}")
            return []
        
        documents = []
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                doc = self.load_document(file_path)
                if doc:
                    documents.append(doc)
        
        logger.info(f"从目录 {directory.name} 加载了 {len(documents)} 个文档")
        return documents
    
    def process_uploaded_files(self, uploaded_files, save_dir: Path) -> List[Dict[str, str]]:
        """处理 Streamlit 上传的文件
        
        Args:
            uploaded_files: Streamlit UploadedFile 对象列表
            save_dir: 保存目录
            
        Returns:
            处理后的文档信息列表
        """
        save_dir.mkdir(parents=True, exist_ok=True)
        documents = []
        
        for uploaded_file in uploaded_files:
            # 保存上传的文件
            file_path = save_dir / uploaded_file.name
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            # 加载文档
            doc = self.load_document(file_path)
            if doc:
                documents.append(doc)
        
        logger.info(f"处理了 {len(documents)} 个上传的文件")
        return documents
