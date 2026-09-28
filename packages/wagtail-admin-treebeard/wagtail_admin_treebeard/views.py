from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views import View
from treebeard.exceptions import InvalidMoveToDescendant
from wagtail.admin.auth import permission_denied
from wagtail.snippets.views.snippets import IndexView, SnippetViewSet

from wagtail_admin_treebeard.forms import INVALID_MOVE_MESSAGE


class TreeIndexView(IndexView):
    """Lists the nodes as a nested tree with drag and drop.

    Searching, filtering or sorting a column falls back to Wagtail's flat table.
    """

    move_url_name = None
    node_template_name = "wagtail_admin_treebeard/node.html"

    @cached_property
    def is_tree_mode(self):
        return not (self.is_searching or self.is_filtering or self.is_explicitly_ordered)

    def get_paginate_by(self, queryset):
        return None if self.is_tree_mode else super().get_paginate_by(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.is_tree_mode:
            roots = self.model.get_root_nodes()
            if getattr(self, "locale", None):
                roots = roots.filter(locale=self.locale)
            context.update(
                tree_roots=roots,
                move_url=reverse(self.move_url_name),
                node_template_name=self.node_template_name,
            )
        return context


class TreeMoveView(View):
    """Re-parents a node.

    POST ``node`` and ``target`` (both pks) to nest ``node`` under ``target``,
    or ``node`` alone to bring it back to the root.
    """

    model = None
    permission_policy = None

    def post(self, request):
        if not self.permission_policy.user_has_permission(request.user, "change"):
            return permission_denied(request)
        node = self.get_node(request.POST.get("node"))
        target_pk = request.POST.get("target")
        is_sorted = bool(self.model.node_order_by)
        try:
            if target_pk:
                target = self.get_node(target_pk)
                node.move(target, pos="sorted-child" if is_sorted else "last-child")
                messages.success(
                    request,
                    _("“%(node)s” moved under “%(target)s”.") % {"node": node, "target": target},
                )
            elif not node.is_root():
                first_root = self.model.get_first_root_node()
                node.move(first_root, pos="sorted-sibling" if is_sorted else "last-sibling")
                messages.success(request, _("“%(node)s” moved to the root.") % {"node": node})
        except InvalidMoveToDescendant:
            messages.error(request, INVALID_MOVE_MESSAGE)
            return HttpResponseBadRequest(INVALID_MOVE_MESSAGE)
        return JsonResponse({"ok": True})

    def get_node(self, pk):
        try:
            return get_object_or_404(self.model, pk=pk)
        except (ValueError, ValidationError):
            raise Http404 from None


class TreeSnippetViewSet(SnippetViewSet):
    """A SnippetViewSet for a django-treebeard model (AL, MP or NS)."""

    index_view_class = TreeIndexView
    move_view_class = TreeMoveView
    index_template_name = "wagtail_admin_treebeard/index.html"
    index_results_template_name = "wagtail_admin_treebeard/index_results.html"

    def get_index_view_kwargs(self, **kwargs):
        return super().get_index_view_kwargs(move_url_name=self.get_url_name("move"), **kwargs)

    @property
    def move_view(self):
        return self.move_view_class.as_view(
            model=self.model, permission_policy=self.permission_policy
        )

    def get_urlpatterns(self):
        return super().get_urlpatterns() + [path("move/", self.move_view, name="move")]
