from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        # TODO: store references to store and llm_fn
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # TODO: retrieve chunks, build prompt, call llm_fn
        
        # 1. Truy xuất top-k chunks
        results = self.store.search(question, top_k=top_k)
        
        # 2. Nếu store rỗng → không gọi LLM
        if not results:
            return "Xin lỗi, tôi không tìm thấy thông tin liên quan trong cơ sở dữ liệu."
        
        # 3. Xây dựng ngữ cảnh - ĐÁNHsố chunks để truy vết được
        context_parts = []
        for i, result in enumerate(results, 1):
            source = result.get('metadata', {}).get('source_url', 'Unknown source')
            context_parts.append(f"[{i}] {result['content']}\n(Nguồn: {source})")
        
        context = "\n\n".join(context_parts)
        
        # 4. Xây dựng prompt (yêu cầu model tham chiếu [1], [2], [3])
        prompt = f"""Dựa trên ngữ cảnh dưới đây, hãy trả lời câu hỏi một cách chính xác.
Chỉ sử dụng thông tin từ ngữ cảnh được cung cấp.
Nếu không tìm thấy thông tin để trả lời, hãy nói rõ là không tìm được.
Khi trích dẫn, hãy tham chiếu đến số [1], [2], [3] của chunks.

NGỮA CẢNH:
{context}

CÂU HỎI: {question}

TRẢLỜI:"""
        
        # 5. Gọi LLM để sinh câu trả lời
        answer = self.llm_fn(prompt)
        
        return answer
