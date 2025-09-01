from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class QueryRequest(BaseModel):
    encrypted_query: str  # Base64-encoded bytes
    encryption_metadata: dict
    content_hash: str
    encrypted_history: Optional[List[Dict[str, Any]]] = []
    max_tokens: Optional[int] = 1000

class PlaintextQueryRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = []
    max_tokens: Optional[int] = 1000


class QueryResponse(BaseModel):
    encrypted_answer: str  # Base64-encoded bytes
    encryption_metadata: dict
    content_hash: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class PlaintextQueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class DocumentUploadResponse(BaseModel):
    message: str
    documents_processed: int
    chunks_created: int


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str = "1.0.0"


class DocumentInfo(BaseModel):
    filename: str
    file_type: str
    chunks: int
    size_bytes: int
    uploaded_at: str
