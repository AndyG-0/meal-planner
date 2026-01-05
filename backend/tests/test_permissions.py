"""Tests for PermissionService helpers."""

from app.services.permissions import PermissionService


class DummyUser:
    def __init__(self, id=1, is_admin=False):
        self.id = id
        self.is_admin = is_admin


class DummyRecipe:
    def __init__(self, owner_id=1, visibility="private", group_id=None):
        self.owner_id = owner_id
        self.visibility = visibility
        self.group_id = group_id


class DummyCalendar:
    def __init__(self, owner_id=1, visibility="private", group_id=None):
        self.owner_id = owner_id
        self.visibility = visibility
        self.group_id = group_id


class DummyGrocery:
    def __init__(self, user_id=1, visibility="private", group_id=None):
        self.user_id = user_id
        self.visibility = visibility
        self.group_id = group_id


class FakeDB:
    def __init__(self, group_member_exists=False, group_owner_id=None, group_admin_exists=False):
        self.group_member_exists = group_member_exists
        self.group_owner_id = group_owner_id
        self.group_admin_exists = group_admin_exists

    def query(self, model):
        model_name = getattr(model, "__name__", "")

        class Filter:
            def __init__(self, parent, model_name):
                self.parent = parent
                self.model_name = model_name

            def filter(self, *args, **kwargs):
                return self

            def first(self):
                # Group lookup
                if self.model_name == "Group":
                    if self.parent.group_owner_id is not None:

                        class G:
                            def __init__(self, owner_id):
                                self.owner_id = owner_id

                        return G(self.parent.group_owner_id)
                    return None

                # GroupMember lookup
                if self.model_name == "GroupMember":
                    if self.parent.group_member_exists or self.parent.group_admin_exists:

                        class M:
                            pass

                        return M()
                    return None

                return None

        return Filter(self, model_name)


def test_permissions_recipe_public_view():
    assert PermissionService.can_view_recipe(None, DummyRecipe(visibility="public"), None) is True


def test_permissions_recipe_requires_auth():
    assert PermissionService.can_view_recipe(None, DummyRecipe(visibility="private"), None) is False


def test_permissions_recipe_admin_can_view_and_edit():
    user = DummyUser(is_admin=True)
    assert PermissionService.can_view_recipe(None, DummyRecipe(owner_id=2), user) is True
    assert PermissionService.can_edit_recipe(None, DummyRecipe(owner_id=2), user) is True


def test_permissions_recipe_owner_can_view_and_edit_and_delete():
    user = DummyUser(id=3)
    recipe = DummyRecipe(owner_id=3)
    assert PermissionService.can_view_recipe(None, recipe, user) is True
    assert PermissionService.can_edit_recipe(None, recipe, user) is True
    assert PermissionService.can_delete_recipe(None, recipe, user) is True


def test_permissions_recipe_group_member():
    user = DummyUser(id=4)
    recipe = DummyRecipe(owner_id=5, visibility="group", group_id=10)
    # monkeypatch internal group check
    original = PermissionService._is_group_member
    try:
        PermissionService._is_group_member = staticmethod(lambda db, gid, uid: True)
        assert PermissionService.can_view_recipe(None, recipe, user) is True
    finally:
        PermissionService._is_group_member = original


def test_permissions_calendar_and_grocery_group_checks():
    user = DummyUser(id=7)
    cal = DummyCalendar(owner_id=8, visibility="group", group_id=11)
    grocery = DummyGrocery(user_id=9, visibility="group", group_id=12)

    # _is_group_member True
    original = PermissionService._is_group_member
    try:
        PermissionService._is_group_member = staticmethod(lambda db, gid, uid: True)
        assert PermissionService.can_view_calendar(None, cal, user) is True
        assert PermissionService.can_view_grocery_list(None, grocery, user) is True
    finally:
        PermissionService._is_group_member = original


def test_is_group_admin_logic():
    # Simulate group owner
    db = FakeDB(group_owner_id=20)
    assert PermissionService._is_group_admin(db, 1, 20) is True
    # Simulate group admin member
    db = FakeDB(group_admin_exists=True)
    assert PermissionService._is_group_admin(db, 1, 99) is True
    # None
    db = FakeDB()
    assert PermissionService._is_group_admin(db, 1, 99) is False
