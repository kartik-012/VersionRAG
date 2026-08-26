from app.services.diff_service import diff_service
from app.models.change import ChangeType, ChangeSeverity

def test_explicit_changelog_extraction():
    content = """# Release Notes
## Changelog
- **[Breaking]**: Removed assert.CallTracker
- **[Added]**: Introduced partialDeepStrictEqual
- **[Deprecated]**: Legacy formatting is deprecated
"""
    changes = diff_service.extract_explicit_changelog(content)
    assert len(changes) == 3
    types = [c["change_type"] for c in changes]
    assert ChangeType.BREAKING in types
    assert ChangeType.ADDED in types
    assert ChangeType.DEPRECATED in types

def test_implicit_silent_change_detection():
    old_doc = """# API Doc
## Features
### Function A
This function returns 42.

### Legacy Support
Legacy formatting is active.
"""
    new_doc = """# API Doc
## Features
### Function A
This function throws an error if input is invalid.

### Function B
New function added here.
"""
    # Legacy Support was silently removed, Function A behavior was modified
    changes, summary = diff_service.compute_all_changes(old_doc, new_doc, "v1.0", "v2.0")
    assert summary["total"] >= 2
    assert summary["breaking"] >= 1 or summary["removed"] >= 1
    assert any(c.get("is_silent") for c in changes)
