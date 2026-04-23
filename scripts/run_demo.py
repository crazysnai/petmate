from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database import DB_PATH, init_db  # noqa: E402
from app.main import app  # noqa: E402


def show(title: str, data: dict) -> None:
    print(f"\n## {title}")
    print(json.dumps(data, ensure_ascii=False, indent=2))


def assert_ok(response, title: str) -> dict:
    if response.status_code >= 400:
        raise RuntimeError(f"{title} failed: {response.status_code} {response.text}")
    return response.json()


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()

    client = TestClient(app)

    child = assert_ok(
        client.post(
            "/api/child/create",
            json={"name": "小林", "age": 8, "guardian_name": "林妈妈"},
        ),
        "create child",
    )
    child_id = child["child"]["id"]
    show("创建孩子", child)

    pet = assert_ok(
        client.post("/api/pet/create", json={"child_id": child_id, "name": "豆豆"}),
        "create pet",
    )
    show("创建宠物", pet)

    walk = assert_ok(
        client.post("/api/adventure/walk", json={"child_id": child_id, "distance_delta_meters": 500}),
        "walk 500m",
    )
    show("上报走路 500 米", walk)

    plant_results = []
    for image_name in ["dandelion_test.jpg", "clover_test.jpg"]:
        plant_results.append(
            assert_ok(
                client.post("/api/scan/plant", json={"child_id": child_id, "image_name": image_name}),
                f"scan {image_name}",
            )
        )
    show("扫描 2 种植物", {"results": plant_results})

    animal = assert_ok(
        client.post("/api/discovery/animal-clue", json={"child_id": child_id}),
        "discover animal clue",
    )
    show("发现动物线索", animal)

    interaction = assert_ok(
        client.post(
            "/api/animal/interact",
            json={
                "child_id": child_id,
                "animal_key": animal["animal_clue"]["animal_key"],
                "action": "greet",
            },
        ),
        "interact with animal",
    )
    show("和动物伙伴互动", interaction)

    first_food = plant_results[0]["drops"][0]["item_key"]
    feed = assert_ok(
        client.post("/api/pet/feed", json={"child_id": child_id, "food_key": first_food}),
        "feed pet",
    )
    show("喂养宠物并完成今日关卡", feed)

    extra_walk = assert_ok(
        client.post("/api/adventure/walk", json={"child_id": child_id, "distance_delta_meters": 250}),
        "walk extra 250m",
    )
    show("额外走 250 米解锁第 3 次植物机会", extra_walk)

    third_plant = assert_ok(
        client.post("/api/scan/plant", json={"child_id": child_id, "image_name": "plane_leaf_test.jpg"}),
        "scan third plant",
    )
    show("扫描第 3 种植物", third_plant)

    encyclopedia = assert_ok(client.get(f"/api/encyclopedia/me?child_id={child_id}"), "encyclopedia")
    show("图鉴", encyclopedia)

    status = assert_ok(client.get(f"/api/pet/status?child_id={child_id}"), "pet status")
    show("宠物状态", status)

    summary = assert_ok(client.get(f"/api/parent/summary/today?child_id={child_id}"), "parent summary")
    show("家长今日摘要", summary)

    assert status["pet"]["level"] >= 2, "pet should reach Lv2"
    assert len(encyclopedia["plants"]) >= 3, "three plants should be collected"
    assert len(encyclopedia["animals"]) >= 1, "one animal clue should be collected"
    assert summary["discoveries"]["animal_interaction_count"] >= 1, "animal interaction should be recorded"
    assert summary["adventure"]["completed"] is True, "daily adventure should be completed"

    print("\nDemo passed: walk -> scan -> animal clue -> feed -> level up -> parent summary")


if __name__ == "__main__":
    main()
