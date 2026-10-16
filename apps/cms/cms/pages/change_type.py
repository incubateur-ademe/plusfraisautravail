"""Change a page's type in place (e.g. blog entry -> content page).

A page is one Page row plus one row in its specific model's table, tied by
``page_ptr`` and ``content_type``. Swapping the specific row keeps the page id,
so its URL, tree position, history, permissions and incoming links survive.
Fields both types share (title, header, body...) and tags are carried over;
the others (blog categories, authors, date...) are dropped.
"""

from django import forms
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, models, transaction
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from wagtail.fields import StreamField
from wagtail.models import Page, ReferenceIndex, Revision, get_page_models
from wagtail.search import index


def _swappable(model) -> bool:
    # ponytail: only models stored right under Page; a deeper concrete chain
    # would need its middle tables swapped too.
    return model._meta.get_parent_list() == [Page]


def target_models(page: Page) -> list[type[Page]]:
    source = page.specific_class
    if not _swappable(source):
        return []
    children = {c.specific_class for c in page.get_children().defer_streamfields()}
    return [
        model
        for model in get_page_models()
        if model is not source
        and _swappable(model)
        and model.is_creatable
        and not (model.max_count and model.objects.count() >= model.max_count)
        and children <= set(model.allowed_subpage_models())
    ]


def lost_fields(source: type[Page], target: type[Page]) -> list[str]:
    kept = {f.name for f in target._meta.get_fields()}
    return [
        str(f.verbose_name)
        for f in source._meta.get_fields()
        if f.concrete and f.model is source and f.name not in kept and f.name != "page_ptr"
    ]


def _delete_specific_row(source: Page) -> None:
    """Delete the specific row and the rows pointing at it, never the Page row.

    Not page.delete() (Wagtail's removes the whole tree node), nor
    Model.delete(keep_parents=True), which still cascades Page's generic
    relations and so wipes the page's revisions and workflow states."""
    model = type(source)
    # Auto-created through tables only: explicit ones (tags, categories) are
    # reverse relations, handled below.
    for field in model._meta.local_many_to_many:
        through = field.remote_field.through
        if not through._meta.auto_created:
            continue
        through._base_manager.filter(**{field.m2m_field_name(): source.pk}).delete()
    for rel in model._meta.related_objects:
        if rel.model is model and not rel.many_to_many:
            if rel.on_delete is not models.CASCADE:
                raise ValueError(f"Des « {rel.related_model._meta.verbose_name} » y sont liés.")
            rel.related_model._base_manager.filter(**{rel.field.name: source.pk}).delete()
    index.remove_object(source)
    ReferenceIndex.remove_for_object(source)
    with connection.cursor() as cursor:
        table = connection.ops.quote_name(model._meta.db_table)
        cursor.execute(f"DELETE FROM {table} WHERE page_ptr_id = %s", [source.pk])


def change_page_type(page: Page, target_model: type[Page], user) -> Page:
    base = Page.objects.get(pk=page.pk)
    source = base.specific
    if base.live and base.has_unpublished_changes:
        raise ValueError("Publiez ou annulez d'abord les modifications en brouillon.")
    if target_model not in target_models(source):
        label = target_model._meta.verbose_name
        raise ValueError(f"Impossible de transformer cette page en « {label} ».")

    target = target_model(
        page_ptr_id=base.pk,
        **{f.attname: getattr(base, f.attname) for f in Page._meta.concrete_fields},
    )
    for field in target_model._meta.concrete_fields:
        if field.model is not target_model or field.name == "page_ptr":
            continue
        try:
            source_field = source._meta.get_field(field.name)
        except models.FieldDoesNotExist:
            continue
        if type(source_field) is not type(field):
            continue
        value = getattr(source, source_field.attname)
        if isinstance(field, StreamField):
            value = source_field.get_prep_value(value)
        setattr(target, field.attname, value)
    tags = list(source.tags.names()) if hasattr(source, "tags") and hasattr(target, "tags") else []

    content_type = ContentType.objects.get_for_model(target_model)
    target.content_type = content_type
    with transaction.atomic():
        _delete_specific_row(source)
        target.save_base(raw=True)
        Page.objects.filter(pk=page.pk).update(content_type=content_type)
        # Old revisions now open as the new type (fields it lacks are ignored).
        Revision.page_revisions.filter(object_id=str(page.pk)).update(content_type=content_type)
        if tags:
            target.tags.set(tags)
        target.save()
        revision = target.save_revision(user=user, log_action=True)
        if base.live:
            revision.publish(user=user)
    return target


class ChangeTypeForm(forms.Form):
    target = forms.ChoiceField(label="Nouveau type")

    def __init__(self, *args, choices, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["target"].choices = choices


def change_type_view(request, page_id):
    page = get_object_or_404(Page, pk=page_id).specific
    if not page.permissions_for_user(request.user).can_publish():
        raise PermissionDenied
    targets = {m._meta.label_lower: m for m in target_models(page)}
    form = ChangeTypeForm(
        request.POST or None,
        choices=[(key, m._meta.verbose_name) for key, m in targets.items()],
    )
    if request.method == "POST" and form.is_valid():
        target_model = targets[form.cleaned_data["target"]]
        try:
            new_page = change_page_type(page, target_model, request.user)
        except (ValueError, ValidationError) as error:
            messages.error(request, " ".join(getattr(error, "messages", [str(error)])))
        else:
            label = target_model._meta.verbose_name
            if not new_page.can_exist_under(new_page.get_parent()):
                messages.warning(
                    request,
                    f"La page est maintenant une « {label} », qui n'a pas sa place ici : "
                    "choisissez où la déplacer.",
                )
                return redirect("wagtailadmin_pages:move", page.pk)
            messages.success(request, f"La page est maintenant une « {label} ».")
            return redirect("wagtailadmin_pages:edit", page.pk)
    return TemplateResponse(
        request,
        "cms_pages/change_type.html",
        {
            "page": page,
            "form": form,
            "lost": {key: lost_fields(page.specific_class, m) for key, m in targets.items()},
            "action_url": reverse("cms_change_page_type", args=[page.pk]),
        },
    )
