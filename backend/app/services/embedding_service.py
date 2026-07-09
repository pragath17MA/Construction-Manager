import os
import hashlib
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.api.types import Documents, Embeddings

CHROMA_PATH = "uploads/chroma_db"

class DeterministicMockEmbeddingFunction(chromadb.EmbeddingFunction):
    """
    Custom 100% offline, CPU-friendly embedding function.
    Computes a deterministic 384-dimensional vector from document text hashing.
    Enables instant vector comparisons and semantic routing during tests.
    """
    def __init__(self, **kwargs):
        pass

    @classmethod
    def name(cls) -> str:
        return "DeterministicMockEmbeddingFunction"

    def get_config(self) -> Dict[str, Any]:
        return {}

    @classmethod
    def build_from_config(cls, config: Dict[str, Any]) -> "DeterministicMockEmbeddingFunction":
        return cls()

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for doc in input:
            vector = []
            for i in range(384):
                # SHA256 hashed seeds to yield float features in range [-1.0, 1.0]
                seed = f"{doc}_feature_{i}".encode("utf-8")
                h = hashlib.sha256(seed).hexdigest()
                val = int(h[:8], 16) / 4294967295.0
                vector.append(val * 2.0 - 1.0)
            embeddings.append(vector)
        return embeddings

class EmbeddingService:
    _chroma_client = None
    _embedding_function = DeterministicMockEmbeddingFunction()

    @classmethod
    def get_chroma_client(cls) -> Any:
        """Retrieves ChromaDB client (remote or persistent)."""
        if cls._chroma_client is None:
            chroma_host = os.getenv("CHROMA_HOST", "")
            chroma_port = os.getenv("CHROMA_PORT", "8000")
            if chroma_host:
                cls._chroma_client = chromadb.HttpClient(host=chroma_host, port=int(chroma_port))
            else:
                os.makedirs(CHROMA_PATH, exist_ok=True)
                cls._chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        return cls._chroma_client

    @classmethod
    def get_collection(cls, collection_name: str) -> chromadb.Collection:
        """Pulls or creates a ChromaDB vector collection."""
        client = cls.get_chroma_client()
        return client.get_or_create_collection(
            name=collection_name,
            embedding_function=cls._embedding_function
        )

    @classmethod
    def add_chunks(
        cls,
        collection_name: str,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """Indexes text segments into the vector database."""
        if not texts:
            return
        collection = cls.get_collection(collection_name)
        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

    @classmethod
    def query_similarity(
        cls,
        collection_name: str,
        query_text: str,
        limit: int = 5,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Queries vector collection for closest matching text chunks."""
        collection = cls.get_collection(collection_name)
        results = collection.query(
            query_texts=[query_text],
            n_results=limit,
            where=where_filter
        )
        
        formatted = []
        if not results or not results.get("documents"):
            return formatted

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]
        ids = results["ids"][0]

        for i in range(len(documents)):
            # Convert distances (e.g. L2) to a pseudo-similarity score between 0.0 and 1.0
            dist = distances[i]
            similarity_score = max(0.0, 1.0 - (dist / 2.0))
            formatted.append({
                "id": ids[i],
                "text": documents[i],
                "metadata": metadatas[i],
                "score": float(similarity_score)
            })

        return formatted

    @classmethod
    def delete_chunks(cls, collection_name: str, ids: List[str]) -> None:
        """Clears specific records from vector indexes."""
        if not ids:
            return
        collection = cls.get_collection(collection_name)
        collection.delete(ids=ids)

    @classmethod
    def clear_collection(cls, collection_name: str) -> None:
        """Wipes a collection completely."""
        client = cls.get_chroma_client()
        try:
            client.delete_collection(name=collection_name)
        except Exception:
            pass
