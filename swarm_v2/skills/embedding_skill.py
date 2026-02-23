"""
Embedding Skill - Vector Embedding Capabilities for Swarm Agents
Provides embedding generation using Ollama embedding models
"""

import os
import json
import httpx
from typing import List, Dict, Any, Optional

class EmbeddingSkill:
    """Skill for generating text embeddings using Ollama"""
    
    def __init__(
        self,
        model: str = "nomic-embed-text",  # Default embedding model
        embedding_dim: int = 768
    ):
        self.skill_name = "embedding"
        self.description = "Generate vector embeddings for text using Ollama embedding models"
        self.model = model
        self.embedding_dim = embedding_dim
        self.ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Model-specific dimensions
        self.model_dims = {
            "nomic-embed-text": 768,
            "mxbai-embed-large": 1024,
            "embeddinggemma": 768,
            "qwen3-embedding:4b": 1024,
            "qwen3-embedding:0.6b": 1024,
        }
        
    def _get_embedding_dimension(self) -> int:
        """Get the correct dimension for the selected model"""
        return self.model_dims.get(self.model, self.embedding_dim)
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.ollama_base}/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": text
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get("embedding", [])
                else:
                    print(f"Embedding error: {response.status_code}")
                    return []
        except Exception as e:
            print(f"Embedding failed: {e}")
            return []
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            emb = self.embed_text(text)
            embeddings.append(emb)
        return embeddings
    
    def embed_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Embed documents with metadata
        
        Args:
            documents: List of dicts with 'content' and optional 'metadata'
            
        Returns:
            List of dicts with 'embedding', 'content', 'metadata'
        """
        results = []
        for doc in documents:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            
            embedding = self.embed_text(content)
            
            results.append({
                "embedding": embedding,
                "content": content,
                "metadata": metadata,
                "model": self.model,
                "dimension": self._get_embedding_dimension()
            })
            
        return results
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2:
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
            
        return dot_product / (mag1 * mag2)
    
    def find_similar(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find most similar documents to a query
        
        Args:
            query: Query text
            documents: List of documents with 'content' field
            top_k: Number of results to return
            
        Returns:
            Top k similar documents with similarity scores
        """
        query_embedding = self.embed_text(query)
        
        similarities = []
        for doc in documents:
            doc_embedding = self.embed_text(doc.get("content", ""))
            score = self.cosine_similarity(query_embedding, doc_embedding)
            similarities.append({
                "content": doc.get("content", ""),
                "metadata": doc.get("metadata", {}),
                "similarity": score
            })
        
        # Sort by similarity
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        return similarities[:top_k]
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get information about the embedding model"""
        return {
            "model": self.model,
            "dimension": self._get_embedding_dimension(),
            "available_models": list(self.model_dims.keys())
        }


class HighQualityEmbeddingSkill(EmbeddingSkill):
    """High quality embeddings using mxbai-embed-large"""
    
    def __init__(self):
        super().__init__(
            model="mxbai-embed-large",
            embedding_dim=1024
        )
        self.skill_name = "high_quality_embedding"
        self.description = "Generate high-quality vector embeddings using mxbai-embed-large"


class FastEmbeddingSkill(EmbeddingSkill):
    """Fast lightweight embeddings using nomic-embed-text"""
    
    def __init__(self):
        super().__init__(
            model="nomic-embed-text",
            embedding_dim=768
        )
        self.skill_name = "fast_embedding"
        self.description = "Generate fast vector embeddings using nomic-embed-text"

class SpectralEmbeddingSkill(EmbeddingSkill):
    """Deep semantic indexing using EmbeddingGemma-300M."""
    
    def __init__(self):
        super().__init__(
            model="embeddinggemma",
            embedding_dim=768
        )
        self.skill_name = "spectral_embedding"
        self.description = "Advanced spectral embedding for deep semantic indexing using Gemma-300M technology."
