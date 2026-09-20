# 📋 Lab 07 Reports - Phùng Đức Đăng

## Tổng Quan

Báo cáo lab 07 về RAG (Retrieval-Augmented Generation) cho hệ thống chính sách Shopee e-commerce.

## Cấu Trúc Báo Cáo

### 📄 REPORT_CANHAN.md (Báo cáo cá nhân)
**5 sections hoàn chỉnh:**

1. **Khởi động** (5đ)
   - Cosine similarity explanation
   - Chunking calculation: 23 chunks với overlap=50

2. **Hướng tiếp cận** (10đ)
   - SentenceChunker, RecursiveChunker implementation approach
   - EmbeddingStore helper methods (_make_record, _search_records)
   - KnowledgeBaseAgent RAG pattern

3. **Hoàn thiện code** (30đ)
   - ✅ **42/42 tests PASSED**
   - All core implementations complete

4. **Dự đoán độ tương tự** (5đ)
   - 5 sentence pairs predictions
   - Key insight: Embeddings hiểu ngữ cảnh, không chỉ từ vựng

5. **Kết quả truy xuất** (10đ)
   - **Score: 4/10 (40%)**
   - Query #1: **PERFECT 2/2** ✅
   - Key learning: Embedding quality > Chunking strategy

---

### 📄 REPORT_NHOM.md (Báo cáo nhóm)
**4 sections hoàn chỉnh:**

1. **Lựa chọn tài liệu** (10đ)
   - Chủ đề: Chính sách Trả hàng/Hoàn tiền Shopee
   - 9 documents, 66KB total
   - Metadata schema: doc_id, audience, category, title, source_url, etc.
   - ✅ Data governance checklist complete

2. **Thiết kế chiến lược** (15đ)
   - Baseline analysis với ChunkingStrategyComparator
   - 3 strategies tested:
     * **RecursiveChunker**: 121 chunks, 40% accuracy ✅ WINNER
     * HierarchicalChunker: 178 chunks, 20% accuracy
     * MixedChunker: 178 chunks, 20% accuracy
   - **Key insight**: Semantic coherence > explicit structure

3. **Chất lượng truy xuất** (10đ)
   - 5 benchmark queries (đa dạng về dạng hỏi)
   - Query #5 demonstrates metadata filtering (audience=seller)
   - **Finding**: Metadata filter essential for multi-audience data

4. **Thuyết trình & Bài học** (5đ)
   - **Embedding bottleneck discovery**: Hash-based → Keyword-based (+40% marker found)
   - Lesson: Optimize biggest bottleneck first (embedding > chunking)
   - Recommendations: Real embeddings + metadata filtering for production

---

## 🎯 Kết Quả Nổi Bật

### Benchmark Performance

| Metric | Hash Mock (old) | **SmartMock (new)** | Improvement |
|--------|----------------|-------------------|-------------|
| Total Score | 2/10 (20%) | **4/10 (40%)** | **+100%** |
| Top-1 Correct | 2/5 (40%) | 2/5 (40%) | Maintained |
| **Marker Found** | 0/5 (0%) | **2/5 (40%)** | **+40%** ✨ |

### Technical Achievements

1. ✅ **42/42 tests passing**
2. ✅ **3 chunking strategies** implemented & compared
3. ✅ **SmartMockEmbedder** with keyword extraction (29 Vietnamese stopwords)
4. ✅ **Metadata filtering** working (Query #5 with audience=seller)
5. ✅ **Complete documentation** in both reports

---

## 💡 Key Learnings

### 1. Embedding Quality = 70% of RAG Accuracy
- Switching from hash to keyword embedding: +100% total score
- ALL chunking strategies improved by same margin
- **Conclusion**: Fix embedding first, then optimize chunking

### 2. RecursiveChunker Wins for Prose-Heavy Documents
- 121 chunks vs 178 for Hierarchical/Mixed
- Better semantic coherence despite simpler approach
- **Lesson**: "More chunks" ≠ better retrieval

### 3. Metadata Filtering is Critical
- Query #5 without filter: mixed buyer/seller docs
- With `audience=seller` filter: 100% top-3 correct
- **Application**: Multi-audience/multi-domain RAG systems

---

## 📊 Comparison với Mock Embedding

### Before (Hash-based Mock)
```
Query #1: ❌ 0/2 (wrong document)
Query #2: ⚠️  1/2 (correct doc, no marker)
Query #5: ⚠️  1/2 (correct doc, no marker)
Total: 2/10 (20%), Marker: 0/5 (0%)
```

### After (Keyword-based SmartMock)
```
Query #1: ✅ 2/2 PERFECT (correct doc + marker!)
Query #2: ⚠️  1/2 (marker found in rank 2)
Query #5: ⚠️  1/2 (top-1 correct)
Total: 4/10 (40%), Marker: 2/5 (40%)
```

**Improvement Path**: Hash → Keyword → Neural (SentenceTransformer)

---

## 🚀 Production Recommendations

1. **Use Real Embeddings**
   - SentenceTransformer: `paraphrase-multilingual-MiniLM-L12-v2`
   - Or OpenAI API: `text-embedding-3-small`
   - Expected: 40% → 70-80% accuracy

2. **Implement Embedding Cache**
   - Hash content → save embedding
   - Avoid re-computation on benchmark runs
   - Critical for API-based embeddings (cost savings)

3. **Enhance Metadata Schema**
   - Current: audience, category
   - Add: topic, urgency, doc_type
   - Enable multi-factor filtering

4. **Monitor Retrieval Quality**
   - Track marker_found_rate (not just top-1 correct)
   - A/B test chunking strategies on real queries
   - Iterate based on production metrics

---

## 📁 Files Structure

```
report/
├── README.md               (this file - overview)
├── REPORT_CANHAN.md        (individual report - 5 sections)
└── REPORT_NHOM.md          (group report - 4 sections)
```

## ✅ Submission Status

- [x] Both reports complete
- [x] All sections filled with concrete data
- [x] Benchmark results documented
- [x] Key learnings explained
- [x] Recommendations provided

**Ready for submission & demo! 🎓**
