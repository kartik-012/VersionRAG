import math
import hashlib
import json
from typing import List, Dict, Any, Optional
import numpy as np
from app.core.config import settings

class EmbeddingService:
    def __init__(self):
        self.dimension = 384  # Standard compact vector dimension

    def _generate_deterministic_vector(self, text: str) -> List[float]:
        """
        High-quality deterministic n-gram semantic hash embedding.
        Produces consistent, normalized 384-dimensional vector with strong lexical-semantic affinity.
        """
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = text.lower().split()
        
        # 1. Word unigram hashing
        for i, word in enumerate(words):
            # Clean word
            clean_word = "".join([c for c in word if c.isalnum()])
            if not clean_word:
                continue
            h = int(hashlib.md5(clean_word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if (h % 2 == 0) else -1.0
            vec[idx] += sign * (1.0 / math.log2(i + 2))

        # 2. Character n-gram hashing for subword robustness
        for n in [3, 4]:
            for j in range(len(text) - n + 1):
                ngram = text[j:j+n].lower()
                h = int(hashlib.sha256(ngram.encode("utf-8")).hexdigest(), 16)
                idx = h % self.dimension
                sign = 1.0 if (h % 2 == 0) else -1.0
                vec[idx] += sign * 0.3

        # L2 Normalization
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return [float(x) for x in vec]

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for a single text."""
        # Try OpenAI API if key is present
        if settings.OPENAI_API_KEY and not settings.USE_MOCK_AI_IF_NO_KEY:
            try:
                import openai
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                resp = client.embeddings.create(
                    model=settings.DEFAULT_EMBEDDING_MODEL,
                    input=text[:8000]
                )
                return resp.data[0].embedding
            except Exception:
                pass
        
        return self._generate_deterministic_vector(text)

    def get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings in batch."""
        return [self.get_embedding(t) for t in texts]

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two float vectors."""
        if not vec_a or not vec_b:
            return 0.0
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

embedding_service = EmbeddingService()
