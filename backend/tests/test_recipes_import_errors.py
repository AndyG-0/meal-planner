import pytest


@pytest.mark.asyncio
async def test_import_json_with_errors(client, test_user, test_token):
    # Prepare JSON with one valid and two invalid recipes
    payload = [
        {"title": "Good", "ingredients": [{"name": "x", "quantity": 1, "unit": "cup"}]},
        {"ingredients": [{"name": "no_title", "quantity": 1, "unit": "tbsp"}]},  # missing title
        {"title": "BadIng", "ingredients": "not-an-array"},  # bad ingredients type
    ]

    import json

    content = json.dumps(payload).encode()

    resp = await client.post(
        "/api/v1/recipes/import",
        files={"file": ("recipes.json", content, "application/json")},
        headers={"Authorization": f"Bearer {test_token}"},
    )

    assert resp.status_code == 200
    body = resp.json()
    # The import will accept records that have a title and ingredients; the bad entry with missing title should be reported
    assert body["imported"] == 2
    assert isinstance(body["errors"], list)
    assert any("Missing required fields" in (str(e)) for e in body["errors"])
