from django.db import models
from treebeard.al_tree import AL_Node
from treebeard.mp_tree import MP_Node
from treebeard.ns_tree import NS_Node
from wagtail.admin.panels import FieldPanel

from wagtail_admin_treebeard.forms import TreeNodeForm, tree_panel


class Named(models.Model):
    name = models.CharField(max_length=80)
    panels = [FieldPanel("name"), tree_panel()]
    base_form_class = TreeNodeForm

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class ALCategory(AL_Node, Named):
    """Unsorted: siblings keep the order given by drag and drop."""

    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children_set", on_delete=models.CASCADE
    )
    sib_order = models.PositiveIntegerField()


class MPCategory(MP_Node, Named):
    """Unsorted: siblings keep the order given by drag and drop."""


class NSCategory(NS_Node, Named):
    """Sorted by name: drag and drop only changes the parent, treebeard keeps siblings sorted."""

    node_order_by = ["name"]
