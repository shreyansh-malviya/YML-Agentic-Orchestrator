"""
RAG-based Memory System for Agent Context Management
Uses sentence-transformers and FAISS for efficient retrieval
"""

import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict

# Try to import dependencies
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠ sentence-transformers not installed. Run: pip install sentence-transformers")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠ faiss-cpu not installed. Run: pip install faiss-cpu")


# Configuration
MEMORY_DIR = Path(__file__).parent / "context"
EMBED_FILE = MEMORY_DIR / "embeddings.npy"
MEMORY_FILE = MEMORY_DIR / "memory.jsonl"
MODEL_NAME = "all-MiniLM-L6-v2"
DIM = 384  # Dimension for all-MiniLM-L6-v2

# Initialize model
if SENTENCE_TRANSFORMERS_AVAILABLE:
    MODEL = SentenceTransformer(MODEL_NAME)
else:
    MODEL = None


def ensure_memory_dir():
    """Ensure memory directory exists"""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def clear_memory():
    """Clear all stored memories and embeddings"""
    ensure_memory_dir()
    
    # Remove files if they exist
    if EMBED_FILE.exists():
        EMBED_FILE.unlink()
    if MEMORY_FILE.exists():
        MEMORY_FILE.unlink()
    
    print("🗑️  Memory cleared")


def load_index():
    """Load FAISS index from embeddings file"""
    if not FAISS_AVAILABLE:
        return None
    
    if EMBED_FILE.exists():
        vectors = np.load(EMBED_FILE)
        index = faiss.IndexFlatL2(DIM)
        index.add(vectors.astype('float32'))
        return index
    else:
        return faiss.IndexFlatL2(DIM)


def store_context(role: str, text: str):
    """
    Store context with semantic embedding for efficient retrieval
    
    Args:
        role: Agent role/name
        text: Response text to store
    """
    if not SENTENCE_TRANSFORMERS_AVAILABLE or not FAISS_AVAILABLE:
        print("⚠ RAG dependencies not available. Skipping memory storage.")
        return
    
    ensure_memory_dir()
    
    # Generate embedding
    embedding = MODEL.encode([text], convert_to_numpy=True)
    
    # Save embedding
    if EMBED_FILE.exists():
        vectors = np.load(EMBED_FILE)
        vectors = np.vstack([vectors, embedding])
    else:
        vectors = embedding
    
    np.save(EMBED_FILE, vectors.astype('float32'))
    
    # Save raw text with metadata
    memory_entry = {
        "role": role,
        "text": text
    }
    
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(memory_entry, ensure_ascii=False) + "\n")
    
    print(f"💾 Stored memory: {role} ({len(text)} chars)")


def retrieve_context(query: str, k: int = 5) -> str:
    """
    Retrieve relevant context based on semantic similarity
    
    Args:
        query: Query text (usually the current agent's prompt)
        k: Number of most relevant memories to retrieve
    
    Returns:
        Formatted context string with relevant previous conversations
    """
    if not SENTENCE_TRANSFORMERS_AVAILABLE or not FAISS_AVAILABLE:
        print("⚠ RAG dependencies not available. Returning empty context.")
        return ""
    
    if not EMBED_FILE.exists() or not MEMORY_FILE.exists():
        return ""
    
    # Load vectors and create index
    vectors = np.load(EMBED_FILE)
    index = load_index()
    
    if index is None or index.ntotal == 0:
        return ""
    
    # Generate query embedding
    query_embedding = MODEL.encode([query], convert_to_numpy=True).astype('float32')
    
    # Search for k most similar
    k = min(k, index.ntotal)  # Don't search for more than available
    distances, indices = index.search(query_embedding, k)
    
    # Retrieve relevant memories
    memories = []
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    for idx in indices[0]:
        if idx < len(lines):
            memory = json.loads(lines[idx])
            memories.append(memory)
    
    # Format as context string
    if not memories:
        return ""
    
    context_parts = []
    for memory in memories:
        role = memory.get("role", "Agent")
        text = memory.get("text", "")
        context_parts.append(f"{role}: {text}")
    
    context = "\n\n".join(context_parts)
    print(f"🔍 Retrieved {len(memories)} relevant memories")
    
    return context


def get_memory_stats() -> Dict:
    """Get statistics about stored memories"""
    stats = {
        "total_memories": 0,
        "embedding_dimension": DIM,
        "storage_path": str(MEMORY_DIR)
    }
    
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            stats["total_memories"] = sum(1 for _ in f)
    
    return stats


# Fallback functions when dependencies not available
def _fallback_store(role: str, text: str):
    """Fallback storage without RAG (simple append)"""
    ensure_memory_dir()
    fallback_file = MEMORY_DIR / "fallback_memory.jsonl"
    
    with open(fallback_file, "a", encoding="utf-8") as f:
        json.dump({"role": role, "text": text}, f, ensure_ascii=False)
        f.write("\n")


def _fallback_retrieve(query: str, k: int = 5) -> str:
    """Fallback retrieval without RAG (return last k items)"""
    fallback_file = MEMORY_DIR / "fallback_memory.jsonl"
    
    if not fallback_file.exists():
        return ""
    
    with open(fallback_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Return last k items
    recent = lines[-k:] if len(lines) > k else lines
    
    context_parts = []
    for line in recent:
        memory = json.loads(line)
        context_parts.append(f"{memory['role']}: {memory['text']}")
    
    return "\n\n".join(context_parts)
