import os
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import fitz # PyMuPDF

from app.models.document import ConstructionDocument, DrawingChunk, EmbeddingMetadata
from app.services.embedding_service import EmbeddingService
from app.agents.rag_agent import rag_prediction_agent

logger = logging.getLogger(__name__)

class RAGService:
    @staticmethod
    def create_document(
        db: Session,
        project_id: int,
        file_name: str,
        file_type: str,
        file_path: str
    ) -> ConstructionDocument:
        """Saves document reference entry into the DB."""
        doc = ConstructionDocument(
            project_id=project_id,
            file_name=file_name,
            file_type=file_type,
            file_path=file_path,
            status="Pending"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def process_document(db: Session, document_id: int) -> ConstructionDocument:
        """Extracts text pages, chunks content, saves chunks to DB, and indexes vector embeddings."""
        doc = db.query(ConstructionDocument).filter(ConstructionDocument.id == document_id).first()
        if not doc:
            raise ValueError("Document record not found.")

        try:
            doc.status = "Processing"
            db.commit()

            # Verify file exists on disk
            if not os.path.exists(doc.file_path):
                raise FileNotFoundError(f"Physical file missing at: {doc.file_path}")

            # PyMuPDF text extraction
            extracted_pages = []
            with fitz.open(doc.file_path) as pdf:
                for page_num, page in enumerate(pdf, start=1):
                    text = page.get_text()
                    if text.strip():
                        extracted_pages.append((page_num, text))

            full_text = "\n\n".join([text for _, text in extracted_pages])
            doc.extracted_text = full_text

            # Text Chunking logic
            chunks_list = []
            chunk_size = 600
            overlap = 150
            chunk_index = 0

            for page_num, text in extracted_pages:
                start = 0
                while start < len(text):
                    end = start + chunk_size
                    chunk_text = text[start:end].strip()
                    
                    if chunk_text:
                        db_chunk = DrawingChunk(
                            document_id=doc.id,
                            chunk_index=chunk_index,
                            page_number=page_num,
                            chunk_text=chunk_text
                        )
                        db.add(db_chunk)
                        chunks_list.append(db_chunk)
                        chunk_index += 1
                        
                    start += (chunk_size - overlap)

            db.commit() # Save chunks to get IDs

            # Populate vector DB (ChromaDB)
            texts_to_embed = []
            metadatas_to_embed = []
            ids_to_embed = []

            for chunk in chunks_list:
                vector_id = f"chunk_{chunk.id}"
                
                # Register vector mapping
                metadata = EmbeddingMetadata(
                    chunk_id=chunk.id,
                    vector_id=vector_id,
                    metadata_json=f'{{"project_id": {doc.project_id}, "document_id": {doc.id}, "page": {chunk.page_number}}}'
                )
                db.add(metadata)
                
                texts_to_embed.append(chunk.chunk_text)
                metadatas_to_embed.append({
                    "project_id": int(doc.project_id),
                    "document_id": int(doc.id),
                    "page_number": int(chunk.page_number),
                    "file_name": doc.file_name
                })
                ids_to_embed.append(vector_id)

            db.commit()

            # Index chunks in vector store
            EmbeddingService.add_chunks(
                collection_name="construction_drawings",
                texts=texts_to_embed,
                metadatas=metadatas_to_embed,
                ids=ids_to_embed
            )

            doc.status = "Completed"
            doc.total_chunks = len(chunks_list)
            db.commit()
            db.refresh(doc)
            return doc

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            doc.status = "Error"
            db.commit()
            raise e

    @staticmethod
    def query_documents(
        db: Session,
        project_id: int,
        query_text: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Queries ChromaDB for closest chunks, then feeds context to drawing Q&A agent."""
        # Query matching vectors
        vector_results = EmbeddingService.query_similarity(
            collection_name="construction_drawings",
            query_text=query_text,
            limit=limit,
            where_filter={"project_id": project_id}
        )

        # Build context from matches
        context_chunks = []
        sources = []
        for res in vector_results:
            context_chunks.append(res["text"])
            sources.append({
                "chunk_text": res["text"],
                "page_number": int(res["metadata"].get("page_number", 1)),
                "document_name": res["metadata"].get("file_name", "Drawing File"),
                "similarity_score": float(res["score"])
            })

        context_payload = "\n---\n".join(context_chunks)

        # Call LangGraph drawing analyzer agent
        agent_input = {
            "query": query_text,
            "context": context_payload,
            "answer": "",
            "recommendations": []
        }
        
        agent_output = rag_prediction_agent.invoke(agent_input)

        return {
            "answer": agent_output.get("answer", "No response could be formulated."),
            "recommendations": agent_output.get("recommendations", []),
            "sources": sources
        }

    @staticmethod
    def get_document_details(db: Session, doc_id: int) -> Optional[ConstructionDocument]:
        """Returns document details along with segmented chunks."""
        return db.query(ConstructionDocument).filter(ConstructionDocument.id == doc_id).first()

    @staticmethod
    def list_project_documents(db: Session, project_id: int) -> List[ConstructionDocument]:
        """Lists drawings registered for a project."""
        return db.query(ConstructionDocument).filter(ConstructionDocument.project_id == project_id).all()
