from sites_conformes_rgaa.emoji_wrapping import (
    wrap_emojis_in_html,
    wrap_emojis_in_streamfield_raw_data,
)


def test_wraps_single_emoji_in_paragraph():
    html = "<p>Hello 👋 world</p>"
    new_html, changed = wrap_emojis_in_html(html)
    assert changed is True
    assert (
        '<span aria-hidden="true" class="sites-conformes-rgaa-emoji" role="img">👋</span>'
        in new_html
    )
    assert "Hello" in new_html and "world" in new_html


def test_wraps_multiple_emoji_independently():
    html = "<p>🟡 mid 🔥 end 🎉</p>"
    new_html, changed = wrap_emojis_in_html(html)
    assert changed is True
    assert new_html.count('class="sites-conformes-rgaa-emoji"') == 3


def test_preserves_surrounding_tags_and_attributes():
    html = '<p data-block-key="abc">🟡 Chez <b>Foo</b>, bar</p>'
    new_html, changed = wrap_emojis_in_html(html)
    assert changed is True
    assert 'data-block-key="abc"' in new_html
    assert "<b>Foo</b>" in new_html


def test_no_emoji_is_a_noop():
    html = "<p>No emoji here.</p>"
    new_html, changed = wrap_emojis_in_html(html)
    assert changed is False
    assert new_html == html


def test_empty_and_none_are_noops():
    assert wrap_emojis_in_html("") == ("", False)
    assert wrap_emojis_in_html(None) == (None, False)


def test_idempotent_second_pass_changes_nothing():
    html = "<p>🟡 Chez Foo, bar ⏱️</p>"
    first_html, first_changed = wrap_emojis_in_html(html)
    second_html, second_changed = wrap_emojis_in_html(first_html)
    assert first_changed is True
    assert second_changed is False
    assert second_html == first_html


def test_streamfield_raw_data_wraps_nested_string_values():
    raw_data = [
        {
            "id": "block1",
            "type": "section",
            "value": {"content": [{"id": "c1", "type": "text", "value": "<p>🎉 party</p>"}]},
        },
        {"id": "block2", "type": "paragraph", "value": "no emoji"},
    ]
    new_raw_data, changed = wrap_emojis_in_streamfield_raw_data(raw_data)
    assert changed is True
    assert "sites-conformes-rgaa-emoji" in new_raw_data[0]["value"]["content"][0]["value"]
    assert new_raw_data[1]["value"] == "no emoji"


def test_streamfield_raw_data_does_not_mutate_input():
    raw_data = [{"id": "b", "type": "text", "value": "🎉"}]
    original_value = raw_data[0]["value"]
    wrap_emojis_in_streamfield_raw_data(raw_data)
    assert raw_data[0]["value"] == original_value
