import json
import builtins
import io
import os
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.auth import create_access_token, get_password_hash
from app.models import Recipe, User


@pytest.mark.asyncio
async def test_update_recipe_forbidden(client: AsyncClient, test_user: User, test_token: str, db_session: AsyncSession):
    # Create recipe owned by another user
    other = User(username="ownerx", email="ox@example.com", password_hash=get_password_hash("p"))
    db_session.add(other)
    await db_session.commit()

    r = Recipe(title="X", owner_id=other.id, ingredients=[], instructions=[], visibility="public")
    db_session.add(r)
    await db_session.commit()

    # test_user should not be able to update
    resp = await client.put(f"/api/v1/recipes/{r.id}", json={"title": "NewTitle"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_add_tag_and_remove_forbidden_and_not_found(client: AsyncClient, test_user: User, test_token: str, db_session: AsyncSession):
    # Create recipe owned by other
    other = User(username="ownery", email="oy@example.com", password_hash=get_password_hash("p"))
    db_session.add(other)
    await db_session.commit()

    r = Recipe(title="T", owner_id=other.id, ingredients=[], instructions=[], visibility="public")
    db_session.add(r)
    await db_session.commit()

    # Adding tag by non-owner should be forbidden
    resp = await client.post(f"/api/v1/recipes/{r.id}/tags", json={"tag_name": "vegan", "tag_category": "dietary"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 403

    # Removing non-existent tag should 404 if owner, otherwise 403; since non-owner, expect 403
    resp2 = await client.delete(f"/api/v1/recipes/{r.id}/tags/9999", headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 403


@pytest.mark.asyncio
async def test_unfavorite_not_found(client: AsyncClient, test_user: User, test_token: str, db_session: AsyncSession):
    # Unfavorite a recipe that's not in favorites -> 404
    r = Recipe(title="Unf", owner_id=test_user.id, ingredients=[], instructions=[], visibility="public")
    db_session.add(r)
    await db_session.commit()

    resp = await client.delete(f"/api/v1/recipes/{r.id}/favorite", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_image_upload_write_failure(client: AsyncClient, test_user: User, test_token: str, db_session: AsyncSession, monkeypatch):
    # Create recipe owned by test_user
    r = Recipe(title="ImgFail", owner_id=test_user.id, ingredients=[], instructions=[], visibility="public")
    db_session.add(r)
    await db_session.commit()

    # Monkeypatch builtins.open to raise when writing
    orig_open = builtins.open

    def fake_open(path, mode="r", *args, **kwargs):
        # Only raise when writing to uploads/recipes path
        pstr = str(path)
        # match 'uploads/recipes' in both relative and absolute paths
        if "uploads/recipes" in pstr and "w" in mode:
            raise OSError("disk error")
        return orig_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)

    content = b"\x89PNG\r\n\x1a\n" + b"0" * 10
    resp = await client.post(
        f"/api/v1/recipes/{r.id}/image",
        files={"file": ("image.png", content, "image/png")},
        headers={"Authorization": f"Bearer {test_token}"},
    )

    # Should return 500 due to save failure
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_import_invalid_json(client: AsyncClient, test_user: User, test_token: str):
    bad = b"not-json"
    resp = await client.post(
        "/api/v1/recipes/import",
        files={"file": ("recipes.json", bad, "application/json")},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_recipe_with_string_ingredient_parsing(client: AsyncClient, test_user: User, test_token: str):
    payload = {
        "title": "StringIng",
        "ingredients": ["1 cup sugar","(100 g) cheese, softened"],
        "instructions": ["a"],
        "category": "dessert",
    }

    resp = await client.post("/api/v1/recipes", json=payload, headers={"Authorization": f"Bearer {test_token}"})
    # Parenthetical ingredient parsing is not supported in the string->ingredient conversion and should return 422
    assert resp.status_code == 422
    body = resp.json()
    # Error message should indicate measurements in ingredient name
    assert any("measurement" in (d.get("msg") or d.get("message") or "").lower() for d in body.get("detail", []))