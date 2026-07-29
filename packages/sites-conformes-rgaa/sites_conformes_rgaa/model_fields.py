"""Generic discovery of RichTextField and StreamField fields across every
installed Django model - so wrap_emojis works on any sites-conformes site
without needing to hardcode which page types or settings models carry rich
text, and keeps working as upstream adds new block types or page models.
"""

from django.apps import apps
from django.db import models
from wagtail.fields import RichTextField, StreamField


def iter_richtext_and_streamfields():
    """Yield (model, field_name, field) for every concrete RichTextField or
    StreamField on every installed model."""
    for model in apps.get_models():
        for field in model._meta.concrete_fields:
            if isinstance(field, (RichTextField, StreamField)):
                yield model, field.name, field


def iter_model_instances_with_richtext():
    """Yield (instance, field_name, field) for every saved row that has a
    non-empty RichTextField or StreamField value."""
    seen_models = set()
    for model, field_name, field in iter_richtext_and_streamfields():
        if (model, field_name) in seen_models:
            continue
        seen_models.add((model, field_name))
        queryset = model._default_manager.all()
        if isinstance(field, models.TextField):
            queryset = queryset.exclude(**{f"{field_name}": ""}).exclude(
                **{f"{field_name}__isnull": True}
            )
        for instance in queryset.iterator():
            yield instance, field_name, field
