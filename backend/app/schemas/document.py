from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

class DrawingChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    page_number: int
    chunk_text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConstructionDocumentResponse(BaseModel):
    id: int
    project_id: int
    file_name: str
    file_type: str
    file_path: str
    status: str
    total_chunks: int
    extracted_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConstructionDocumentDetailResponse(ConstructionDocumentResponse):
    chunks: List[DrawingChunkResponse] = []

class DocumentQueryRequest(BaseModel):
    project_id: int
    query_text: str
    limit: Optional[int] = Field(5, description="Maximum number of context chunks to retrieve.")

class DocumentQueryResultItem(BaseModel):
    chunk_text: str
    page_number: int
    document_name: str
    similarity_score: float

class DocumentQueryResponse(BaseModel):
    answer: str
    recommendations: List[str] = []
    sources: List[DocumentQueryResultItem] = []
