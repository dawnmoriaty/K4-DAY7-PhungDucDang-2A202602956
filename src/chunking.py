from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        # TODO: split into sentences, group into chunks
        if not text:
            return []
        
        # Tách câu nhưng GIỮ dấu câu (lookahead)
        # (?<=[.!?])\s+ = "sau dấu câu + space"
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Nhóm theo max_sentences_per_chunk
        chunks = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk = ' '.join(sentences[i:i + self.max_sentences_per_chunk])
            chunks.append(chunk)
        
        return chunks

class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        # TODO: implement recursive splitting strategy
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # TODO: recursive helper used by RecursiveChunker.chunk
        # Base case 1: text đủ ngắn
        if len(current_text) <= self.chunk_size:
            return [current_text]
        
        # Base case 2: hết separators → cắt cứng
        if not remaining_separators:
            chunks = []
            for i in range(0, len(current_text), self.chunk_size):
                chunks.append(current_text[i:i+self.chunk_size])
            return chunks
        
        # Lấy separator đầu tiên
        sep = remaining_separators[0]
        
        # Base case 3: empty separator
        if not sep:
            chunks = []
            for i in range(0, len(current_text), self.chunk_size):
                chunks.append(current_text[i:i+self.chunk_size])
            return chunks
        
        # Chia theo separator
        parts = current_text.split(sep)
        
        # Đệ quy: nếu part dài quá → thử separator tiếp theo
        good_chunks = []
        for part in parts:
            if len(part) > self.chunk_size:
                # Quá dài → đệ quy với separator nhỏ hơn
                good_chunks.extend(self._split(part, remaining_separators[1:]))
            elif part:
                # Đủ ngắn → giữ lại
                good_chunks.append(part)
        
        # ⭐ BƯỚC GOM LẠI (quan trọng!)
        # Nối các chunk nhỏ liền kề tới sát chunk_size
        merged = []
        current = ""
        for chunk in good_chunks:
            # Nếu nối được mà vẫn <= chunk_size → nối
            if len(current) + len(sep) + len(chunk) <= self.chunk_size:
                current = (current + sep + chunk) if current else chunk
            else:
                # Nếu không nối được → lưu current, bắt đầu chunk mới
                if current:
                    merged.append(current)
                current = chunk
        
        # Lưu chunk cuối cùng
        if current:
            merged.append(current)
        
        return merged


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    # TODO: implement cosine similarity formula
    import math
    
    # Tính dot product
    dot_product = _dot(vec_a, vec_b)
    
    # Tính độ dài (magnitude)
    mag_a = math.sqrt(sum(x*x for x in vec_a))
    mag_b = math.sqrt(sum(x*x for x in vec_b))
    
    # Chặn chia cho 0
    if mag_a == 0 or mag_b == 0:
        return 0.0
    
    return dot_product / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        # TODO: call each chunker, compute stats, return comparison dict
        """Return dict with keys: fixed_size, by_sentences, recursive, hierarchical"""
    
        if not text:
            return {
                'fixed_size': {'count': 0, 'avg_length': 0.0, 'chunks': []},
                'by_sentences': {'count': 0, 'avg_length': 0.0, 'chunks': []},
                'recursive': {'count': 0, 'avg_length': 0.0, 'chunks': []},
                'hierarchical': {'count': 0, 'avg_length': 0.0, 'chunks': []}
            }
        
        # Gọi 4 chunker
        fixed_chunks = FixedSizeChunker(chunk_size=chunk_size).chunk(text)
        sentence_chunks = SentenceChunker(max_sentences_per_chunk=3).chunk(text)
        recursive_chunks = RecursiveChunker(chunk_size=chunk_size).chunk(text)
        hierarchical_chunks = HierarchicalChunker(chunk_size=chunk_size).chunk(text)
        
        # Helper: tính stats
        def stats(chunks):
            count = len(chunks)
            if count == 0:
                avg = 0.0
            else:
                avg = sum(len(c) for c in chunks) / count
            return {
                'count': count,
                'avg_length': avg,
                'chunks': chunks
            }
        
        return {
            'fixed_size': stats(fixed_chunks),
            'by_sentences': stats(sentence_chunks),
            'recursive': stats(recursive_chunks),
            'hierarchical': stats(hierarchical_chunks)
        }



class HierarchicalChunker:
    """
    Split text by hierarchical structure (headings/sections).
    
    Designed for structured documents like policies, terms, regulations.
    Each section becomes a chunk. Long sections are recursively split.
    
    Features:
        - Preserves heading context in each chunk
        - Respects document structure (## Section → ### Subsection)
        - Falls back to RecursiveChunker for oversized sections
    """
    
    def __init__(self, chunk_size: int = 1000, preserve_headings: bool = True) -> None:
        self.chunk_size = chunk_size
        self.preserve_headings = preserve_headings
        self._recursive_fallback = RecursiveChunker(chunk_size=chunk_size)
    
    def chunk(self, text: str) -> list[str]:
        """
        Split by Markdown headings (## Header, ### Subheader).
        
        Algorithm:
            1. Detect headings (##, ###, ####)
            2. Split into sections
            3. For each section:
               - If small enough → keep as-is
               - If too large → recursive split BUT preserve heading
        
        Example:
            Input:
                ## Chính Sách Đổi Trả
                Khách hàng có 7 ngày...
                
                ## Chính Sách Bảo Hành
                Sản phẩm được bảo hành...
            
            Output:
                [
                    "## Chính Sách Đổi Trả\nKhách hàng có 7 ngày...",
                    "## Chính Sách Bảo Hành\nSản phẩm được bảo hành..."
                ]
        """
        if not text:
            return []
        
        # Detect headings: lines starting with ## or ###
        lines = text.split('\n')
        sections = []
        current_heading = ""
        current_content = []
        
        for line in lines:
            # Check if line is a heading
            if re.match(r'^#{2,4}\s+', line):
                # Save previous section
                if current_content:
                    section_text = '\n'.join(current_content).strip()
                    if section_text:
                        sections.append({
                            'heading': current_heading,
                            'content': section_text
                        })
                
                # Start new section
                current_heading = line
                current_content = [line] if self.preserve_headings else []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            section_text = '\n'.join(current_content).strip()
            if section_text:
                sections.append({
                    'heading': current_heading,
                    'content': section_text
                })
        
        # If no headings found, treat entire text as one section
        if not sections:
            if len(text) <= self.chunk_size:
                return [text]
            else:
                return self._recursive_fallback.chunk(text)
        
        # Process each section
        chunks = []
        for section in sections:
            content = section['content']
            heading = section['heading']
            
            # If section fits → keep as-is
            if len(content) <= self.chunk_size:
                chunks.append(content)
            else:
                # Section too large → split recursively but preserve heading
                sub_chunks = self._recursive_fallback.chunk(content)
                
                # Re-attach heading to each sub-chunk
                if self.preserve_headings and heading:
                    for i, sub_chunk in enumerate(sub_chunks):
                        # Only add heading to first sub-chunk
                        if i == 0:
                            chunks.append(sub_chunk)
                        else:
                            # For subsequent chunks, add heading + context marker
                            chunks.append(f"{heading} (tiếp)\n{sub_chunk}")
                else:
                    chunks.extend(sub_chunks)
        
        return chunks
    
    def chunk_with_metadata(self, text: str) -> list[dict]:
        """
        Return chunks with metadata about their hierarchical position.
        
        Returns:
            List of dicts with keys:
                - content: chunk text
                - heading: section heading (if any)
                - level: heading level (2=##, 3=###, 4=####)
                - index: chunk index within section
        
        Useful for preserving document structure in metadata.
        """
        if not text:
            return []
        
        chunks_with_meta = []
        lines = text.split('\n')
        
        current_heading = ""
        current_level = 0
        current_content = []
        section_index = 0
        
        for line in lines:
            heading_match = re.match(r'^(#{2,4})\s+(.+)$', line)
            
            if heading_match:
                # Save previous section
                if current_content:
                    section_text = '\n'.join(current_content).strip()
                    if section_text:
                        if len(section_text) <= self.chunk_size:
                            chunks_with_meta.append({
                                'content': section_text,
                                'heading': current_heading,
                                'level': current_level,
                                'index': 0
                            })
                        else:
                            # Split large section
                            sub_chunks = self._recursive_fallback.chunk(section_text)
                            for idx, sub in enumerate(sub_chunks):
                                chunks_with_meta.append({
                                    'content': sub,
                                    'heading': current_heading,
                                    'level': current_level,
                                    'index': idx
                                })
                
                # Start new section
                current_heading = heading_match.group(2).strip()
                current_level = len(heading_match.group(1))
                current_content = [line] if self.preserve_headings else []
                section_index += 1
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            section_text = '\n'.join(current_content).strip()
            if section_text:
                if len(section_text) <= self.chunk_size:
                    chunks_with_meta.append({
                        'content': section_text,
                        'heading': current_heading,
                        'level': current_level,
                        'index': 0
                    })
                else:
                    sub_chunks = self._recursive_fallback.chunk(section_text)
                    for idx, sub in enumerate(sub_chunks):
                        chunks_with_meta.append({
                            'content': sub,
                            'heading': current_heading,
                            'level': current_level,
                            'index': idx
                        })
        
        return chunks_with_meta


class MixedHierarchicalRecursiveChunker:
    """
    Hybrid chunker combining Hierarchical + Recursive strategies.
    
    Strategy:
        1. First split by Markdown headings (hierarchical structure)
        2. Then recursively split oversized sections (coherence preservation)
        3. Preserve heading context at each level
    
    Why Mix?
        - Hierarchical: captures document structure (sections, subsections)
        - Recursive: maintains semantic coherence within sections
        - Mixed: best of both - structure + coherence
    
    Expected to work well for Shopee e-commerce policies (structured + detailed).
    """
    
    def __init__(self, chunk_size: int = 500, preserve_headings: bool = True) -> None:
        self.chunk_size = chunk_size
        self.preserve_headings = preserve_headings
        self._hierarchical = HierarchicalChunker(chunk_size=chunk_size, preserve_headings=preserve_headings)
        self._recursive = RecursiveChunker(chunk_size=chunk_size)
    
    def chunk(self, text: str) -> list[str]:
        """
        Split using mixed hierarchical + recursive strategy.
        
        Algorithm:
            1. Use HierarchicalChunker to split by sections
            2. For each chunk from step 1:
               - If small enough → keep as-is
               - If too large → recursive split (preserves coherence)
        
        Returns list of chunks preserving both structure and coherence.
        """
        if not text:
            return []
        
        # Step 1: Get hierarchical chunks (respects structure)
        hier_chunks = self._hierarchical.chunk(text)
        
        # Step 2: Post-process with recursive splitting if needed
        final_chunks = []
        for hier_chunk in hier_chunks:
            if len(hier_chunk) <= self.chunk_size:
                # Small enough → keep as-is
                final_chunks.append(hier_chunk)
            else:
                # Too large → recursive split to improve coherence
                # But try to preserve heading if present
                lines = hier_chunk.split('\n')
                heading = ""
                content_lines = []
                
                for line in lines:
                    if re.match(r'^#{2,4}\s+', line):
                        heading = line
                    else:
                        content_lines.append(line)
                
                content_text = '\n'.join(content_lines).strip()
                if content_text:
                    # Recursively split content
                    recursive_chunks = self._recursive.chunk(content_text)
                    
                    # Reattach heading to first chunk only
                    for i, chunk in enumerate(recursive_chunks):
                        if i == 0 and heading:
                            final_chunks.append(f"{heading}\n{chunk}")
                        else:
                            final_chunks.append(chunk)
                else:
                    # Only heading, no content → keep as-is
                    final_chunks.append(hier_chunk)
        
        return final_chunks
