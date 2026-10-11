"""
Multi-Tier Semantic Embedding Service for VersionRAG.

Supports 3 tiers of dense vector generation:
- Tier 1: Google Gemini API (`text-embedding-004`) when GEMINI_API_KEY is configured.
- Tier 2: OpenAI API (`text-embedding-3-small`) when OPENAI_API_KEY is configured.
- Tier 3: Local Semantic Software-Engineering Ontology + Subword Distributional Embedding
          (maps synonyms like 'retired/obsolete' -> 'deprecated', 'coercive/loose' -> '==',
           'subset/partial' -> 'partialDeepStrictEqual', etc. into shared latent dimensions).
Includes an in-memory SHA-256 LRU cache for zero-latency repeated lookups.
"""

import math
import hashlib
import re
from collections import OrderedDict
from typing import List, Dict, Set, Optional
import httpx
import numpy as np
from app.core.config import settings


# Software Engineering & API Evolution Semantic Concept Clusters
# Each cluster maps semantically equivalent developer terminology to shared latent dimensions.
SEMANTIC_CONCEPT_CLUSTERS: Dict[str, List[str]] = {
    "CONCEPT_DEPRECATION": [
        "deprecate", "deprecated", "deprecation", "obsolete", "retired",
        "phased out", "legacy", "scheduled for removal", "discontinued", "end of life", "eol"
    ],
    "CONCEPT_REMOVAL": [
        "remove", "removed", "removal", "deleted", "dropped", "eliminated",
        "no longer supported", "purged", "stripped"
    ],
    "CONCEPT_BREAKING_CHANGE": [
        "breaking", "breaking change", "incompatible", "incompatibility",
        "migration", "upgrade risk", "regression", "crash", "throws", "fatal"
    ],
    "CONCEPT_SILENT_CHANGE": [
        "silent", "silent change", "undocumented", "implicit", "unlisted",
        "hidden change", "without being mentioned", "omitted from changelog"
    ],
    "CONCEPT_STRICT_EQUALITY": [
        "strict", "deepstrictequal", "object.is", "=== ", "triple equals",
        "identity comparison", "no type coercion", "strictly equal"
    ],
    "CONCEPT_LOOSE_COERCION": [
        "deepequal", "loose", "coercive", "coercion", "==", "double equals",
        "abstract equality", "legacy comparison"
    ],
    "CONCEPT_PROTOTYPE_CHECK": [
        "prototype", "__proto__", "constructor", "instanceof", "class hierarchy",
        "object prototype", "inheritance", "structural prototype"
    ],
    "CONCEPT_SUBSET_PARTIAL": [
        "partial", "partialdeepstrictequal", "subset", "sub-object",
        "partial match", "contains properties", "subset validation"
    ],
    "CONCEPT_CALL_TRACKING": [
        "calltracker", "tracker", "calls", "verify", "mock", "spy",
        "invocation count", "call count", "expected calls"
    ],
    "CONCEPT_REGEX_MATCH": [
        "match", "doesnotmatch", "regexp", "regular expression", "pattern",
        "string matching", "regex"
    ],
    "CONCEPT_ASYNC_REJECTION": [
        "rejects", "doesnotreject", "async", "await", "promise",
        "asynchronous", "promise rejection", "unhandled rejection"
    ],
    "CONCEPT_EXCEPTION_ERROR": [
        "throws", "doesnothrow", "assertionerror", "typeerror", "error",
        "exception", "stack trace", "error message", "ERR_ASSERTION"
    ],
    "CONCEPT_HTTP_SERVER": [
        "createserver", "listen", "closeallconnections", "http", "socket",
        "connection", "port", "host", "terminate", "shutdown"
    ],
    "CONCEPT_INTRODUCED_ADDED": [
        "added", "introduced", "new feature", "newly added", "created",
        "launched", "initial release", "supported since"
    ],
    "CONCEPT_EXPERIMENTAL_STABILITY": [
        "experimental", "stability", "stable", "release candidate", "rc",
        "beta", "alpha", "production ready", "maturity"
    ],
}


class EmbeddingService:
    def __init__(self, dimension: int = 384, max_cache_size: int = 2048):
        self.dimension = dimension
        self._max_cache_size = max_cache_size
        self._cache: OrderedDict[str, List[float]] = OrderedDict()

    @staticmethod
    def expand_semantic_concepts(text: str) -> Set[str]:
        """
        Identifies which canonical Software Engineering semantic concepts are active in `text`.
        Used by both dense vector projection and Cross-Encoder reranking.
        """
        if not text:
            return set()
        t_lower = text.lower()
        active_concepts: Set[str] = set()
        for concept_id, phrases in SEMANTIC_CONCEPT_CLUSTERS.items():
            for phrase in phrases:
                if phrase in t_lower:
                    active_concepts.add(concept_id)
                    break
        return active_concepts

    def _project_to_dimension(self, raw_vec: List[float]) -> List[float]:
        """Projects or pools an external API embedding (e.g. 768d or 1536d) into `self.dimension`."""
        arr = np.asarray(raw_vec, dtype=np.float32)
        src_dim = arr.shape[0]
        if src_dim == self.dimension:
            norm = np.linalg.norm(arr)
            return [float(x) for x in (arr / norm if norm > 0 else arr)]

        # Deterministic folding / average pooling into target dimension
        projected = np.zeros(self.dimension, dtype=np.float32)
        for i in range(src_dim):
            projected[i % self.dimension] += arr[i]
        norm = np.linalg.norm(projected)
        if norm > 0:
            projected = projected / norm
        return [float(x) for x in projected]

    def _generate_semantic_ontology_vector(self, text: str) -> List[float]:
        """
        Tier-3 Local Semantic Ontology + Distributional Subword Vectorizer.
        Combines:
        1. Canonical Concept Cluster projection (high weight for synonym invariance)
        2. Code-aware identifier & camelCase sub-token projection
        3. Positional unigram & bigram semantic hashing
        4. Character 3/4-gram morphological robustness
        """
        vec = np.zeros(self.dimension, dtype=np.float32)
        if not text:
            return [0.0] * self.dimension

        t_lower = text.lower()

        # 1. Semantic Ontology Concept Activation (Strongest signal for synonym matching)
        active_concepts = self.expand_semantic_concepts(t_lower)
        for concept_id in active_concepts:
            # Project each concept across 6 dedicated orthogonal basis slots
            for slot in range(6):
                seed = f"{concept_id}::slot_{slot}".encode("utf-8")
                h = int(hashlib.sha256(seed).hexdigest(), 16)
                idx = h % self.dimension
                sign = 1.0 if ((h >> 8) % 2 == 0) else -1.0
                vec[idx] += sign * 2.2

        # 2. CamelCase-aware word & bigram projection
        # Split camelCase so `deepStrictEqual` activates `deep`, `strict`, `equal`
        camel_expanded = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text).lower()
        words = [w for w in re.findall(r"[a-z0-9_]+", camel_expanded) if len(w) > 1]

        for i, word in enumerate(words):
            pos_weight = 1.0 / math.log2(i + 2.5)
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx1 = h % self.dimension
            idx2 = (h >> 16) % self.dimension
            sign1 = 1.0 if (h % 2 == 0) else -1.0
            sign2 = 1.0 if ((h >> 4) % 2 == 0) else -1.0
            vec[idx1] += sign1 * (1.2 * pos_weight)
            vec[idx2] += sign2 * (0.8 * pos_weight)

            # Word bigram for phrase order sensitivity
            if i + 1 < len(words):
                bigram = f"{word}_{words[i + 1]}"
                hb = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16)
                vec[hb % self.dimension] += (1.0 if (hb % 2 == 0) else -1.0) * 0.65

        # 3. Character n-gram hashing for subword & typo resilience
        compact = re.sub(r"\s+", " ", t_lower)[:2000]
        for n in (3, 4):
            for j in range(len(compact) - n + 1):
                ngram = compact[j : j + n]
                h = int(hashlib.sha256(ngram.encode("utf-8")).hexdigest(), 16)
                idx = h % self.dimension
                sign = 1.0 if (h % 2 == 0) else -1.0
                vec[idx] += sign * 0.22

        # L2 Normalization
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return [float(x) for x in vec]

    def get_embedding(self, text: str) -> List[float]:
        """Generate normalized embedding vector with multi-tier provider fallback and LRU caching."""
        if not text:
            return [0.0] * self.dimension

        cache_key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

        result_vec: Optional[List[float]] = None

        # Tier 1: Google Gemini Embedding API (`text-embedding-004`)
        if settings.GEMINI_API_KEY and not settings.USE_MOCK_AI_IF_NO_KEY:
            try:
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"text-embedding-004:embedContent?key={settings.GEMINI_API_KEY}"
                )
                payload = {
                    "model": "models/text-embedding-004",
                    "content": {"parts": [{"text": text[:8000]}]},
                }
                with httpx.Client(timeout=6.0) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        raw_values = resp.json().get("embedding", {}).get("values")
                        if raw_values:
                            result_vec = self._project_to_dimension(raw_values)
            except Exception:
                pass

        # Tier 2: OpenAI Embedding API (`text-embedding-3-small`)
        if result_vec is None and settings.OPENAI_API_KEY and not settings.USE_MOCK_AI_IF_NO_KEY:
            try:
                import openai
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                resp = client.embeddings.create(
                    model=settings.DEFAULT_EMBEDDING_MODEL,
                    input=text[:8000],
                )
                result_vec = self._project_to_dimension(resp.data[0].embedding)
            except Exception:
                pass

        # Tier 3: Local Semantic Ontology + Distributional Subword Vectorizer
        if result_vec is None:
            result_vec = self._generate_semantic_ontology_vector(text)

        # Store in bounded LRU cache
        self._cache[cache_key] = result_vec
        if len(self._cache) > self._max_cache_size:
            self._cache.popitem(last=False)

        return result_vec

    def get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings in batch."""
        return [self.get_embedding(t) for t in texts]

    @property
    def provider_name(self) -> str:
        """Return active embedding tier identifier for telemetry."""
        if settings.GEMINI_API_KEY and not settings.USE_MOCK_AI_IF_NO_KEY:
            return "gemini-text-embedding-004"
        if settings.OPENAI_API_KEY and not settings.USE_MOCK_AI_IF_NO_KEY:
            return settings.DEFAULT_EMBEDDING_MODEL
        return "local-semantic-ontology-256d"

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two float vectors."""
        if not vec_a or not vec_b:
            return 0.0
        a = np.asarray(vec_a, dtype=np.float32)
        b = np.asarray(vec_b, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))


embedding_service = EmbeddingService()

