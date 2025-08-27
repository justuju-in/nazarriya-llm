import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import shutil

from .document_loader import DocumentLoader
from .vector_store import VectorStore
from .llm_service import LLMService
from ..config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """Main service for orchestrating the RAG pipeline"""
    
    def __init__(self):
        self.document_loader = DocumentLoader()
        self.vector_store = VectorStore()
        self.llm_service = LLMService()
        
        logger.info("RAG service initialized successfully")
    
    def ingest_documents(self, file_paths: List[str]) -> Dict[str, Any]:
        """Ingest multiple documents into the RAG system"""
        try:
            total_chunks = 0
            processed_files = 0
            
            for file_path in file_paths:
                file_path = Path(file_path)
                
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue
                
                # Check if file is already in the data directory
                if str(file_path).startswith(str(self.document_loader.data_dir)):
                    # File is already in data directory, use it directly
                    dest_path = file_path
                    logger.info(f"File already in data directory: {file_path.name}")
                else:
                    # Copy file to appropriate data directory
                    if file_path.suffix.lower() == '.pdf':
                        dest_dir = self.document_loader.data_dir / "pdfs"
                    elif file_path.suffix.lower() in ['.html', '.htm']:
                        dest_dir = self.document_loader.data_dir / "html"
                    else:
                        logger.warning(f"Unsupported file type: {file_path.suffix}")
                        continue
                    
                    dest_path = dest_dir / file_path.name
                    shutil.copy2(file_path, dest_path)
                    logger.info(f"Copied {file_path.name} to data directory")
                
                # Load and process document
                if file_path.suffix.lower() == '.pdf':
                    documents = self.document_loader.load_pdf(str(dest_path))
                else:
                    documents = self.document_loader.load_html(str(dest_path))
                
                # Add to vector store
                self.vector_store.add_documents(documents)
                
                total_chunks += len(documents)
                processed_files += 1
                
                logger.info(f"Processed {file_path.name}: {len(documents)} chunks")
            
            return {
                "message": f"Successfully processed {processed_files} files",
                "files_processed": processed_files,
                "total_chunks": total_chunks
            }
            
        except Exception as e:
            logger.error(f"Error ingesting documents: {str(e)}")
            raise
    
    def query(
        self, 
        query: str, 
        history: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None,
        k: int = 4
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Query the RAG system"""
        try:
            # Search for relevant documents
            relevant_docs = self.vector_store.similarity_search(query, k=k)
            
            if not relevant_docs:
                return "I don't have enough context to answer this question. Please ensure documents have been ingested.", []
            
            # Extract context from relevant documents
            context = [doc.page_content for doc in relevant_docs]
            
            # Generate response using LLM
            response = self.llm_service.generate_response(
                query=query,
                context=context,
                history=history,
                max_tokens=max_tokens
            )
            
            # Prepare sources information
            sources = []
            for doc in relevant_docs:
                sources.append({
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "metadata": doc.metadata,
                    "relevance_score": 0.8  # Placeholder score
                })
            
            logger.info(f"Generated response for query: {query[:50]}...")
            return response, sources
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        try:
            # Get vector store stats
            vector_stats = self.vector_store.get_collection_stats()
            
            # Get available documents
            available_docs = self.document_loader.get_available_documents()
            
            # Get model info
            model_info = self.llm_service.get_model_info()
            
            return {
                "vector_store": vector_stats,
                "available_documents": available_docs,
                "model_info": model_info,
                "total_documents": len(available_docs),
                "status": "healthy"
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def reset_system(self) -> Dict[str, str]:
        """Reset the entire RAG system"""
        try:
            # Reset vector store
            self.vector_store.reset_collection()
            
            # Clear data directory
            for subdir in ["pdfs", "html"]:
                subdir_path = self.document_loader.data_dir / subdir
                if subdir_path.exists():
                    for file_path in subdir_path.iterdir():
                        if file_path.is_file():
                            file_path.unlink()
            
            logger.info("RAG system reset successfully")
            return {"message": "System reset successfully"}
            
        except Exception as e:
            logger.error(f"Error resetting system: {str(e)}")
            raise
    
    def add_document_from_path(self, file_path: str) -> Dict[str, Any]:
        """Add a single document from a file path"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Check if file is already in the data directory
            if str(file_path).startswith(str(self.document_loader.data_dir)):
                # File is already in data directory, use it directly
                dest_path = file_path
                logger.info(f"File already in data directory: {file_path.name}")
            else:
                # Copy to appropriate data directory
                if file_path.suffix.lower() == '.pdf':
                    dest_dir = self.document_loader.data_dir / "pdfs"
                elif file_path.suffix.lower() in ['.html', '.htm']:
                    dest_dir = self.document_loader.data_dir / "html"
                else:
                    raise ValueError(f"Unsupported file type: {file_path.suffix}")
                
                dest_path = dest_dir / file_path.name
                shutil.copy2(file_path, dest_path)
                logger.info(f"Copied {file_path.name} to data directory")
            
            # Load and process document
            if file_path.suffix.lower() == '.pdf':
                documents = self.document_loader.load_pdf(str(dest_path))
            else:
                documents = self.document_loader.load_html(str(dest_path))
            
            # Add to vector store
            self.vector_store.add_documents(documents)
            
            return {
                "message": f"Successfully added {file_path.name}",
                "filename": file_path.name,
                "chunks_created": len(documents),
                "file_type": file_path.suffix.lower()
            }
            
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            raise
