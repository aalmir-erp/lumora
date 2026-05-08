from app.persona import (
    ESCALATE_TAG,
    build_system_prompt,
    needs_escalation,
    strip_escalate_tag,
)


def test_system_prompt_includes_identity_and_kb():
    p = build_system_prompt()
    assert "Aalmir Plastic" in p
    assert "Knowledge base" in p
    assert "HARD RULES" in p


def test_escalation_detection():
    assert needs_escalation(f"please wait {ESCALATE_TAG}") is True
    assert needs_escalation("normal reply") is False


def test_strip_escalate_tag_cleans_output():
    assert strip_escalate_tag(f"reply text\n{ESCALATE_TAG}") == "reply text"
