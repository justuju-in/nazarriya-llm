import logging
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import json

from ..services.rag_service import RAGService
from ..models import (
    QueryRequest, 
    QueryResponse, 
    DocumentUploadResponse, 
    HealthResponse,
    DocumentInfo
)
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG"])
rag_service = RAGService()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )


@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Query the RAG system"""
    try:
        # Convert history format if needed
        history = []
        if request.history:
            for msg in request.history:
                if "message" in msg and "role" in msg:
                    history.append({
                        "role": msg["role"],
                        "content": msg["message"]
                    })
                elif "message" in msg:
                    history.append({
                        "role": "user",
                        "content": msg["message"]
                    })
        
        # Get response from RAG service
        answer, sources = rag_service.query(
            query=request.query,
            history=history,
            max_tokens=request.max_tokens
        )
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            metadata={
                "query_length": len(request.query),
                "sources_count": len(sources),
                "model": settings.openai_model
            }
        )
        
    except Exception as e:
        logger.error(f"Error in RAG query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    file_path: str = Form(None)
):
    """Upload a document to the RAG system"""
    try:
        if file_path:
            # Use provided file path
            result = rag_service.add_document_from_path(file_path)
        else:
            # Save uploaded file and process
            if not file.filename:
                raise HTTPException(status_code=400, detail="No filename provided")
            
            # Determine file type and save to appropriate directory
            if file.filename.lower().endswith('.pdf'):
                save_dir = rag_service.document_loader.data_dir / "pdfs"
            elif file.filename.lower().endswith(('.html', '.htm')):
                save_dir = rag_service.document_loader.data_dir / "html"
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type")
            
            save_path = save_dir / file.filename
            
            # Save file
            with open(save_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Process the saved file
            result = rag_service.add_document_from_path(str(save_path))
        
        return DocumentUploadResponse(
            message=result["message"],
            documents_processed=1,
            chunks_created=result["chunks_created"]
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest", response_model=DocumentUploadResponse)
async def ingest_documents(file_paths: List[str]):
    """Ingest multiple documents from file paths"""
    try:
        result = rag_service.ingest_documents(file_paths)
        
        return DocumentUploadResponse(
            message=result["message"],
            documents_processed=result["files_processed"],
            chunks_created=result["total_chunks"]
        )
        
    except Exception as e:
        logger.error(f"Error ingesting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """List all available documents"""
    try:
        documents = rag_service.document_loader.get_available_documents()
        
        # Convert to DocumentInfo format
        doc_infos = []
        for doc in documents:
            doc_info = DocumentInfo(
                filename=doc["filename"],
                file_type=doc["file_type"],
                chunks=doc.get("pages", 0),  # For PDFs
                size_bytes=doc["size_bytes"],
                uploaded_at=doc["uploaded_at"]
            )
            doc_infos.append(doc_info)
        
        return doc_infos
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_system_status():
    """Get overall system status"""
    try:
        status = rag_service.get_system_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_system():
    """Reset the entire RAG system"""
    try:
        result = rag_service.reset_system()
        return {"message": result["message"]}
        
    except Exception as e:
        logger.error(f"Error resetting system: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Delete a specific document"""
    try:
        # Find the document path
        for subdir in ["pdfs", "html"]:
            file_path = rag_service.document_loader.data_dir / subdir / filename
            if file_path.exists():
                # Remove from vector store (this will reset the collection)
                rag_service.vector_store.delete_documents(str(file_path))
                
                # Remove file
                file_path.unlink()
                
                return {"message": f"Document {filename} deleted successfully"}
        
        raise HTTPException(status_code=404, detail=f"Document {filename} not found")
        
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
