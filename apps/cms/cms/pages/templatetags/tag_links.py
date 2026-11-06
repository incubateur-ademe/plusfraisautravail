from django import template
from sites_conformes.blog.models import BlogIndexPage
from sites_conformes.core.models import CatalogIndexPage

from cms.pages.models import TagSettings

register = template.Library()


# ponytail: without a request (``{{ page.body }}``, on the listing pages) every tag runs its own
# SELECT: one query per tag block, on these pages only. No process-wide cache to lift it, the
# gunicorn workers would serve a stale value: render with {% include_block page.body %} instead.


@register.simple_tag(takes_context=True)
def tag_links_enabled(context):
    return TagSettings.links_on(context.get("request"))


@register.simple_tag(takes_context=True)
def breadcrumb_links(context):
    """The trail of a filtered listing, without its link to the tag list once that list is down.
    The URL is the one sites-conformes builds: a page may itself have the slug ``tags``."""
    links = context["extra_breadcrumbs"]["links"]
    page = context.get("page")
    if TagSettings.links_on(context.get("request")) or not isinstance(
        page, BlogIndexPage | CatalogIndexPage
    ):
        return links
    tag_list = f"{page.get_url()}{page.reverse_subpage('tags_list')}"
    return [link for link in links if link["url"] != tag_list]
