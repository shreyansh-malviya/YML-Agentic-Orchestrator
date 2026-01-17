"""
Test RAG Memory System
"""

from engine.memory.rag import store_memory, retrieve_memory, get_context, clear_memory, get_memory_stats

print("="*70)
print("Testing RAG Memory System")
print("="*70)

# Clear previous memories
print("\n🗑 Clearing previous memories...")
clear_memory()

# Store some test memories
print("\n📝 Storing memories...")

store_memory(
    "Python is a high-level programming language known for its simplicity and readability.",
    role="Researcher",
    metadata={"topic": "programming"}
)

store_memory(
    "Machine learning is a subset of AI that enables systems to learn from data.",
    role="AI Expert",
    metadata={"topic": "AI"}
)

store_memory(
    "FAISS is a library for efficient similarity search and clustering of dense vectors.",
    role="Engineer",
    metadata={"topic": "vector-db"}
)

store_memory(
    "RAG combines retrieval and generation to provide context-aware AI responses.",
    role="AI Architect",
    metadata={"topic": "AI"}
)

store_memory(
    "Vector embeddings represent text as numerical vectors in high-dimensional space.",
    role="Data Scientist",
    metadata={"topic": "embeddings"}
)

# Get stats
print("\n📊 Memory Statistics:")
stats = get_memory_stats()
for key, value in stats.items():
    print(f"  {key}: {value}")

# Test retrieval
print("\n" + "="*70)
print("Testing Retrieval")
print("="*70)

queries = [
    "My name is kartik",
    # "What is vector search?",
    # "Explain programming languages"
]

for query in queries:
    print(f"\n🔍 Query: {query}")
    print("-"*70)
    
    # Retrieve memories
    results = retrieve_memory(query, top_k=1)
    
    for i, result in enumerate(results, 1):
        print(f"\n  Result {i}:")
        print(f"    Role: {result['role']}")
        print(f"    Similarity: {result['similarity_score']:.4f}")
        print(f"    Text: {result['text'][:100]}...")

# Test context string
print("\n" + "="*70)
print("Testing Context String")
print("="*70)

query = "How does AI work with vectors?"
print(f"\n🔍 Query: {query}")
print("-"*70)

context = get_context(query, top_k=3)
print("\n📄 Context String:")
print(context)

print("\n" + "="*70)
print("✅ RAG Test Complete!")
print("="*70)
