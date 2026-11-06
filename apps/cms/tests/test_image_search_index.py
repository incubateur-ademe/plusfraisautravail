"""Images copied without going through the search signals are found again once the
cms_pages migration has indexed them."""

from importlib import import_module

import pytest
from wagtail.images import get_image_model
from wagtail.models import Collection
from wagtail.search.backends import get_search_backend

pytestmark = pytest.mark.django_db


def test_copied_images_are_found_by_the_admin_search():
    image_model = get_image_model()
    collection = Collection.get_first_root_node()
    # bulk_create skips the signals, like the historical models of the copy.
    image_model.objects.bulk_create(
        image_model(
            title=f"Canicule {i}",
            file="original_images/canicule.png",
            width=1,
            height=1,
            collection=collection,
        )
        for i in range(31)
    )
    backend = get_search_backend()
    assert backend.autocomplete("canicule", image_model).count() == 0

    import_module("cms.pages.migrations.0005_index_copied_images").index_images(None, None)

    assert backend.autocomplete("canicule", image_model).count() == 31
