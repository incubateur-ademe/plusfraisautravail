"""wagtail-block-clipboard: what the admin needs to copy and paste blocks."""

import pytest
from wagtail import blocks
from wagtail.admin.telepath import JSContext


class CardBlock(blocks.StructBlock):
    title = blocks.CharBlock()


@pytest.mark.parametrize(
    "block, class_path",
    [
        (blocks.CharBlock(), "wagtail.blocks.field_block.CharBlock"),
        (blocks.StaticBlock(), "wagtail.blocks.static_block.StaticBlock"),
        (CardBlock(), f"{__name__}.CardBlock"),
        (blocks.ListBlock(CardBlock()), "wagtail.blocks.list_block.ListBlock"),
        (blocks.StreamBlock([("card", CardBlock())]), "wagtail.blocks.stream_block.StreamBlock"),
    ],
)
def test_the_admin_receives_the_python_class_of_each_block(block, class_path):
    packed = JSContext().pack(block)

    assert packed["_args"][-1]["blockClass"] == class_path


def test_the_admin_loads_the_clipboard_script_with_its_french_strings(admin_client, settings):
    # The production storage needs collectstatic to have run, which the tests do not do.
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }

    response = admin_client.get("/cms-admin/")

    assert "wagtail_block_clipboard/block-clipboard" in response.text
    # json_script escapes non-ASCII characters, hence the cut before the accent.
    assert "Coller un bloc copi" in response.text
