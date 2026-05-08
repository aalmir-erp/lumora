from app import kb


def test_default_assemble_includes_company_and_products():
    text = kb.assemble()
    assert "Aalmir Plastic" in text
    assert "HDPE" in text
    assert "FAQ" in text


def test_save_block_overrides_default():
    kb.save_block("company", "Company", "CUSTOMIZED CONTENT XYZ")
    text = kb.assemble()
    assert "CUSTOMIZED CONTENT XYZ" in text


def test_reset_block_restores_default():
    kb.save_block("company", "Company", "TEMP CUSTOM")
    kb.reset_block("company")
    text = kb.assemble()
    assert "TEMP CUSTOM" not in text
    assert "Aalmir Plastic" in text


def test_list_blocks_marks_overrides():
    kb.save_block("products", "Products", "X")
    by_slug = {b["slug"]: b for b in kb.list_blocks()}
    assert by_slug["products"]["overridden"] is True
    assert by_slug["faq"]["overridden"] is False
