from django.utils.translation import gettext_lazy as _
from treebeard.forms import MoveNodeForm
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.panels import FieldPanel, MultiFieldPanel

INVALID_MOVE_MESSAGE = _("An item cannot be moved under itself or one of its descendants.")


def tree_panel(heading=None):
    """The two treebeard fields ("Relative to" and "Position") as a Wagtail panel."""
    return MultiFieldPanel(
        [FieldPanel("treebeard_ref_node"), FieldPanel("treebeard_position")],
        heading=heading or _("Place in the tree"),
    )


class TreeNodeForm(MoveNodeForm, WagtailAdminModelForm):
    """Wagtail admin form for a django-treebeard node.

    Set it as ``base_form_class`` on the node model and add ``tree_panel()`` to its panels.
    """

    def _get_initial(self, instance):
        # Wagtail hands the create view an unsaved instance; treebeard expects a saved node.
        if not instance._state.adding:
            return super()._get_initial(instance)
        return {"treebeard_position": "sorted-child" if self.is_sorted else "first-child"}

    def _set_ref_model_queryset(self, opts, instance):
        if instance is not None and instance._state.adding:
            instance = None
        super()._set_ref_model_queryset(opts, instance)

    def clean(self):
        cleaned_data = super().clean()
        reference = cleaned_data.get("treebeard_ref_node")
        node = self.instance
        if (
            reference
            and not node._state.adding
            and (reference == node or reference.is_descendant_of(node))
        ):
            self.add_error("treebeard_ref_node", INVALID_MOVE_MESSAGE)
        return cleaned_data
