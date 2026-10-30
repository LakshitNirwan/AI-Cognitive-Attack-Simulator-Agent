from datasets.audit.verify_slabs_pinned_upstream import (
    audit_csv_bytes,
    compare_pinned_source,
)


def test_identical_bytes_with_conflicting_labels_still_block():
    payload = b"text,label\nsame prompt,0\nsame prompt,1\n"
    result = compare_pinned_source(payload, payload)
    assert result["byte_identical"] is True
    assert result["status"] == "PINNED_SOURCE_HAS_CONFLICTS"
    assert result["training_eligible"] is False


def test_different_bytes_are_not_misreported_as_verified():
    local = b"text,label\nbenign query,0\n"
    upstream = b"text,label\nbenign query,0\nanother query,0\n"
    result = compare_pinned_source(local, upstream)
    assert result["byte_identical"] is False
    assert result["status"] == "PINNED_SOURCE_BYTES_DIFFER"
    assert result["training_eligible"] is False


def test_conflict_audit_returns_fingerprint_not_source_text():
    result = audit_csv_bytes(b"text,label\nsame prompt,0\nsame prompt,1\n")
    assert result["conflicting_normalized_text_count"] == 1
    assert "same prompt" not in str(result["conflicts"])
