from django.core.management.base import BaseCommand
from wagtail.fields import RichTextField, StreamField

from sites_conformes_rgaa.emoji_wrapping import (
    unwrap_emojis_in_html,
    unwrap_emojis_in_streamfield_raw_data,
    wrap_emojis_in_html,
    wrap_emojis_in_streamfield_raw_data,
)
from sites_conformes_rgaa.model_fields import iter_model_instances_with_richtext


class Command(BaseCommand):
    help = "Wrap decorative emojis in every RichTextField/StreamField value in accessible markup."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change without saving anything.",
        )
        parser.add_argument(
            "--unwrap",
            action="store_true",
            help="Strip the emoji wrapper spans instead of adding them.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        unwrap = options["unwrap"]
        verb, verb_past = ("unwrap", "Unwrapped") if unwrap else ("wrap", "Wrapped")
        changed_count = 0
        checked_count = 0

        for instance, field_name, field in iter_model_instances_with_richtext():
            checked_count += 1
            changed = self._apply(instance, field_name, field, unwrap)
            if not changed:
                continue

            changed_count += 1
            label = f"{instance._meta.label} #{instance.pk}.{field_name}"
            if dry_run:
                self.stdout.write(f"Would {verb} emojis in {label}")
            else:
                instance.save(update_fields=[field_name])
                self.stdout.write(self.style.SUCCESS(f"{verb_past} emojis in {label}"))

        self.stdout.write(
            f"\nChecked {checked_count} field value(s), "
            f"{'would change' if dry_run else 'changed'} {changed_count}."
        )

    def _apply(self, instance, field_name, field, unwrap: bool) -> bool:
        html_fn = unwrap_emojis_in_html if unwrap else wrap_emojis_in_html
        stream_fn = (
            unwrap_emojis_in_streamfield_raw_data
            if unwrap
            else wrap_emojis_in_streamfield_raw_data
        )
        value = getattr(instance, field_name)
        if isinstance(field, RichTextField):
            new_value, changed = html_fn(str(value) if value else value)
            if changed:
                setattr(instance, field_name, new_value)
            return changed

        if isinstance(field, StreamField):
            raw_data = list(value.raw_data)
            new_raw_data, changed = stream_fn(raw_data)
            if changed:
                setattr(instance, field_name, field.stream_block.to_python(new_raw_data))
            return changed

        return False
