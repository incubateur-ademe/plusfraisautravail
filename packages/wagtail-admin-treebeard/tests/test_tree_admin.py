import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import Permission
from django.urls import reverse

from tests.testapp.models import ALCategory, MPCategory, NSCategory

pytestmark = pytest.mark.django_db
XHR = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


def url(model, name, *args):
    return reverse(f"wagtailsnippets_testapp_{model._meta.model_name}:{name}", args=args)


def position(model):
    return "sorted-child" if model.node_order_by else "first-child"


@pytest.fixture(params=[ALCategory, MPCategory, NSCategory], ids=lambda m: m.__name__)
def tree(request):
    """Thème > (Emploi, Logement), Public > Entreprises."""
    model = request.param
    theme = model.add_root(name="Thème")
    housing = theme.add_child(name="Logement")
    theme.add_child(name="Emploi")
    public = model.add_root(name="Public")
    public.add_child(name="Entreprises")
    return {"model": model, "theme": theme, "housing": housing, "public": public}


@pytest.fixture
def admin_client(client, django_user_model):
    client.force_login(django_user_model.objects.create_superuser("admin", "a@b.c", "pw"))
    return client


def fresh(node):
    return type(node).objects.get(pk=node.pk)


def test_listing_is_in_tree_order_with_indented_draggable_rows(admin_client, tree):
    response = admin_client.get(url(tree["model"], "list"))

    assert response.status_code == 200
    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.select("table.listing tr[data-node]")
    order = {row["data-node"]: index for index, row in enumerate(rows)}
    position = {
        name: order[str(pk)] for name, pk in tree["model"].objects.values_list("name", "pk")
    }
    assert len(rows) == 5
    assert position["Entreprises"] == position["Public"] + 1
    assert {position["Logement"], position["Emploi"]} == {
        position["Thème"] + 1,
        position["Thème"] + 2,
    }
    housing = soup.select_one(f'tr[data-node="{tree["housing"].pk}"]')
    assert housing["draggable"] == "true"
    assert housing["style"] == "--tb-depth: 1"
    assert soup.select_one(f'tr[data-node="{tree["theme"].pk}"]')["style"] == "--tb-depth: 0"
    assert soup.select_one('[data-tb-tree-target="bar"]') is not None
    assert (
        soup.select_one(f'a[href="{url(tree["model"], "edit", tree["housing"].pk)}"]') is not None
    )


def test_listing_says_whether_siblings_can_be_reordered(admin_client, tree):
    response = admin_client.get(url(tree["model"], "list"))

    soup = BeautifulSoup(response.content, "html.parser")
    controller = soup.select_one('[data-controller="tb-tree"]')
    if tree["model"].node_order_by:
        assert controller["data-tb-tree-sorted-value"] == "true"
        assert "sorted by name and cannot be reordered" in controller.get_text()
    else:
        assert controller["data-tb-tree-sorted-value"] == "false"
        assert "cannot be reordered" not in controller.get_text()


def test_search_falls_back_to_the_flat_table(admin_client, tree):
    response = admin_client.get(url(tree["model"], "list") + "?q=Logement")

    assert response.status_code == 200
    assert b"Logement" in response.content
    assert b'data-controller="tb-tree"' not in response.content


def test_drop_on_a_node_nests_under_it(admin_client, tree):
    data = {"node": tree["housing"].pk, "target": tree["public"].pk, "position": "child"}

    response = admin_client.post(url(tree["model"], "move"), data, **XHR)

    assert response.status_code == 200
    assert fresh(tree["housing"]).get_parent() == tree["public"]
    assert fresh(tree["housing"]).get_depth() == 2


def test_drop_before_a_node_makes_it_a_sibling(admin_client, tree):
    model = tree["model"]
    companies = model.objects.get(name="Entreprises")
    data = {"node": companies.pk, "target": tree["housing"].pk, "position": "before"}

    response = admin_client.post(url(model, "move"), data, **XHR)

    assert response.status_code == 200
    assert fresh(companies).get_parent() == tree["theme"]
    if not model.node_order_by:
        children = fresh(tree["theme"]).get_children().values_list("name", flat=True)
        assert list(children) == ["Entreprises", "Logement", "Emploi"]


def test_drop_after_a_root_makes_it_a_root(admin_client, tree):
    model = tree["model"]
    data = {"node": tree["housing"].pk, "target": tree["public"].pk, "position": "after"}

    response = admin_client.post(url(model, "move"), data, **XHR)

    assert response.status_code == 200
    assert fresh(tree["housing"]).is_root()
    if not model.node_order_by:
        roots = model.get_root_nodes().values_list("name", flat=True)
        assert list(roots) == ["Thème", "Public", "Logement"]


def test_unknown_position_is_refused(admin_client, tree):
    data = {"node": tree["housing"].pk, "target": tree["public"].pk, "position": "sideways"}

    assert admin_client.post(url(tree["model"], "move"), data, **XHR).status_code == 400


def test_drop_on_a_descendant_is_refused(admin_client, tree):
    data = {"node": tree["theme"].pk, "target": tree["housing"].pk}

    response = admin_client.post(url(tree["model"], "move"), data, **XHR)

    assert response.status_code == 400
    assert fresh(tree["theme"]).is_root()


def test_drop_on_itself_is_refused(admin_client, tree):
    data = {"node": tree["theme"].pk, "target": tree["theme"].pk}

    response = admin_client.post(url(tree["model"], "move"), data, **XHR)

    assert response.status_code == 400


def test_unknown_node_is_a_404(admin_client, tree):
    target = tree["public"].pk
    for node in ("nope", 999999):
        data = {"node": node, "target": target}
        assert admin_client.post(url(tree["model"], "move"), data, **XHR).status_code == 404


def test_move_requires_the_change_permission(client, django_user_model, tree):
    user = django_user_model.objects.create_user("editor", "e@b.c", "pw")
    user.user_permissions.add(Permission.objects.get(codename="access_admin"))
    client.force_login(user)

    data = {"node": tree["housing"].pk, "target": tree["public"].pk}
    response = client.post(url(tree["model"], "move"), data, **XHR)

    assert response.status_code == 403
    assert fresh(tree["housing"]).get_parent() == tree["theme"]


def test_create_view_places_the_node_under_the_chosen_parent(admin_client, tree):
    model = tree["model"]
    data = {
        "name": "Santé",
        "treebeard_ref_node": tree["public"].pk,
        "treebeard_position": position(model),
    }

    response = admin_client.post(url(model, "add"), data)

    assert response.status_code == 302
    assert model.objects.get(name="Santé").get_parent() == tree["public"]


def test_create_view_with_no_reference_makes_a_root(admin_client, tree):
    model = tree["model"]
    data = {"name": "Santé", "treebeard_ref_node": "", "treebeard_position": position(model)}

    response = admin_client.post(url(model, "add"), data)

    assert response.status_code == 302
    node = model.objects.get(name="Santé")
    assert node.is_root()
    assert node.get_depth() == 1
    assert node in model.get_root_nodes()


def test_create_view_renders(admin_client, tree):
    response = admin_client.get(url(tree["model"], "add"))

    assert response.status_code == 200
    assert b'name="treebeard_ref_node"' in response.content


def test_edit_view_moves_the_node_under_another_parent(admin_client, tree):
    model = tree["model"]
    data = {
        "name": "Logement",
        "treebeard_ref_node": tree["public"].pk,
        "treebeard_position": position(model),
    }

    response = admin_client.post(url(model, "edit", tree["housing"].pk), data)

    assert response.status_code == 302
    assert fresh(tree["housing"]).get_parent() == tree["public"]


def test_edit_view_refuses_a_move_under_its_own_child(admin_client, tree):
    model = tree["model"]
    data = {
        "name": "Thème",
        "treebeard_ref_node": tree["housing"].pk,
        "treebeard_position": position(model),
    }

    response = admin_client.post(url(model, "edit", tree["theme"].pk), data)

    assert response.status_code == 200
    assert fresh(tree["theme"]).is_root()
