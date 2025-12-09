#!/usr/bin/env python3
"""
Build FAISS Index from Academic Corpus.

Loads the academic corpus and builds a FAISS vector store for RAG.

Usage:
    python scripts/build_rag_index.py
    python scripts/build_rag_index.py --input test-docs/academic_corpus.jsonl
    python scripts/build_rag_index.py --output data/faiss
"""

import argparse
import json
from pathlib import Path
from tqdm import tqdm

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag import FAISSVectorStore, Chunk


def load_jsonl_corpus(filepath: str) -> list:
    """Load chunks from JSONL file."""
    chunks = []
    with open(filepath) as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks


def build_index(
    input_path: str = "test-docs/academic_corpus.jsonl",
    output_dir: str = "data/faiss",
    batch_size: int = 50,
) -> None:
    """
    Build FAISS index from corpus.
    
    Args:
        input_path: Path to JSONL corpus
        output_dir: Directory to save FAISS index
        batch_size: Batch size for embedding generation
    """
    input_file = Path(input_path)
    
    if not input_file.exists():
        print(f"Error: Corpus file not found: {input_path}")
        print("Run 'python scripts/generate_academic_corpus.py' first")
        return
    
    print(f"\nBuilding FAISS index...")
    print(f"Input: {input_path}")
    print(f"Output: {output_dir}")
    print("-" * 50)
    
    # Load corpus
    print("Loading corpus...")
    corpus = load_jsonl_corpus(input_path)
    print(f"Loaded {len(corpus)} entries")
    
    # Convert to Chunk objects
    chunks = []
    for i, entry in enumerate(corpus):
        chunk = Chunk(
            text=entry["content"],
            source=entry["id"],
            chunk_index=0,
            start_char=0,
            end_char=len(entry["content"]),
            metadata={
                "domain": entry["domain"],
                "topic": entry["topic"],
            }
        )
        chunks.append(chunk)
    
    # Create vector store
    print("\nInitializing vector store...")
    store = FAISSVectorStore(persist_dir=output_dir)
    
    # Add chunks in batches
    print(f"\nGenerating embeddings (batch_size={batch_size})...")
    total_cost = 0.0
    
    for i in tqdm(range(0, len(chunks), batch_size), desc="Embedding"):
        batch = chunks[i:i + batch_size]
        cost = store.add_chunks(batch)
        total_cost += cost
    
    # Save
    print("\nSaving index...")
    store.save()
    
    # Print summary
    stats = store.get_stats()
    print("-" * 50)
    print(f"✓ Index built successfully!")
    print(f"  Chunks indexed: {stats['num_chunks']}")
    print(f"  Embedding cost: ${stats['index_cost']:.4f}")
    print(f"  Index saved to: {output_dir}")
    
    # Test search
    print("\n--- Test Search ---")
    test_query = "How do transformer models work?"
    results, query_cost = store.search(test_query, k=3)
    
    print(f"Query: '{test_query}'")
    print(f"Query cost: ${query_cost:.6f}")
    print(f"Top 3 results:")
    for r in results:
        print(f"  [{r.rank}] {r.chunk.source} (score: {r.score:.3f})")
        print(f"      {r.chunk.text[:100]}...")


def main():
    parser = argparse.ArgumentParser(
        description="Build FAISS index from academic corpus"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default="test-docs/academic_corpus.jsonl",
        help="Input JSONL corpus file"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="data/faiss",
        help="Output directory for FAISS index"
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=50,
        help="Batch size for embedding generation"
    )
    
    args = parser.parse_args()
    
    build_index(
        input_path=args.input,
        output_dir=args.output,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
