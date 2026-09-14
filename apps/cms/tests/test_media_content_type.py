"""The WebP renditions regression: python:3.12-slim has no mime database and
3.12's built-in table has no .webp, so django-storages uploaded every
rendition as application/octet-stream. cms.settings.base registers the type.
"""

import mimetypes


def test_webp_resolves_to_image_webp():
    # Fails on python 3.12 without the add_type call in cms/settings/base.py.
    assert mimetypes.guess_type("Logo.original.webp")[0] == "image/webp"


def test_other_media_types_still_resolve():
    assert mimetypes.guess_type("a.png")[0] == "image/png"
    assert mimetypes.guess_type("a.jpg")[0] == "image/jpeg"
    assert mimetypes.guess_type("a.svg")[0] == "image/svg+xml"
