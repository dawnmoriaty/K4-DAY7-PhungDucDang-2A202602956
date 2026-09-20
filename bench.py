#!/usr/bin/env python3
"""
Benchmark script - CP5 Production Version
Đo chất lượng retrieval của chiến lược chunking trên 5 benchmark queries.

Mỗi thành viên chỉ thay đổi DUY NHẤT dòng CHUNKER_STRATEGY để so sánh công bằng.
"""

import csv
from pathlib import Path
from src.chunking import (
    FixedSizeChunker, 
    SentenceChunker, 
    RecursiveChunker,
    HierarchicalChunker,
    MixedHierarchicalRecursiveChunker
)
from src.store import EmbeddingStore
from src.agent import KnowledgeBaseAgent
from src.embeddings import _mock_embed  # Đổi thành real embedding nếu có
from src.models import Document

# ============================================================================
# CHIẾN LƯỢC CỦA THÀNH VIÊN NÀY
# Mỗi người CHỈ ĐỔI DÒNG NÀY, mọi thứ khác giữ nguyên để so sánh công bằng
# ============================================================================
CHUNKER_STRATEGY = "recursive"  # Các giá trị: "fixed" / "sentence" / "recursive" / "hierarchical" / "mixed"

# Cấu hình
DATA_DIR = "data/shopee"
QUERIES_CSV = "benchmark/benchmark_queries.csv"
CHUNK_SIZE = 500
OVERLAP = 50  # Cho FixedSizeChunker


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Tách frontmatter YAML thành metadata và phần thân.
    
    Returns:
        (metadata_dict, body_content)
    """
    if not content.startswith("---"):
        return {}, content
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    
    metadata = {}
    frontmatter_lines = parts[1].strip().split('\n')
    
    for line in frontmatter_lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"\'')  # Remove quotes
            metadata[key] = value
    
    body = parts[2].strip()
    return metadata, body


def get_chunker(strategy: str):
    """Khởi tạo chunker theo chiến lược"""
    if strategy == "fixed":
        return FixedSizeChunker(chunk_size=CHUNK_SIZE, overlap=OVERLAP)
    elif strategy == "sentence":
        return SentenceChunker(max_sentences_per_chunk=3)
    elif strategy == "recursive":
        return RecursiveChunker(chunk_size=CHUNK_SIZE)
    elif strategy == "hierarchical":
        return HierarchicalChunker(chunk_size=CHUNK_SIZE, preserve_headings=True)
    elif strategy == "mixed":
        return MixedHierarchicalRecursiveChunker(chunk_size=CHUNK_SIZE, preserve_headings=True)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def load_and_chunk_documents() -> list[Document]:
    """
    1. Đọc từng file .md
    2. Tách frontmatter thành metadata và phần thân thành content
    3. Chunk phần thân
    4. Mỗi chunk thành một Document với metadata kế thừa từ frontmatter
    
    Quan trọng:
    - Document.id = "{filename}#{chunk_index}"
    - metadata['doc_id'] = filename (không có #{i})
    - Metadata frontmatter phải được trải vào MỌI chunk
    """
    chunker = get_chunker(CHUNKER_STRATEGY)
    data_path = Path(DATA_DIR)
    documents = []
    
    print(f"📁 Loading documents from: {DATA_DIR}")
    print(f"🔧 Using chunker: {CHUNKER_STRATEGY}")
    
    for md_file in sorted(data_path.glob("*.md")):
        content = md_file.read_text(encoding='utf-8')
        
        # Tách frontmatter
        metadata, body = parse_frontmatter(content)
        
        # Chunk phần thân (KHÔNG chunk frontmatter)
        chunks = chunker.chunk(body)
        
        # Tạo Document cho mỗi chunk
        for i, chunk in enumerate(chunks):
            # Document.id cho chunk cụ thể
            doc_id_full = f"{md_file.stem}#{i}"
            
            # metadata['doc_id'] trỏ về file gốc (để delete_document hoạt động)
            meta_copy = dict(metadata)
            meta_copy['doc_id'] = md_file.stem  # ⭐ QUAN TRỌNG: không có #{i}
            meta_copy['chunk_index'] = i
            meta_copy['source_file'] = md_file.name
            
            documents.append(Document(
                id=doc_id_full,
                content=chunk,
                metadata=meta_copy
            ))
    
    print(f"✅ Loaded {len(documents)} chunks from {len(list(data_path.glob('*.md')))} files\n")
    return documents


def load_benchmark_queries() -> list[dict]:
    """Load 5 benchmark queries từ CSV"""
    queries = []
    with open(QUERIES_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            queries.append(row)
    return queries


def run_benchmark():
    """
    Chạy benchmark theo format CP5:
    1. Nạp documents vào EmbeddingStore
    2. Chạy 5 query qua search_with_filter()
    3. In top-3 kèm score và doc_id để đối chiếu với gold answer
    4. Chấm 2 mức: doc_id match + answer marker found
    """
    
    print("="*80)
    print(f"📊 BENCHMARK - Chiến lược: {CHUNKER_STRATEGY.upper()}")
    print("="*80)
    
    # 1. Load & chunk documents
    documents = load_and_chunk_documents()
    
    # 2. Nạp vào EmbeddingStore
    print("⏳ Nạp vào EmbeddingStore...")
    store = EmbeddingStore(embedding_fn=_mock_embed)
    store.add_documents(documents)
    print(f"✅ Store size: {store.get_collection_size()} chunks\n")
    
    # 3. Load queries
    queries = load_benchmark_queries()
    print(f"📋 Running {len(queries)} benchmark queries...\n")
    
    # 4. Chạy từng query
    results = []
    
    for query_row in queries:
        query_id = int(query_row['id'])
        query = query_row['query']
        gold_doc_id = query_row['gold_doc_id']
        answer_marker = query_row['answer_marker']
        audience_filter = query_row.get('audience_filter', '').strip()
        
        print(f"\n{'='*80}")
        print(f"Query #{query_id}: {query}")
        print(f"Gold doc_id: {gold_doc_id}")
        print(f"Answer marker: {answer_marker}")
        
        # Search (với filter nếu có)
        if audience_filter:
            print(f"🔍 Searching with filter: audience={audience_filter}")
            search_results = store.search_with_filter(
                query,
                top_k=3,
                metadata_filter={'audience': audience_filter}
            )
        else:
            print(f"🔍 Searching without filter")
            search_results = store.search(query, top_k=3)
        
        # Print top-3 kèm score và doc_id
        print(f"\n📊 Top-3 Results:")
        for rank, result in enumerate(search_results, 1):
            doc_id = result['metadata'].get('doc_id', '?')
            score = result['score']
            content_preview = result['content'][:100].replace('\n', ' ')
            
            marker_found = answer_marker.lower() in result['content'].lower() if answer_marker else False
            marker_icon = "✅" if marker_found else "❌"
            gold_icon = "🎯" if doc_id == gold_doc_id else "  "
            
            print(f"  [{rank}] {gold_icon} doc_id={doc_id}, score={score:.4f}, marker={marker_icon}")
            print(f"      Preview: {content_preview}...")
        
        # Chấm 2 mức
        top_1_doc_id = search_results[0]['metadata'].get('doc_id', '?') if search_results else '?'
        top_1_correct = (top_1_doc_id == gold_doc_id)
        
        # Kiểm tra answer marker có trong top-3 không
        marker_found_in_top3 = False
        gold_in_top3 = False
        
        for result in search_results[:3]:
            doc_id = result['metadata'].get('doc_id', '')
            if doc_id == gold_doc_id:
                gold_in_top3 = True
                if answer_marker and answer_marker.lower() in result['content'].lower():
                    marker_found_in_top3 = True
                    break
        
        # Thang điểm CP5
        if top_1_correct and marker_found_in_top3:
            score = 2  # Đúng top-1 + có answer marker
        elif gold_in_top3:
            score = 1  # Gold trong top-3 nhưng không top-1 hoặc thiếu marker
        else:
            score = 0  # Gold không trong top-3
        
        result_icon = "✅" if score == 2 else ("⚠️" if score == 1 else "❌")
        print(f"\n{result_icon} Score: {score}/2 (Top-1 correct: {top_1_correct}, Marker in top-3: {marker_found_in_top3})")
        
        results.append({
            'query_id': query_id,
            'query': query,
            'gold_doc_id': gold_doc_id,
            'top_1_doc_id': top_1_doc_id,
            'top_1_correct': top_1_correct,
            'gold_in_top3': gold_in_top3,
            'marker_found': marker_found_in_top3,
            'score': score
        })
    
    # 5. Summary
    print(f"\n\n{'='*80}")
    print(f"📈 SUMMARY - {CHUNKER_STRATEGY.upper()}")
    print(f"{'='*80}")
    
    total_score = sum(r['score'] for r in results)
    max_score = len(results) * 2
    top_1_correct_count = sum(1 for r in results if r['top_1_correct'])
    marker_found_count = sum(1 for r in results if r['marker_found'])
    
    print(f"Total Chunks: {len(documents)}")
    print(f"Total Queries: {len(results)}")
    print(f"Total Score: {total_score}/{max_score} ({100*total_score//max_score}%)")
    print(f"Top-1 Correct: {top_1_correct_count}/{len(results)} ({100*top_1_correct_count//len(results)}%)")
    print(f"Marker Found in Top-3: {marker_found_count}/{len(results)} ({100*marker_found_count//len(results)}%)")
    
    print(f"\n{'='*80}\n")
    
    return results


if __name__ == '__main__':
    run_benchmark()
