import os
import logging
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from pypdf import PdfReader
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from ..config import settings

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Service for loading and processing PDF and HTML documents"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
        )
        self.data_dir = Path(settings.data_directory)
        self.data_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.data_dir / "pdfs").mkdir(exist_ok=True)
        (self.data_dir / "html").mkdir(exist_ok=True)
    
    def load_pdf(self, file_path: str) -> List[Document]:
        """Load and chunk a PDF document"""
        try:
            reader = PdfReader(file_path)
            text = ""
            
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            # Create Document objects with metadata
            documents = []
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": file_path,
                        "file_type": "pdf",
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "processed_at": datetime.now().isoformat()
                    }
                )
                documents.append(doc)
            
            logger.info(f"Loaded PDF {file_path} into {len(documents)} chunks")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {str(e)}")
            raise
    
    def load_html(self, file_path: str) -> List[Document]:
        """Load and chunk an HTML document"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file.read(), 'html.parser')
                
                # Extract text content
                text = soup.get_text(separator='\n', strip=True)
                
                # Split text into chunks
                chunks = self.text_splitter.split_text(text)
                
                # Create Document objects with metadata
                documents = []
                for i, chunk in enumerate(chunks):
                    doc = Document(
                        page_content=chunk,
                        metadata={
                            "source": file_path,
                            "file_type": "html",
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "processed_at": datetime.now().isoformat()
                        }
                    )
                    documents.append(doc)
                
                logger.info(f"Loaded HTML {file_path} into {len(documents)} chunks")
                return documents
                
        except Exception as e:
            logger.error(f"Error loading HTML {file_path}: {str(e)}")
            raise
    
    def get_available_documents(self) -> List[Dict[str, Any]]:
        """Get list of available documents in the data directory"""
        documents = []
        
        # Check PDFs
        pdf_dir = self.data_dir / "pdfs"
        for pdf_file in pdf_dir.glob("*.pdf"):
            try:
                reader = PdfReader(str(pdf_file))
                documents.append({
                    "filename": pdf_file.name,
                    "file_type": "pdf",
                    "pages": len(reader.pages),
                    "size_bytes": pdf_file.stat().st_size,
                    "uploaded_at": datetime.fromtimestamp(pdf_file.stat().st_mtime).isoformat()
                })
            except Exception as e:
                logger.warning(f"Could not read PDF {pdf_file}: {str(e)}")
        
        # Check HTML files
        html_dir = self.data_dir / "html"
        for html_file in html_dir.glob("*.html"):
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    documents.append({
                        "filename": html_file.name,
                        "file_type": "html",
                        "size_bytes": html_file.stat().st_size,
                        "uploaded_at": datetime.fromtimestamp(html_file.stat().st_mtime).isoformat()
                    })
            except Exception as e:
                logger.warning(f"Could not read HTML {html_file}: {str(e)}")
        
        return documents
