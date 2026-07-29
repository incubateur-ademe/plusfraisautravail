"""Wrap decorative emoji in accessible markup, per the DSFR/RGAA pattern:
<span role="img" aria-hidden="true">emoji</span> so screen readers skip them
while sighted users still see the emoji.
"""

import emoji
from bs4 import BeautifulSoup, NavigableString

WRAPPER_CLASS = "sites-conformes-rgaa-emoji"


def _wrap_text_node(soup: BeautifulSoup, text_node: NavigableString) -> bool:
    """Replace a text node with a mix of text and emoji spans, in place.

    Returns True if the node contained at least one emoji (and was replaced).
    """
    matches = emoji.emoji_list(str(text_node))
    if not matches:
        return False

    text = str(text_node)
    new_nodes = []
    cursor = 0
    for match in matches:
        start, end = match["match_start"], match["match_end"]
        if start > cursor:
            new_nodes.append(NavigableString(text[cursor:start]))
        span = soup.new_tag("span", attrs={"role": "img", "aria-hidden": "true"})
        span["class"] = WRAPPER_CLASS
        span.string = text[start:end]
        new_nodes.append(span)
        cursor = end
    if cursor < len(text):
        new_nodes.append(NavigableString(text[cursor:]))

    text_node.replace_with(*new_nodes)
    return True


def wrap_emojis_in_html(html: str) -> tuple[str, bool]:
    """Wrap every decorative emoji found in `html`'s text nodes.

    Returns (new_html, changed). Idempotent: text nodes already inside a
    WRAPPER_CLASS span are left alone, so re-running on already-wrapped
    content is a no-op.
    """
    if not html or not emoji.emoji_count(html):
        return html, False

    soup = BeautifulSoup(html, "html.parser")
    changed = False

    for text_node in soup.find_all(string=True):
        parent_classes = text_node.parent.get("class") or []
        if WRAPPER_CLASS in parent_classes:
            continue
        if _wrap_text_node(soup, text_node):
            changed = True

    if not changed:
        return html, False
    return str(soup), True


def wrap_emojis_in_streamfield_raw_data(raw_data: list) -> tuple[list, bool]:
    """Recursively wrap emojis in every string value of a StreamField's raw
    (pre-serialization) data - the list-of-dicts shape returned by
    `StreamValue.raw_data`, covering arbitrarily nested stream/struct/list
    blocks without needing to know each block type in advance.

    Returns (new_raw_data, changed). Does not mutate the input.
    """
    new_data, changed = _wrap_emojis_in_value(raw_data)
    return new_data, changed


def _wrap_emojis_in_value(value):
    if isinstance(value, str):
        return wrap_emojis_in_html(value)
    if isinstance(value, dict):
        changed = False
        new_dict = {}
        for key, sub_value in value.items():
            new_sub_value, sub_changed = _wrap_emojis_in_value(sub_value)
            new_dict[key] = new_sub_value
            changed = changed or sub_changed
        return new_dict, changed
    if isinstance(value, list):
        changed = False
        new_list = []
        for item in value:
            new_item, item_changed = _wrap_emojis_in_value(item)
            new_list.append(new_item)
            changed = changed or item_changed
        return new_list, changed
    return value, False
