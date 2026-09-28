"""Wagtail escapes validation error messages (``messages.validation_error``
joins them as plain strings), so ContentPage.clean() can't emit a link.
Turn admin page URLs inside error lists into links client-side instead."""

from django.utils.safestring import mark_safe
from wagtail import hooks

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
