"""Wagtail escapes validation error messages (``messages.validation_error``
joins them as plain strings), so ContentPage.clean() can't emit a link.
Turn admin page URLs inside error lists into links client-side instead."""

from django.http import Http404
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from wagtail import hooks
from wagtail.admin.widgets import Button

from cms.pages.change_type import change_type_view, target_models
from cms.pages.models import TagSettings

LINKIFY_ERRORLIST_URLS = mark_safe(r"""<script>
document.addEventListener("DOMContentLoaded", () => {
  for (const li of document.querySelectorAll(".messages .errorlist li")) {
    li.innerHTML = li.innerHTML.replace(/(\/[\w-]+\/pages\/\d+\/edit\/)/g, '<a href="$1">$1</a>');
  }
});
</script>""")


@hooks.register("insert_global_admin_js")
def linkify_errorlist_urls():
    return LINKIFY_ERRORLIST_URLS


@hooks.register("register_admin_urls")
def change_page_type_urls():
    return [
        path("pages/<int:page_id>/changer-type/", change_type_view, name="cms_change_page_type")
    ]


@hooks.register("register_page_header_buttons")
def change_page_type_button(page, user, view_name, next_url=None):
    if page.permissions_for_user(user).can_publish() and target_models(page):
        yield Button(
            "Changer le type",
            reverse("cms_change_page_type", args=[page.pk]),
            icon_name="doc-empty-inverse",
            priority=25,
        )


@hooks.register("before_serve_page")
def hide_tag_list_subpages(page, request, args, kwargs):
    """The ``tags/`` route of the blog and catalog pages; cms/urls.py covers the global ones."""
    match = getattr(request, "routable_resolver_match", None)
    if match and match.url_name == "tags_list" and not TagSettings.links_on(request):
        raise Http404
