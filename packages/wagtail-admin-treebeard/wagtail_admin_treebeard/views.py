from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import path
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views import View
from wagtail.admin.auth import permission_denied
from wagtail.snippets.views.snippets import IndexView, SnippetViewSet

from wagtail_admin_treebeard.forms import INVALID_MOVE_MESSAGE


class TreeTableMixin:
    """Marks each row with its node pk and depth, and makes it draggable."""

    def get_row_attrs(self, instance):
        return {
            **super().get_row_attrs(instance),
            "data-node": instance.pk,
            "draggable": "true",
            "style": f"--tb-depth: {instance.tree_depth}",
        }


class TreeIndexView(IndexView):
    """Wagtail's standard listing, in tree order with indented rows and drag and drop.

    Searching, filtering or sorting a column gives the plain listing.
    """

    move_url_name = None

    @cached_property
    def is_tree_mode(self):
        return not (self.is_searching or self.is_filtering or self.is_explicitly_ordered)

    @cached_property
    def sort_labels(self):
        """Labels of the fields treebeard sorts siblings by; empty when editors order them."""
        fields = self.model.node_order_by or []
        return [str(self.model._meta.get_field(name).verbose_name) for name in fields]

    def get_paginate_by(self, queryset):
        # Every node must be on the page to be a drop target, like Wagtail's own reorder mode.
        return None if self.is_tree_mode else super().get_paginate_by(queryset)

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.is_tree_mode:
            return queryset
        # ponytail: DFS order and depth resolved in Python so AL, MP and NS share one code path;
        # switch to backend-specific ORM ordering if trees get big enough to matter.
        tree = {
            node.pk: (index, info["level"])
            for index, (node, info) in enumerate(self.model.get_annotated_list())
        }
        nodes = sorted(queryset, key=lambda node: tree[node.pk][0])
        for node in nodes:
            node.tree_depth = tree[node.pk][1]
        return nodes

    @cached_property
    def table_class(self):
        table_class = super().table_class
        if not self.is_tree_mode:
            return table_class
        return type(f"{self.model.__name__}TreeTable", (TreeTableMixin, table_class), {})


# Drop position -> treebeard position for (sorted, unsorted) models.
POSITIONS = {
    "child": ("sorted-child", "first-child"),
    "before": ("sorted-sibling", "left"),
    "after": ("sorted-sibling", "right"),
}


class TreeMoveView(View):
    """Moves a node relative to another one.

    POST ``node`` and ``target`` (both pks) and ``position``: ``child`` to nest ``node``
    under ``target``, ``before`` or ``after`` to make it a sibling of ``target``.
    """

    model = None
    permission_policy = None

    def post(self, request):
        if not self.permission_policy.user_has_permission(request.user, "change"):
            return permission_denied(request)
        node = self.get_node(request.POST.get("node"))
        target = self.get_node(request.POST.get("target"))
        position = request.POST.get("position")
        if position not in POSITIONS:
            return HttpResponseBadRequest("Unknown position")
        if target == node or target.is_descendant_of(node):
            messages.error(request, INVALID_MOVE_MESSAGE)
            return HttpResponseBadRequest(INVALID_MOVE_MESSAGE)
        sorted_position, plain_position = POSITIONS[position]
        node.move(target, pos=sorted_position if self.model.node_order_by else plain_position)
        if position == "child":
            message = _("“%(node)s” moved under “%(target)s”.")
        else:
            message = _("“%(node)s” moved next to “%(target)s”.")
        messages.success(request, message % {"node": node, "target": target})
        return JsonResponse({"ok": True})

    def get_node(self, pk):
        try:
            return get_object_or_404(self.model, pk=pk)
        except (ValueError, ValidationError):
            raise Http404 from None


class TreeSnippetViewSet(SnippetViewSet):
    """A SnippetViewSet for a django-treebeard model (AL, MP or NS)."""

    index_view_class = TreeIndexView
    index_template_name = "wagtail_admin_treebeard/index.html"
    index_results_template_name = "wagtail_admin_treebeard/index_results.html"

    def get_index_view_kwargs(self, **kwargs):
        return super().get_index_view_kwargs(move_url_name=self.get_url_name("move"), **kwargs)

    def get_urlpatterns(self):
        move = TreeMoveView.as_view(model=self.model, permission_policy=self.permission_policy)
        return super().get_urlpatterns() + [path("move/", move, name="move")]
