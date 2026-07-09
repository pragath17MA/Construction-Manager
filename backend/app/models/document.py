from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base

class ConstructionDocument(Base):
    __tablename__ = "construction_documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(String, default="Pending") # Pending, Processing, Completed, Error
    total_chunks = Column(Integer, default=0)
    extracted_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="construction_documents")
    chunks = relationship("DrawingChunk", back_populates="document", cascade="all, delete-orphan")

class DrawingChunk(Base):
    __tablename__ = "drawing_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("construction_documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("ConstructionDocument", back_populates="chunks")
    embeddings = relationship("EmbeddingMetadata", back_populates="chunk", cascade="all, delete-orphan")

class EmbeddingMetadata(Base):
    __tablename__ = "embeddings_metadata"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(Integer, ForeignKey("drawing_chunks.id", ondelete="CASCADE"), nullable=False)
    vector_id = Column(String, nullable=False) # ChromaDB UUID reference
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chunk = relationship("DrawingChunk", back_populates="embeddings")
