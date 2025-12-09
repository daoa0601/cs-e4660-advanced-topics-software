"""
Document Chunking Utilities.

Provides text chunking for RAG indexing with configurable sizes and overlap.
"""

from dataclasses import dataclass
from typing import List, Optional
import re


@dataclass
class Chunk:
    """A chunk of text with metadata."""
    text: str
    source: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: Optional[dict] = None


def chunk_text(
    text: str,
    source: str = "unknown",
    chunk_size: int = 500,
    overlap: int = 50,
    split_on_sentences: bool = True,
) -> List[Chunk]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to chunk
        source: Source identifier
        chunk_size: Target characters per chunk
        overlap: Character overlap between chunks
        split_on_sentences: Try to break on sentence boundaries
        
    Returns:
        List of Chunk objects
    """
    if not text.strip():
        return []
    
    chunks = []
    
    if split_on_sentences:
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        char_pos = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                # Save current chunk
                chunks.append(Chunk(
                    text=current_chunk.strip(),
                    source=source,
                    chunk_index=chunk_index,
                    start_char=current_start,
                    end_char=char_pos,
                ))
                chunk_index += 1
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + " " + sentence
                current_start = char_pos - len(overlap_text)
            else:
                current_chunk += (" " if current_chunk else "") + sentence
            
            char_pos += len(sentence) + 1
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(Chunk(
                text=current_chunk.strip(),
                source=source,
                chunk_index=chunk_index,
                start_char=current_start,
                end_char=char_pos,
            ))
    else:
        # Simple fixed-size chunking
        for i in range(0, len(text), chunk_size - overlap):
            chunk_text = text[i:i + chunk_size]
            if chunk_text.strip():
                chunks.append(Chunk(
                    text=chunk_text.strip(),
                    source=source,
                    chunk_index=len(chunks),
                    start_char=i,
                    end_char=min(i + chunk_size, len(text)),
                ))
    
    return chunks


def chunk_document(
    content: str,
    filepath: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[Chunk]:
    """
    Chunk a document file's content.
    
    Args:
        content: Document content
        filepath: Path to the document (for metadata)
        chunk_size: Target characters per chunk
        overlap: Character overlap
        
    Returns:
        List of Chunk objects with metadata
    """
    chunks = chunk_text(
        text=content,
        source=filepath,
        chunk_size=chunk_size,
        overlap=overlap,
        split_on_sentences=True,
    )
    
    # Add metadata
    for chunk in chunks:
        chunk.metadata = {
            "filepath": filepath,
            "total_chunks": len(chunks),
        }
    
    return chunks


def chunk_jsonl_entries(
    entries: List[dict],
    text_field: str = "content",
    id_field: str = "id",
) -> List[Chunk]:
    """
    Create chunks from JSONL entries (one chunk per entry).
    
    Args:
        entries: List of dict entries
        text_field: Field containing the text
        id_field: Field containing the ID
        
    Returns:
        List of Chunk objects
    """
    chunks = []
    
    for i, entry in enumerate(entries):
        text = entry.get(text_field, "")
        source = entry.get(id_field, f"entry_{i}")
        
        if text.strip():
            chunks.append(Chunk(
                text=text.strip(),
                source=str(source),
                chunk_index=0,
                start_char=0,
                end_char=len(text),
                metadata=entry,
            ))
    
    return chunks
