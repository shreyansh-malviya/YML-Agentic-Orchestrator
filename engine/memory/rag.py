"""
RAG (Retrieval Augmented Generation) Memory System
Uses sentence-transformers for embeddings and FAISS for vector storage
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠ sentence-transformers not installed. Install with: pip install sentence-transformers")

try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠ faiss-cpu not installed. Install with: pip install faiss-cpu")


class MemoryRAG:
    """RAG-based memory system for storing and retrieving context"""
    
    def __init__(self, memory_dir: Optional[str] = None, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize RAG memory system
        
        Args:
            memory_dir: Directory to store memory files (default: engine/memory/storage)
            model_name: Sentence transformer model name (default: all-MiniLM-L6-v2)
        """
        if memory_dir is None:
            memory_dir = Path(__file__).parent / "storage"
        else:
            memory_dir = Path(memory_dir)
        
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.index_path = self.memory_dir / "faiss_index.bin"
        self.metadata_path = self.memory_dir / "metadata.json"
        self.model_cache_path = self.memory_dir / "model_cache"
        
        # Initialize model
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self.model = SentenceTransformer(model_name, cache_folder=str(self.model_cache_path))
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
        else:
            self.model = None
            self.embedding_dim = 384  # Default for all-MiniLM-L6-v2
        
        # Initialize FAISS index and metadata
        self.index = None
        self.metadata = []
        
        # Load existing data if available
        self._load()
    
    def _load(self):
        """Load existing index and metadata from disk"""
        if not FAISS_AVAILABLE:
            return
        
        # Load FAISS index
        if self.index_path.exists():
            try:
                self.index = faiss.read_index(str(self.index_path))
                print(f"✓ Loaded FAISS index with {self.index.ntotal} vectors")
            except Exception as e:
                print(f"⚠ Failed to load FAISS index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
        
        # Load metadata
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                print(f"✓ Loaded {len(self.metadata)} memory entries")
            except Exception as e:
                print(f"⚠ Failed to load metadata: {e}")
                self.metadata = []
    
    def _create_new_index(self):
        """Create a new FAISS index"""
        if not FAISS_AVAILABLE:
            return
        
        # Using IndexFlatL2 for exact search (can switch to IndexIVFFlat for larger datasets)
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        print(f"✓ Created new FAISS index (dimension: {self.embedding_dim})")
    
    def _save(self):
        """Save index and metadata to disk"""
        if not FAISS_AVAILABLE:
            return
        
        # Save FAISS index
        try:
            faiss.write_index(self.index, str(self.index_path))
        except Exception as e:
            print(f"⚠ Failed to save FAISS index: {e}")
        
        # Save metadata
        try:
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠ Failed to save metadata: {e}")
    
    def store(self, text: str, role: str = "Agent", metadata: Optional[Dict[str, Any]] = None):
        """
        Store text in memory with vector embedding
        
        Args:
            text: Text to store
            role: Role/agent name for this memory
            metadata: Additional metadata to store
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE or not FAISS_AVAILABLE:
            print("⚠ RAG dependencies not available. Skipping memory storage.")
            return
        
        if not text or not text.strip():
            return
        
        # Generate embedding
        embedding = self.model.encode([text])[0]
        
        # Prepare metadata
        entry_metadata = {
            "text": text,
            "role": role,
            "timestamp": datetime.now().isoformat(),
            "index_id": len(self.metadata)
        }
        
        if metadata:
            entry_metadata.update(metadata)
        
        # Add to FAISS index
        self.index.add(np.array([embedding], dtype=np.float32))
        
        # Add metadata
        self.metadata.append(entry_metadata)
        
        # Save to disk
        self._save()
        
        print(f"💾 Stored memory: {role} ({len(text)} chars)")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories based on query
        
        Args:
            query: Query text to search for
            top_k: Number of top results to return
        
        Returns:
            List of relevant memory entries with scores
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE or not FAISS_AVAILABLE:
            print("⚠ RAG dependencies not available. Returning empty results.")
            return []
        
        if not query or not query.strip():
            return []
        
        if self.index.ntotal == 0:
            print("⚠ No memories stored yet")
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query])[0]
        
        # Search FAISS index
        top_k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(
            np.array([query_embedding], dtype=np.float32),
            top_k
        )
        
        # Prepare results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result['similarity_score'] = float(1 / (1 + distances[0][i]))  # Convert distance to similarity
                result['distance'] = float(distances[0][i])
                results.append(result)
        
        print(f"🔍 Retrieved {len(results)} relevant memories")
        return results
    
    def get_context_string(self, query: str, top_k: int = 5) -> str:
        """
        Get formatted context string from relevant memories
        
        Args:
            query: Query text to search for
            top_k: Number of top results to return
        
        Returns:
            Formatted context string
        """
        results = self.retrieve(query, top_k)
        
        if not results:
            return ""
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Memory {i} - {result['role']}]")
            context_parts.append(result['text'])
            context_parts.append("")  # Empty line
        
        return "\n".join(context_parts)
    
    def clear(self):
        """Clear all memories"""
        self.metadata = []
        self._create_new_index()
        self._save()
        print("🗑 Memory cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "total_memories": len(self.metadata),
            "index_size": self.index.ntotal if self.index else 0,
            "embedding_dim": self.embedding_dim,
            "storage_path": str(self.memory_dir)
        }


# Global instance
_memory_instance = None


def get_memory_instance() -> MemoryRAG:
    """Get or create global memory instance"""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = MemoryRAG()
    return _memory_instance


def store_memory(text: str, role: str = "Agent", metadata: Optional[Dict[str, Any]] = None):
    """
    Store text in memory
    
    Args:
        text: Text to store
        role: Role/agent name
        metadata: Additional metadata
    """
    memory = get_memory_instance()
    memory.store(text, role, metadata)


def retrieve_memory(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve relevant memories
    
    Args:
        query: Query text
        top_k: Number of results to return
    
    Returns:
        List of relevant memories
    """
    memory = get_memory_instance()
    return memory.retrieve(query, top_k)


def get_context(query: str, top_k: int = 5) -> str:
    """
    Get formatted context string
    
    Args:
        query: Query text
        top_k: Number of results to include
    
    Returns:
        Formatted context string
    """
    memory = get_memory_instance()
    return memory.get_context_string(query, top_k)


def clear_memory():
    """Clear all memories"""
    memory = get_memory_instance()
    memory.clear()


def get_memory_stats() -> Dict[str, Any]:
    """Get memory statistics"""
    memory = get_memory_instance()
    return memory.get_stats()
