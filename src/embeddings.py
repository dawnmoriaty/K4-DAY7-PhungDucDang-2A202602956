from __future__ import annotations

import hashlib
import math
import os

# Multilingual model suitable for the Vietnamese corpora used in this Lab.
# The local backend remains optional; required checkpoints use MockEmbedder.
LOCAL_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_PROVIDER_ENV = "EMBEDDING_PROVIDER"


class MockEmbedder:
    """Deterministic embedding backend used by tests and default classroom runs."""

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim
        self._backend_name = "mock embeddings fallback"

    def __call__(self, text: str) -> list[float]:
        digest = hashlib.md5(text.encode()).hexdigest()
        seed = int(digest, 16)
        vector = []
        for _ in range(self.dim):
            seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
            vector.append((seed / 0xFFFFFFFF) * 2 - 1)
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class SmartMockEmbedder:
    """
    Improved mock embedder with keyword-based similarity.
    Better than pure hash for demo purposes - captures semantic overlap via keywords.
    """
    
    def __init__(self, dim: int = 128) -> None:
        self.dim = dim
        self._backend_name = "smart mock embeddings (keyword-based)"
        
        # Vietnamese stopwords
        self.stopwords = {
            'là', 'của', 'và', 'có', 'được', 'trong', 'cho', 'này', 'với', 
            'không', 'các', 'đã', 'một', 'để', 'tôi', 'bạn', 'trên', 'về',
            'thì', 'sẽ', 'như', 'khi', 'hay', 'nhưng', 'hoặc', 'đến', 'từ'
        }
    
    def _extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from text (simple tokenization)"""
        # Lowercase and split
        text_lower = text.lower()
        
        # Simple word extraction (remove punctuation)
        import re
        words = re.findall(r'\b\w+\b', text_lower)
        
        # Filter stopwords
        keywords = [w for w in words if w not in self.stopwords and len(w) > 2]
        
        return keywords
    
    def __call__(self, text: str) -> list[float]:
        """Generate embedding based on keyword TF-IDF style"""
        keywords = self._extract_keywords(text)
        
        # Create vector based on keyword hashes
        vector = [0.0] * self.dim
        
        if not keywords:
            # Fallback to hash-based if no keywords
            digest = hashlib.md5(text.encode()).hexdigest()
            seed = int(digest, 16)
            for i in range(self.dim):
                seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
                vector[i] = (seed / 0xFFFFFFFF) * 2 - 1
        else:
            # Each keyword contributes to specific dimensions
            for keyword in keywords:
                # Hash keyword to get dimension indices
                kw_hash = hashlib.md5(keyword.encode()).hexdigest()
                kw_seed = int(kw_hash, 16)
                
                # Each keyword affects ~10% of dimensions
                num_dims = max(1, self.dim // 10)
                for _ in range(num_dims):
                    kw_seed = (kw_seed * 1664525 + 1013904223) & 0xFFFFFFFF
                    idx = kw_seed % self.dim
                    # Add contribution (so similar keywords → similar vectors)
                    vector[idx] += 1.0 / len(keywords)
        
        # Normalize
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


class LocalEmbedder:
    """Sentence Transformers-backed local embedder."""

    def __init__(self, model_name: str = LOCAL_EMBEDDING_MODEL) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._backend_name = model_name
        self.model = SentenceTransformer(model_name)

    def __call__(self, text: str) -> list[float]:
        embedding = self.model.encode(text, normalize_embeddings=True)
        if hasattr(embedding, "tolist"):
            return embedding.tolist()
        return [float(value) for value in embedding]


class OpenAIEmbedder:
    """OpenAI embeddings API-backed embedder."""

    def __init__(self, model_name: str = OPENAI_EMBEDDING_MODEL) -> None:
        from openai import OpenAI

        self.model_name = model_name
        self._backend_name = model_name
        self.client = OpenAI()

    def __call__(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=self.model_name, input=text)
        return [float(value) for value in response.data[0].embedding]


class GeminiEmbedder:
    """Google Gemini embeddings API-backed embedder (google-genai SDK).

    Free-tier alternative to OpenAI for students without an OpenAI key —
    a Gemini API key (aistudio.google.com) has a free quota, no billing card needed.
    """

    def __init__(self, model_name: str = GEMINI_EMBEDDING_MODEL) -> None:
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY (or GOOGLE_API_KEY) is required for GeminiEmbedder")
        self.model_name = model_name
        self._backend_name = model_name
        self.client = genai.Client(api_key=api_key)

    def __call__(self, text: str) -> list[float]:
        response = self.client.models.embed_content(model=self.model_name, contents=text)
        return [float(value) for value in response.embeddings[0].values]


_mock_embed = MockEmbedder()
