"""Index the images copied into CustomImage by sites_conformes_customimages.0002.

The copy goes through historical models, which don't fire the search signal handlers,
so the admin search only finds the images uploaded or saved since the swap.
"""

from django.db import migrations
from wagtail.images import get_image_model
from wagtail.search.backends import get_search_backend


def index_images(apps, schema_editor):
    # The real model: historical ones don't carry search_fields.
    image_model = get_image_model()
    get_search_backend().add_bulk(image_model, image_model.get_indexed_objects())


class Migration(migrations.Migration):
    dependencies = [
        ("cms_pages", "0004_contentpage_categories_alter_blogentrypage_body_and_more"),
        ("sites_conformes_customimages", "0002_copy_wagtail_images"),
        ("wagtailsearch", "0010_add_text_fields"),
    ]

    operations = [
        migrations.RunPython(index_images, migrations.RunPython.noop),
    ]
