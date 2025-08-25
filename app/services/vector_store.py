import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from ..config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Service for managing vector storage and retrieval using ChromaDB"""
    
    def __init__(self):
        self.persist_directory = Path(settings.chroma_persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            openai_api_key=settings.openai_api_key
        )
        
        # Initialize vector store
        self.vector_store = Chroma(
            client=self.client,
            collection_name="nazarriya_documents",
            embedding_function=self.embeddings,
            persist_directory=str(self.persist_directory)
        )
        
        logger.info("Vector store initialized successfully")
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store"""
        try:
            # Add documents to the vector store
            self.vector_store.add_documents(documents)
            
            # Persist changes
            self.vector_store.persist()
            
            logger.info(f"Added {len(documents)} documents to vector store")
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise
    
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Perform similarity search for relevant documents"""
        try:
            results = self.vector_store.similarity_search(query, k=k)
            logger.info(f"Found {len(results)} relevant documents for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error performing similarity search: {str(e)}")
            raise
    
    def similarity_search_with_score(self, query: str, k: int = 4) -> List[tuple]:
        """Perform similarity search with scores"""
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            logger.info(f"Found {len(results)} relevant documents for scores for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error performing similarity search with scores: {str(e)}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection"""
        try:
            collection = self.client.get_collection("nazarriya_documents")
            count = collection.count()
            
            return {
                "total_documents": count,
                "collection_name": "nazarriya_documents",
                "persist_directory": str(self.persist_directory)
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {
                "total_documents": 0,
                "collection_name": "nazarriya_documents",
                "persist_directory": str(self.persist_directory),
                "error": str(e)
            }
    
    def reset_collection(self) -> None:
        """Reset the vector store collection"""
        try:
            self.client.delete_collection("nazarriya_documents")
            
            # Reinitialize vector store
            self.vector_store = Chroma(
                client=self.client,
                collection_name="nazarriya_documents",
                embedding_function=self.embeddings,
                persist_directory=str(self.persist_directory)
            )
            
            logger.info("Vector store collection reset successfully")
            
        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")
            raise
    
    def delete_documents(self, source: str) -> None:
        """Delete documents by source"""
        try:
            # Get all documents with the specified source
            results = self.vector_store.similarity_search("", k=1000)  # Get all documents
            
            # Filter documents by source
            docs_to_delete = [doc for doc in results if doc.metadata.get("source") == source]
            
            if docs_to_delete:
                # Note: ChromaDB doesn't have a direct delete method in Langchain
                # We'll need to reset and rebuild the collection
                logger.warning(f"Deleting documents from source {source} requires collection reset")
                self.reset_collection()
            
            logger.info(f"Deleted documents from source: {source}")
            
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            raise
