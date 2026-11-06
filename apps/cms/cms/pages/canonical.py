"""Replaces sites-conformes' {% canonical_url %}, which appends every port but 80 to the host.

Builds on Site.root_url instead, like the sitemap. Our Site record has to stay on 443: Wagtail
derives the scheme of root_url from it, so moving it to 80 would turn every URL to http://.
Remove once sites-conformes treats 443 as a default port too.
"""

from sites_conformes.core.templatetags.wagtail_dsfr_tags import register
from wagtail.models import Site


@register.simple_tag(takes_context=True)
def canonical_url(context):
    request = context.get("request")
    if not request:
        # The 500 page renders without a request.
        return ""

    return f"{Site.find_for_request(request).root_url}{request.path}"
