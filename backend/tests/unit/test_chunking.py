from app.services.chunking_service import chunking_service

def test_structure_aware_chunking():
    doc_text = """# Title of Doc

## Section 1: Introduction
This is the introduction paragraph explaining the API.

## Section 2: Functions
### assert.deepEqual()
Here is how deepEqual works.
```javascript
assert.deepEqual({a: 1}, {a: 1});
```

### assert.equal()
Here is how shallow equal works.
"""
    chunks = chunking_service.chunk_document(doc_text, "Title of Doc")
    assert len(chunks) >= 2
    section_titles = [c["section_title"] for c in chunks]
    assert any("Functions" in s or "assert.deepEqual()" in s for s in section_titles)
    # Check metadata
    assert any(c["chunk_metadata"]["has_code"] for c in chunks)
