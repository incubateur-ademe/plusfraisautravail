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


def test_listing_nests_children_inside_their_parent(admin_client, tree):
    response = admin_client.get(url(tree["model"], "list"))

    assert response.status_code == 200
    soup = BeautifulSoup(response.content, "html.parser")
    theme, housing = tree["theme"].pk, tree["housing"].pk
    assert soup.select_one(f'[data-node="{theme}"] [data-node="{housing}"]') is not None
    assert soup.select_one("[data-root-zone]") is not None
    assert soup.select_one(f'a[href="{url(tree["model"], "edit", housing)}"]') is not None


def test_search_falls_back_to_the_flat_table(admin_client, tree):
    response = admin_client.get(url(tree["model"], "list") + "?q=Logement")

    assert response.status_code == 200
    assert b"Logement" in response.content
    assert b'data-controller="tb-tree"' not in response.content


def test_drop_on_a_node_nests_under_it(admin_client, tree):
    data = {"node": tree["housing"].pk, "target": tree["public"].pk}

    response = admin_client.post(url(tree["model"], "move"), data, **XHR)

    assert response.status_code == 200
    assert fresh(tree["housing"]).get_parent() == tree["public"]
    assert fresh(tree["housing"]).get_depth() == 2


def test_drop_on_the_root_zone_makes_a_root(admin_client, tree):
    response = admin_client.post(url(tree["model"], "move"), {"node": tree["housing"].pk}, **XHR)

    assert response.status_code == 200
    assert fresh(tree["housing"]).is_root()
    assert set(tree["model"].get_root_nodes().values_list("name", flat=True)) == {
        "Thème",
        "Public",
        "Logement",
    }


def test_drop_a_root_on_the_root_zone_is_a_no_op(admin_client, tree):
    response = admin_client.post(url(tree["model"], "move"), {"node": tree["theme"].pk}, **XHR)

    assert response.status_code == 200
    assert fresh(tree["theme"]).is_root()
    assert fresh(tree["housing"]).get_parent() == tree["theme"]


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
    assert admin_client.post(url(tree["model"], "move"), {"node": "nope"}, **XHR).status_code == 404
    assert admin_client.post(url(tree["model"], "move"), {"node": 999999}, **XHR).status_code == 404


def test_move_requires_the_change_permission(client, django_user_model, tree):
    user = django_user_model.objects.create_user("editor", "e@b.c", "pw")
    user.user_permissions.add(Permission.objects.get(codename="access_admin"))
    client.force_login(user)

    response = client.post(url(tree["model"], "move"), {"node": tree["housing"].pk}, **XHR)

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
