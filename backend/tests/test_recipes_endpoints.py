"""Integration tests for recipe endpoints."""

import json
import os

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Recipe, User
from app.utils.auth import create_access_token, get_password_hash


@pytest.mark.asyncio
async def test_create_and_get_recipe(
    client: AsyncClient, test_user: User, test_token: str, db_session: AsyncSession
):
    recipe_payload = {
        "title": "Test Recipe",
        "description": "A test",
        "ingredients": [{"name": "flour", "quantity": 1, "unit": "cup"}],
        "instructions": ["Mix", "Cook"],
        "category": "dinner",
    }

    # Create
    resp = await client.post(
        "/api/v1/recipes", json=recipe_payload, headers={"Authorization": f"Bearer {test_token}"}
    )
    assert resp.status_code == 201
    created = resp.json()
    assert created["title"] == "Test Recipe"

    # Get
    resp = await client.get(
        f"/api/v1/recipes/{created['id']}", headers={"Authorization": f"Bearer {test_token}"}
    )
    assert resp.status_code == 200
    got = resp.json()
    assert got["title"] == "Test Recipe"


@pytest.mark.asyncio
async def test_listing_and_filters(
    client: AsyncClient, test_user: User, test_token: str, db_session: AsyncSession
):
    # Create recipes with various properties
    r1 = Recipe(
        title="Pancakes",
        owner_id=test_user.id,
        category="breakfast",
        prep_time=10,
        visibility="public",
        ingredients=[{"name": "flour", "quantity": 1, "unit": "cup"}],
        instructions=["a"],
    )
    r2 = Recipe(
        title="Stew",
        owner_id=test_user.id,
        category="dinner",
        prep_time=60,
        visibility="private",
        ingredients=[{"name": "beef", "quantity": 1, "unit": "lb"}],
        instructions=["cook"],
    )
    db_session.add_all([r1, r2])
    await db_session.commit()

    # List public and own -> should include both when authenticated as test_user
    resp = await client.get("/api/v1/recipes", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    titles = [i["title"] for i in data["items"]]
    assert "Pancakes" in titles
    assert "Stew" in titles

    # Filter by category
    resp = await client.get(
        "/api/v1/recipes?category=breakfast", headers={"Authorization": f"Bearer {test_token}"}
    )
    items = resp.json()["items"]
    assert all(i["category"] == "breakfast" for i in items)

    # Max prep time
    resp = await client.get(
        "/api/v1/recipes?max_prep_time=30", headers={"Authorization": f"Bearer {test_token}"}
    )
    items = resp.json()["items"]
    assert all((i["prep_time"] is None) or (i["prep_time"] <= 30) for i in items)


@pytest.mark.asyncio
async def test_tags_and_tag_filters(
    client: AsyncClient, test_user: User, test_token: str, db_session: AsyncSession
):
    # Create recipe
    r = Recipe(
        title="Salad",
        owner_id=test_user.id,
        category="lunch",
        visibility="public",
        ingredients=[],
        instructions=[],
    )
    db_session.add(r)
    await db_session.commit()

    # Add tag
    resp = await client.post(
        f"/api/v1/recipes/{r.id}/tags",
        json={"tag_name": "vegan", "tag_category": "dietary"},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert resp.status_code == 201
    tag = resp.json()
    assert tag["tag_name"] == "vegan"

    # Adding same tag again should return 400
    resp = await client.post(
        f"/api/v1/recipes/{r.id}/tags",
        json={"tag_name": "vegan", "tag_category": "dietary"},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert resp.status_code == 400

    # Filter by tag
    resp = await client.get(
        "/api/v1/recipes?tags=vegan", headers={"Authorization": f"Bearer {test_token}"}
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any("Salad" == it["title"] for it in items)

    # Remove tag
    tag_id = tag["id"]
    resp = await client.delete(
        f"/api/v1/recipes/{r.id}/tags/{tag_id}", headers={"Authorization": f"Bearer {test_token}"}
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_favorites_and_list(
    client: AsyncClient, test_user: User, test_token: str, db_session: AsyncSession
):
    r = Recipe(
        title="FavRecipe",
        owner_id=test_user.id,
        category="dinner",
        visibility="public",
        ingredients=[],
        instructions=[],
    )
    db_session.add(r)
    await db_session.commit()

    # Favorite
    resp = await client.post(
        f"/api/v1/recipes/{r.id}/favorite", headers={"Authorization": f"Bearer {test_token}"}
    )
    assert resp.status_code == 201

    # Duplicate favorite returns 400
    resp = await client.post(
        f"/api/v1/recipes/{r.id}/favorite", headers={"Authorization": f"Bearer {test_token}"}
    )
    assert resp.status_code == 400

    # List favorites
    resp = await client.get(
        "/api/v1/recipes/favorites", headers={"Authorization": f"Bearer {test_token}"}
    )
    assert resp.status_code == 200
    items = resp.json()
    assert any(i["title"] == "FavRecipe" for i in items)

    # Unfavorite
    resp = await client.delete(
        f"/api/v1/recipes/{r.id}/favorite", headers={"Authorization": f"Bearer {test_token}"}
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_image_upload(
    client: AsyncClient, test_user: User, test_token: str, db_session: AsyncSession
):
    r = Recipe(
        title="ImgRecipe",
        owner_id=test_user.id,
        category="dinner",
        visibility="public",
        ingredients=[],
        instructions=[],
    )
    db_session.add(r)
    await db_session.commit()

    # Invalid content type
    resp = await client.post(
        f"/api/v1/recipes/{r.id}/image",
        files={"file": ("notimage.txt", b"hello", "text/plain")},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert resp.status_code == 400

    # Valid image
    content = b"\x89PNG\r\n\x1a\n" + b"0" * 10
    resp = await client.post(
        f"/api/v1/recipes/{r.id}/image",
        files={"file": ("image.png", content, "image/png")},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "image_url" in data and data["image_url"]

    # Cleanup uploaded file
    url = data["image_url"]
    if url and "/uploads/recipes/" in url:
        filename = url.split("/uploads/recipes/")[-1]
        path = os.path.join("uploads", "recipes", filename)
        if os.path.exists(path):
            os.remove(path)


@pytest.mark.asyncio
async def test_ratings_crud(
    client: AsyncClient, test_user: User, test_token: str, db_session: AsyncSession
):
    r = Recipe(
        title="RateRecipe",
        owner_id=test_user.id,
        category="lunch",
        visibility="public",
        ingredients=[],
        instructions=[],
    )
    db_session.add(r)
    await db_session.commit()

    # Create rating
    resp = await client.post(
        f"/api/v1/recipes/{r.id}/ratings",
        json={"rating": 5, "review": "Great"},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert resp.status_code == 201
    rating = resp.json()
    assert rating["rating"] == 5

    # Update rating via same endpoint
    resp = await client.post(
        f"/api/v1/recipes/{r.id}/ratings",
        json={"rating": 4, "review": "Good"},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert resp.status_code == 201
    rating = resp.json()
    assert rating["rating"] == 4

    # List ratings
    resp = await client.get(f"/api/v1/recipes/{r.id}/ratings")
    assert resp.status_code == 200
    assert any(rt["rating"] == 4 for rt in resp.json())

    # Delete rating
    resp = await client.delete(
        f"/api/v1/recipes/{r.id}/ratings", headers={"Authorization": f"Bearer {test_token}"}
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_nutrition_and_export_import(
    client: AsyncClient, test_user: User, test_token: str, db_session: AsyncSession
):
    # Nutrition for a non-existent recipe
    resp = await client.get("/api/v1/recipes/99999/nutrition")
    assert resp.status_code == 404

    # Create recipe with ingredients
    r = Recipe(
        title="NutRecipe",
        owner_id=test_user.id,
        category="dinner",
        visibility="public",
        ingredients=[{"name": "milk", "quantity": 1, "unit": "cup"}],
        instructions=[],
        serving_size=2,
    )
    db_session.add(r)
    await db_session.commit()

    resp = await client.get(f"/api/v1/recipes/{r.id}/nutrition")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data and "calories" in data["total"]


@pytest.mark.asyncio
async def test_list_recipes_pagination_and_metadata(client: AsyncClient, test_user: User, test_token: str, db_session: AsyncSession):
    # Create multiple public recipes
    recipes = []
    for i in range(5):
        r = Recipe(title=f"Paginated {i}", owner_id=test_user.id, category="dinner", visibility="public", ingredients=[], instructions=[])
        recipes.append(r)
        db_session.add(r)
    await db_session.commit()

    # Request page 2 with page_size=2
    resp = await client.get("/api/v1/recipes?page=2&page_size=2", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["pagination"]["page"] == 2
    assert data["pagination"]["page_size"] == 2
    assert data["pagination"]["total"] >= 5


@pytest.mark.asyncio
async def test_group_visibility_and_admin_edit(client: AsyncClient, test_user: User, test_token: str, db_session: AsyncSession):
    # Create a group and another user who owns a group recipe
    from app.models import Group, GroupMember

    owner = User(username="ownr", email="ownr@example.com", password_hash=get_password_hash("p"))
    db_session.add(owner)
    await db_session.commit()

    group = Group(name="G", owner_id=owner.id)
    db_session.add(group)
    await db_session.commit()

    # Owner creates a group recipe
    r = Recipe(title="GroupRecipe", owner_id=owner.id, category="dinner", visibility="group", group_id=group.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()

    # test_user is not a member yet -> cannot access
    resp = await client.get(f"/api/v1/recipes/{r.id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 403

    # Add test_user as group member (admin)
    gm = GroupMember(group_id=group.id, user_id=test_user.id, role="admin", permissions={})
    db_session.add(gm)
    await db_session.commit()

    # Now test_user can access
    resp = await client.get(f"/api/v1/recipes/{r.id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200

    # And can update because admin
    resp = await client.put(f"/api/v1/recipes/{r.id}", json={"title": "Updated"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


@pytest.mark.asyncio
async def test_delete_recipe_permissions(client: AsyncClient, test_user: User, test_token: str, db_session: AsyncSession):
    # Create recipe owned by other
    other = User(username="otherdel", email="od@example.com", password_hash=get_password_hash("p"))
    db_session.add(other)
    await db_session.commit()

    r = Recipe(title="ToDelete", owner_id=other.id, category="dinner", visibility="public", ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()

    # test_user cannot delete
    resp = await client.delete(f"/api/v1/recipes/{r.id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 403

    # Admin can delete
    admin = User(username="admindel", email="adm@example.com", password_hash=get_password_hash("p"), is_admin=True)
    db_session.add(admin)
    await db_session.commit()
    token_admin = create_access_token({"sub": str(admin.id)})

    resp = await client.delete(f"/api/v1/recipes/{r.id}", headers={"Authorization": f"Bearer {token_admin}"})
    assert resp.status_code == 204

    # Export (should include user's recipes)
    resp = await client.get(
        "/api/v1/recipes/export/all", headers={"Authorization": f"Bearer {test_token}"}
    )
    assert resp.status_code == 200
    assert resp.headers["Content-Disposition"].startswith("attachment; filename=recipes_")

    # Import valid JSON file
    content = json.dumps(
        [{"title": "Imported", "ingredients": [{"name": "x", "quantity": 1, "unit": "cup"}]}]
    ).encode()
    resp = await client.post(
        "/api/v1/recipes/import",
        files={"file": ("recipes.json", content, "application/json")},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 1

    # Import invalid JSON
    resp = await client.post(
        "/api/v1/recipes/import",
        files={"file": ("bad.json", b"notjson", "application/json")},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_access_control_for_private_recipe(
    client: AsyncClient, test_user: User, db_session: AsyncSession
):
    # Create another user
    other = User(
        username="other", email="other@example.com", password_hash=get_password_hash("pass")
    )
    db_session.add(other)
    await db_session.commit()
    token_other = create_access_token({"sub": str(other.id)})

    # Create private recipe by test_user
    r = Recipe(
        title="PrivateR",
        owner_id=test_user.id,
        category="dinner",
        visibility="private",
        ingredients=[],
        instructions=[],
    )
    db_session.add(r)
    await db_session.commit()

    # Other user should not access
    resp = await client.get(
        f"/api/v1/recipes/{r.id}", headers={"Authorization": f"Bearer {token_other}"}
    )
    assert resp.status_code == 403

    # Admin can access
    admin = User(
        username="a", email="a@example.com", password_hash=get_password_hash("p"), is_admin=True
    )
    db_session.add(admin)
    await db_session.commit()
    token_admin = create_access_token({"sub": str(admin.id)})

    resp = await client.get(
        f"/api/v1/recipes/{r.id}", headers={"Authorization": f"Bearer {token_admin}"}
    )
    assert resp.status_code == 200
