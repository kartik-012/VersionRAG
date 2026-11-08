import json
from app.services.chunking_service import chunking_service
from app.services.parser_service import parser_service
from app.services.diff_service import diff_service
from app.models.change import ChangeType


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


def test_openapi_json_upload_normalization_to_ast_diff():
    openapi_v1 = {
        "openapi": "3.0.3",
        "info": {
            "title": "Stripe Billing API",
            "version": "1.0.0",
            "description": "Core payment processing endpoints.",
        },
        "paths": {
            "/v1/payments/charge": {
                "post": {
                    "summary": "Create a payment charge",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["amount", "currency"],
                                    "properties": {
                                        "amount": {"type": "integer", "description": "Amount in cents"},
                                        "currency": {"type": "string", "description": "ISO currency code"},
                                        "idempotency_key": {"type": "string", "description": "Optional retry key"},
                                    },
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Charge created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ChargeObject"}
                                }
                            },
                        },
                        "400": {"description": "Invalid payment parameters"},
                    },
                }
            },
            "/v1/payments/legacy-token": {
                "get": {
                    "summary": "Retrieve legacy card token",
                    "responses": {"200": {"description": "LegacyToken"}},
                }
            },
        },
    }

    openapi_v2 = {
        "openapi": "3.0.3",
        "info": {
            "title": "Stripe Billing API",
            "version": "2.0.0",
            "description": "Core payment processing endpoints v2.",
        },
        "paths": {
            "/v1/payments/charge": {
                "post": {
                    "summary": "Create a payment charge",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["amount", "currency", "idempotency_key"],
                                    "properties": {
                                        "amount": {"type": "integer", "description": "Amount in cents"},
                                        "currency": {"type": "string", "description": "ISO currency code"},
                                        "idempotency_key": {"type": "string", "description": "Mandatory retry key in v2"},
                                    },
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Charge created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/PaymentReceipt"}
                                }
                            },
                        },
                        "400": {"description": "Invalid payment parameters"},
                        "422": {"description": "Missing required idempotency_key"},
                    },
                }
            }
        },
    }

    md_v1 = parser_service.extract_text_from_file(json.dumps(openapi_v1).encode("utf-8"), "openapi_spec.json")
    md_v2 = parser_service.extract_text_from_file(json.dumps(openapi_v2).encode("utf-8"), "openapi_spec.json")

    assert "## POST /v1/payments/charge" in md_v1
    assert "- `idempotency_key` (string, optional)" in md_v1
    assert "- `idempotency_key` (string, required)" in md_v2
    assert "- 200: `PaymentReceipt`" in md_v2

    meta_v2 = parser_service.extract_metadata_and_version(md_v2, "openapi_spec.json")
    assert meta_v2["version_tag"] == "v2.0.0"
    assert "Stripe Billing API" in meta_v2["doc_family"]

    chunks_v2 = chunking_service.chunk_document(md_v2, meta_v2["title"])
    assert any("POST /v1/payments/charge" in c["section_title"] for c in chunks_v2)

    changes, summary = diff_service.compute_all_changes(md_v1, md_v2, "v1.0.0", "v2.0.0")
    assert summary["breaking"] >= 1
    assert summary["removed"] >= 1
    charge_breaks = [
        c for c in changes
        if "POST /v1/payments/charge" in c["location"] and c["change_type"] == ChangeType.BREAKING
    ]
    assert len(charge_breaks) == 1
    assert "idempotency_key" in charge_breaks[0]["summary"]
    assert "HTTP_422" in charge_breaks[0]["summary"]


def test_chunking_sanitization_and_null_byte_filtering():
    raw_content = "# Module Alpha\x00\n\nThis is content with a \x00null byte and whitespace.\n\n"
    chunks = chunking_service.chunk_document(raw_content, "Alpha Spec")
    assert len(chunks) == 1
    assert "\x00" not in chunks[0]["content"]
    assert "null byte and whitespace." in chunks[0]["content"]
    assert chunks[0]["token_count"] >= 1


def test_parser_service_sanitize_extracted_text():
    dirty_text = "Line 1\r\nLine 2\x00\r\n\n\n\n\nLine 3\r\n"
    cleaned = parser_service.sanitize_extracted_text(dirty_text)
    assert "\x00" not in cleaned
    assert "\r" not in cleaned
    assert "\n\n\n\n" not in cleaned
    assert "Line 1\nLine 2\n\n\nLine 3" == cleaned


