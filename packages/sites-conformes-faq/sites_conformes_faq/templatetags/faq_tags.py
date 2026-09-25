import re

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Wagtail renders page links relative, so an absolute http(s) href is external.
# ponytail: regex over rendered HTML; swap for a rich text link handler if
# more attributes ever need per-link logic.
_EXTERNAL_A = re.compile(r'<a (?=[^>]*href="https?://)(?![^>]*\btarget=)')


@register.filter
def external_links_blank(html):
    """Open external links of rendered rich text in a new tab."""
    return mark_safe(_EXTERNAL_A.sub('<a target="_blank" rel="noopener external" ', str(html)))
