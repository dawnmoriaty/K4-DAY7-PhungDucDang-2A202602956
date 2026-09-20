#!/usr/bin/env python3
"""
Benchmark script - Đo từng chunker riêng lẻ.

Sử dụng:
    python bench_single.py --chunker recursive
    python bench_single.py --chunker hierarchical
    python bench_single.py --chunker mixed
"""

import sys
import csv
from pathlib import Path
from dataclasses import dataclass

# Import from src
from src.chunking import (
    FixedSizeChunker, SentenceChunker, RecursiveChunker,
    HierarchicalChunker
)

# Try import MixedHierarchicalRecursiveChunker, fallback nếu chưa có
try:
    from src.chunking import MixedHierarchicalRecursiveChunker
except ImportError:
    MixedHierarchicalRecursiveChunker = None
from src.store import EmbeddingStore
from src.agent import KnowledgeBaseAgent
from src.embeddings import SmartMockEmbedder, _mock_embed
from src.models import Document


@dataclass
class BenchmarkResult:
    query_id: int
    query: str
    chunker: str
    num_chunks_total: int
    top_1_doc_id: str
    top_1_score: float
    top_1_in_gold: bool
    top_3_relevant: int
    answer_marker_found: bool


def load_benchmark_queries(csv_path: str) -> list[dict]:
    """Load từ benchmark_queries.csv"""
    queries = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            queries.append(row)
    return queries


def load_and_chunk(data_dir: str, chunker_name: str) -> tuple[list[Document], int]:
    """
    Load tài liệu từ data_dir, chunk, trả về (documents, total_chunks)
    """
    documents = []
    total_chunks = 0

    # Chọn chunker
    if chunker_name == "fixed":
        chunker = FixedSizeChunker(chunk_size=500, overlap=50)
    elif chunker_name == "sentence":
        chunker = SentenceChunker(max_sentences_per_chunk=3)
    elif chunker_name == "recursive":
        chunker = RecursiveChunker(chunk_size=500)
    elif chunker_name == "hierarchical":
        chunker = HierarchicalChunker(chunk_size=500, preserve_headings=True)
    elif chunker_name == "mixed":
        if MixedHierarchicalRecursiveChunker is None:
            raise ValueError("MixedHierarchicalRecursiveChunker not available yet")
        chunker = MixedHierarchicalRecursiveChunker(chunk_size=500, preserve_headings=True)
    else:
        raise ValueError(f"Unknown chunker: {chunker_name}")

    # Load tài liệu
    data_path = Path(data_dir)
    for md_file in sorted(data_path.glob("*.md")):
        content = md_file.read_text(encoding='utf-8')

        # Tách frontmatter
        metadata = {}
        body = content

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                metadata_str = parts[1]
                body = parts[2].strip()

                # Parse YAML-like frontmatter
                for line in metadata_str.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip().strip('"\'')

        # Chunk
        chunks = chunker.chunk(body)
        total_chunks += len(chunks)

        # Tạo Document cho mỗi chunk
        for i, chunk in enumerate(chunks):
            doc_id = f"{md_file.stem}#{i}"
            meta_copy = dict(metadata)
            meta_copy['doc_id'] = md_file.stem  # ⭐ Quan trọng!

            documents.append(Document(
                id=doc_id,
                content=chunk,
                metadata=meta_copy
            ))

    return documents, total_chunks


def run_benchmark(chunker_name: str, queries_csv: str, data_dir: str):
    """Chạy benchmark cho một chunker"""
    print(f"\n{'='*80}")
    print(f"📊 BENCHMARK: {chunker_name.upper()}")
    print(f"{'='*80}\n")

    # 1. Load & chunk
    print(f"⏳ Loading & chunking ({data_dir})...")
    documents, total_chunks = load_and_chunk(data_dir, chunker_name)
    print(f"   ✅ {len(documents)} chunks tạo từ {total_chunks} sections\n")

    # 2. Nạp vào store
    store = EmbeddingStore(embedding_fn=SmartMockEmbedder())
    store.add_documents(documents)
    print(f"   ✅ Store size: {store.get_collection_size()}\n")

    # 3. Load queries
    queries_data = load_benchmark_queries(queries_csv)

    # 4. Chạy queries
    def fake_llm(prompt: str) -> str:
        return "[LLM response]"

    agent = KnowledgeBaseAgent(store, fake_llm)

    results = []

    print(f"Running {len(queries_data)} queries...\n")
    for query_row in queries_data:
        query_id = int(query_row['id'])
        query = query_row['query']
        gold_doc_id = query_row['gold_doc_id']
        answer_marker = query_row['answer_marker']
        audience_filter = query_row['audience_filter'] or None

        # Search (với filter nếu có)
        if audience_filter:
            search_results = store.search_with_filter(
                query,
                top_k=3,
                metadata_filter={'audience': audience_filter}
            )
        else:
            search_results = store.search(query, top_k=3)

        # Phân tích kết quả
        top_1_doc_id = search_results[0]['metadata'].get('doc_id', '?') if search_results else '?'
        top_1_score = search_results[0]['score'] if search_results else 0.0
        top_1_in_gold = top_1_doc_id == gold_doc_id

        # Check top-3 có chunk liên quan không
        top_3_relevant = 0
        answer_marker_found = False
        for result in search_results[:3]:
            doc_id = result['metadata'].get('doc_id', '')
            if doc_id == gold_doc_id:
                top_3_relevant += 1
                # Check có chứa answer_marker không
                if answer_marker and answer_marker.lower() in result['content'].lower():
                    answer_marker_found = True

        result = BenchmarkResult(
            query_id=query_id,
            query=query,
            chunker=chunker_name,
            num_chunks_total=len(documents),
            top_1_doc_id=top_1_doc_id,
            top_1_score=round(top_1_score, 3),
            top_1_in_gold=top_1_in_gold,
            top_3_relevant=top_3_relevant,
            answer_marker_found=answer_marker_found
        )
        results.append(result)

        # Print từng query
        status = "✅" if top_1_in_gold else "❌"
        print(f"{status} [Q{query_id}] {query[:60]}...")
        print(f"   Top-1: {top_1_doc_id} (score={top_1_score}, gold={gold_doc_id})")
        print(f"   Relevant in top-3: {top_3_relevant}/3, Marker found: {answer_marker_found}")
        print()

    # 5. Summary
    print(f"\n{'='*80}")
    print(f"📈 SUMMARY - {chunker_name.upper()}")
    print(f"{'='*80}")

    passed = sum(1 for r in results if r.top_1_in_gold)
    marker_found = sum(1 for r in results if r.answer_marker_found)

    print(f"Total Chunks: {total_chunks}")
    print(f"Total Queries: {len(results)}")
    print(f"Top-1 Correct: {passed}/{len(results)} ({100*passed//len(results)}%)")
    print(f"Marker Found: {marker_found}/{len(results)} ({100*marker_found//len(results)}%)")

    # Lưu CSV
    output_csv = f"results_{chunker_name}.csv"
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'query_id', 'query', 'chunker', 'num_chunks_total',
            'top_1_doc_id', 'top_1_score', 'top_1_in_gold',
            'top_3_relevant', 'answer_marker_found'
        ])
        writer.writeheader()
        for r in results:
            writer.writerow({
                'query_id': r.query_id,
                'query': r.query,
                'chunker': r.chunker,
                'num_chunks_total': r.num_chunks_total,
                'top_1_doc_id': r.top_1_doc_id,
                'top_1_score': r.top_1_score,
                'top_1_in_gold': r.top_1_in_gold,
                'top_3_relevant': r.top_3_relevant,
                'answer_marker_found': r.answer_marker_found
            })

    print(f"\n📁 Kết quả lưu: {output_csv}\n")

    return results


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python bench_single.py --chunker [recursive|hierarchical|mixed]")
        sys.exit(1)

    chunker = sys.argv[2] if len(sys.argv) > 2 else 'recursive'
    queries_csv = 'benchmark/benchmark_queries.csv'
    data_dir = 'data/shopee'  # ✅ Use real Shopee data

    run_benchmark(chunker, queries_csv, data_dir)
