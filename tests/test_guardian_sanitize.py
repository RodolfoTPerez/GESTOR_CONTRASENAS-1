from src.infrastructure.guardian_ai import GuardianAI


def test_sanitize_removes_sensitive_fields():
    ai = GuardianAI()
    # Build a fake report that contains potentially sensitive fields
    report = {
        "score": 42,
        "status": "Riesgoso",
        "stats": {"total": 2, "reused": 1, "weak": 1},
        "findings": [
            {"type": "danger", "title": "Clave Débil", "desc": "pwd123", "secret": "pwd123"},
            {"type": "warning", "title": "Reutilizada", "desc": "Usada en A,B", "secret": "pwd123"}
        ]
    }

    safe = ai.sanitize_report_for_ai(report)

    # Check top-level fields preserved
    assert safe["score"] == 42
    assert safe["status"] == "Riesgoso"
    assert "stats" in safe

    # Findings preserved but no 'secret' field
    assert len(safe["findings"]) == 2
    for f in safe["findings"]:
        assert "secret" not in f
        assert "title" in f and "desc" in f
