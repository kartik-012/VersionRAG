import re
from typing import List, Dict, Any

class ChunkingService:
    def __init__(self, target_chunk_size: int = 512, chunk_overlap: int = 50):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap

    def approximate_tokens(self, text: str) -> int:
        """Approximate token count (roughly 4 characters per token)."""
        return max(1, len(text) // 4)

    def chunk_document(self, content: str, title: str) -> List[Dict[str, Any]]:
        """
        Structure-aware semantic chunking.
        Splits by markdown headings (H1/H2/H3) or section dividers first,
        then splits large sections into overlapping token windows.
        """
        chunks: List[Dict[str, Any]] = []
        if not content.strip():
            return chunks

        # Split into sections based on headings
        section_pattern = r"(^#{1,3}\s+.+$)"
        splits = re.split(section_pattern, content, flags=re.MULTILINE)
        
        current_section = title
        sections: List[Dict[str, str]] = []

        if len(splits) == 1:
            sections.append({"title": title, "body": content})
        else:
            i = 0
            while i < len(splits):
                segment = splits[i].strip()
                if not segment:
                    i += 1
                    continue
                if segment.startswith("#"):
                    current_section = segment.lstrip("#").strip()
                    i += 1
                    body = splits[i].strip() if i < len(splits) else ""
                    sections.append({"title": current_section, "body": body})
                else:
                    sections.append({"title": current_section, "body": segment})
                i += 1

        chunk_idx = 0
        page_estimate = 1

        for sec in sections:
            sec_title = sec["title"]
            body = sec["body"]
            
            # Estimate pages if "--- Page X ---" markers exist
            page_match = re.search(r"Page\s+(\d+)", body)
            if page_match:
                try:
                    page_estimate = int(page_match.group(1))
                except ValueError:
                    pass

            paragraphs = body.split("\n\n")
            current_buffer: List[str] = []
            current_token_count = 0

            for p in paragraphs:
                p_clean = p.strip()
                if not p_clean:
                    continue
                p_tokens = self.approximate_tokens(p_clean)

                if current_token_count + p_tokens > self.target_chunk_size and current_buffer:
                    chunk_text = "\n\n".join(current_buffer)
                    chunks.append({
                        "chunk_index": chunk_idx,
                        "section_title": sec_title,
                        "page_number": page_estimate,
                        "content": chunk_text,
                        "token_count": current_token_count,
                        "chunk_metadata": {
                            "has_code": "```" in chunk_text,
                            "section": sec_title
                        }
                    })
                    chunk_idx += 1
                    
                    # Retain last paragraph for overlap if possible
                    if len(current_buffer) > 1:
                        last_p = current_buffer[-1]
                        current_buffer = [last_p, p_clean]
                        current_token_count = self.approximate_tokens(last_p) + p_tokens
                    else:
                        current_buffer = [p_clean]
                        current_token_count = p_tokens
                else:
                    current_buffer.append(p_clean)
                    current_token_count += p_tokens

            if current_buffer:
                chunk_text = "\n\n".join(current_buffer)
                chunks.append({
                    "chunk_index": chunk_idx,
                    "section_title": sec_title,
                    "page_number": page_estimate,
                    "content": chunk_text,
                    "token_count": current_token_count,
                    "chunk_metadata": {
                        "has_code": "```" in chunk_text,
                        "section": sec_title
                    }
                })
                chunk_idx += 1

        return chunks

chunking_service = ChunkingService()
