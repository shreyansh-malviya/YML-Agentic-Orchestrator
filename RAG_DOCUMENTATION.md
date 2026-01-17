# RAG Memory System Documentation

## Overview

The RAG (Retrieval Augmented Generation) memory system provides intelligent context management for agent workflows. Instead of sending the entire conversation history to each agent (which can grow to 3-4k lines), the system:

1. **Stores** each agent response as a vector embedding
2. **Retrieves** only the most relevant previous responses based on semantic similarity
3. **Provides** compact, relevant context to each agent

## Installation

```bash
pip install -r requirements.txt
```

Required packages:
- `sentence-transformers>=2.2.0` - For text embeddings
- `faiss-cpu>=1.7.4` - For vector similarity search
- `numpy>=1.24.0` - For numerical operations

## How It Works

### 1. Vector Embeddings
Each agent response is converted to a 384-dimensional vector using the `all-MiniLM-L6-v2` model:
```python
"Python is a programming language" → [0.123, -0.456, 0.789, ...]
```

### 2. FAISS Index
Vectors are stored in a FAISS index for fast similarity search:
- **IndexFlatL2**: Exact search, perfect for small-medium datasets
- Can be upgraded to **IndexIVFFlat** for larger datasets

### 3. Semantic Retrieval
When an agent needs context, the system:
1. Converts the agent's prompt to a vector
2. Finds the top K most similar stored memories
3. Returns only relevant context (not everything)

## API Reference

### Core Functions

#### `store_memory(text, role, metadata=None)`
Store text in the memory system.

```python
from engine.memory.rag import store_memory

store_memory(
    "Python is great for AI development",
    role="AI Expert",
    metadata={"topic": "programming"}
)
```

**Parameters:**
- `text` (str): Text to store
- `role` (str): Agent/role name
- `metadata` (dict, optional): Additional metadata

---

#### `retrieve_memory(query, top_k=5)`
Retrieve relevant memories based on query.

```python
from engine.memory.rag import retrieve_memory

results = retrieve_memory("Tell me about AI", top_k=3)

for result in results:
    print(f"Role: {result['role']}")
    print(f"Text: {result['text']}")
    print(f"Similarity: {result['similarity_score']}")
```

**Parameters:**
- `query` (str): Search query
- `top_k` (int): Number of results to return

**Returns:**
List of dictionaries with keys:
- `text`: Original text
- `role`: Agent role
- `timestamp`: When stored
- `similarity_score`: Relevance score (0-1)
- `distance`: Vector distance

---

#### `get_context(query, top_k=5)`
Get formatted context string for prompts.

```python
from engine.memory.rag import get_context

context = get_context("How does machine learning work?", top_k=3)
# Returns:
# [Memory 1 - AI Expert]
# Machine learning uses algorithms to learn from data...
#
# [Memory 2 - Data Scientist]
# Training models involves feeding data and adjusting weights...
```

**Parameters:**
- `query` (str): Search query
- `top_k` (int): Number of memories to include

**Returns:**
- Formatted string ready to append to prompts

---

#### `clear_memory()`
Clear all stored memories.

```python
from engine.memory.rag import clear_memory

clear_memory()  # Deletes all memories
```

---

#### `get_memory_stats()`
Get memory system statistics.

```python
from engine.memory.rag import get_memory_stats

stats = get_memory_stats()
# Returns:
# {
#     "total_memories": 42,
#     "index_size": 42,
#     "embedding_dim": 384,
#     "storage_path": "D:/Projects/.../engine/memory/storage"
# }
```

## Integration with Agent.py

The RAG system is automatically integrated into the agent workflow:

### Sequential Workflow
```python
# For each agent after the first:
base_prompt = f"you are {role} and your motive is {goal}"

# Retrieve relevant context from previous agents
relevant_context = get_context(base_prompt, top_k=3)

if relevant_context:
    prompt = f"{base_prompt}\n\nRelevant previous context:\n{relevant_context}"
```

### Parallel Workflow
```python
# Each branch can access context from previous workflows
relevant_context = get_context(base_prompt, top_k=2)

# Consolidation agent gets more context
relevant_context = get_context(base_prompt, top_k=5)
```

## Storage Structure

```
engine/memory/
├── __init__.py
├── rag.py
└── storage/
    ├── faiss_index.bin      # Vector index
    ├── metadata.json         # Text and metadata
    └── model_cache/          # Cached embedding model
        └── ...
```

### metadata.json Structure
```json
[
  {
    "text": "Python is a high-level programming language...",
    "role": "Researcher",
    "timestamp": "2026-01-17T10:30:45.123456",
    "index_id": 0,
    "topic": "programming"
  }
]
```

## Performance Benefits

### Without RAG (Old System)
```
Iteration 1: 50 lines → LLM
Iteration 2: 200 lines → LLM
Iteration 3: 500 lines → LLM
Iteration 6: 3000 lines → LLM ❌ Token limit exceeded
```

### With RAG (New System)
```
Iteration 1: 50 lines → Stored
Iteration 2: 50 base + 150 relevant → LLM ✓
Iteration 3: 50 base + 150 relevant → LLM ✓
Iteration 6: 50 base + 150 relevant → LLM ✓
```

**Benefits:**
- ✅ Constant context size (~200 lines)
- ✅ Only relevant information included
- ✅ No token limit issues
- ✅ Faster processing
- ✅ Better focus for agents

## Testing

Run the RAG test script:

```bash
python test_rag.py
```

This will:
1. Clear previous memories
2. Store 5 test memories
3. Test retrieval with different queries
4. Display similarity scores
5. Show formatted context strings

## Advanced Configuration

### Change Embedding Model

```python
from engine.memory.rag import MemoryRAG

# Use a larger model for better accuracy
memory = MemoryRAG(model_name="all-mpnet-base-v2")

# Use a multilingual model
memory = MemoryRAG(model_name="paraphrase-multilingual-MiniLM-L12-v2")
```

### Custom Storage Location

```python
memory = MemoryRAG(memory_dir="D:/custom/path/memories")
```

### Adjust Retrieval Count

```python
# For simple queries, fewer results
context = get_context(query, top_k=2)

# For complex consolidation, more results
context = get_context(query, top_k=10)
```

## Troubleshooting

### Issue: "sentence-transformers not installed"
```bash
pip install sentence-transformers
```

### Issue: "faiss-cpu not installed"
```bash
pip install faiss-cpu
```

### Issue: Memory not persisting
Check that `engine/memory/storage/` exists and is writable.

### Issue: Poor retrieval quality
- Try using a larger embedding model
- Increase `top_k` parameter
- Ensure stored text is descriptive enough

## Best Practices

1. **Store Complete Thoughts**: Store full responses, not fragments
2. **Use Descriptive Roles**: Helps identify memory sources
3. **Add Metadata**: Include topic, task, etc. for better organization
4. **Adjust top_k**: 
   - 2-3 for simple queries
   - 5-7 for consolidation
   - 10+ for research tasks
5. **Clear Periodically**: Clear memories between unrelated workflows

## Example: Complete Workflow

```python
from engine.Agent import run_agent
from engine.memory.rag import clear_memory, get_memory_stats

# Clear previous workflow memories
clear_memory()

# Run agent workflow (automatically uses RAG)
run_agent("engine/examples/config_sequential.yml")

# Check how many memories were created
stats = get_memory_stats()
print(f"Stored {stats['total_memories']} memories")
```

## Future Enhancements

- [ ] Support for IndexIVFFlat for 10k+ memories
- [ ] Metadata filtering (e.g., only retrieve from specific roles)
- [ ] Time-based relevance decay
- [ ] Hybrid search (keyword + semantic)
- [ ] Memory summarization for long-term storage
