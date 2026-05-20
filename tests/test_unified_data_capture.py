from app.services.unified_data_capture import classify_input, detect_language, extract_entities


def test_arabic_operational_update_extracts_entities_and_classifies_issue():
    text = "القاعة 5 اليوم سحبت 6 طن علف وبقى بالسايلو 800 كيلو والإنتاج نازل"

    entities = extract_entities(text)
    classification = classify_input(
        text=text,
        entities=entities,
        submitted_category="daily_update",
        submitted_priority="normal",
    )

    assert detect_language(text) == "ar"
    assert entities[0]["entity_type"] == "hall"
    assert entities[0]["entity_value"] == "5"
    assert any(entity["entity_type"] == "quantity" and entity["entity_value"] == "6 طن" for entity in entities)
    assert any(entity["entity_type"] == "quantity" and entity["entity_value"] == "800 كيلو" for entity in entities)
    assert any(entity["entity_type"] == "date" and entity["entity_value"] == "today" for entity in entities)
    assert classification["inferred_department"] == "production"
    assert classification["category"] == "issue"
    assert classification["operational_signal"] == "risk"
    assert classification["priority"] == "watch"
    assert "warehouse" in classification["related_departments"]
