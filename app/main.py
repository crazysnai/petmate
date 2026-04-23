from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import FastAPI, HTTPException

from app.catalog import (
    ANIMAL_CLUES,
    ANIMAL_INTERACTIONS,
    FOOD_EFFECTS,
    PLANTS,
    animal_by_key,
    choose_animal,
    choose_plant,
)
from app.database import get_db, init_db, row_to_dict
from app.schemas import (
    AnimalClueDiscover,
    AnimalInteract,
    ChildCreate,
    FeedPet,
    GuardianSettingsUpdate,
    PetCreate,
    PlantScan,
    WalkReport,
)

app = FastAPI(title="PetMate Adventure API", version="0.1.0")

DEFAULT_CHILD_WEIGHT_KG = 25
STEP_LENGTH_METERS = 0.65
WALKING_METERS_PER_MINUTE = 75


@app.on_event("startup")
def startup() -> None:
    init_db()


def today() -> str:
    return date.today().isoformat()


def require_child(db, child_id: int) -> dict[str, Any]:
    row = db.execute("SELECT * FROM child WHERE id = ?", (child_id,)).fetchone()
    child = row_to_dict(row)
    if child is None:
        raise HTTPException(status_code=404, detail="Child not found")
    return child


def ensure_adventure_day(db, child_id: int) -> dict[str, Any]:
    require_child(db, child_id)
    day = today()
    db.execute(
        """
        INSERT OR IGNORE INTO adventure_day (child_id, day)
        VALUES (?, ?)
        """,
        (child_id, day),
    )
    row = db.execute(
        "SELECT * FROM adventure_day WHERE child_id = ? AND day = ?",
        (child_id, day),
    ).fetchone()
    return row_to_dict(row) or {}


def get_guardian_settings(db, child_id: int) -> dict[str, Any]:
    settings = row_to_dict(
        db.execute("SELECT * FROM guardian_settings WHERE child_id = ?", (child_id,)).fetchone()
    )
    if settings is None:
        raise HTTPException(status_code=404, detail="Guardian settings not found")
    return settings


def get_pet(db, child_id: int) -> dict[str, Any] | None:
    return row_to_dict(db.execute("SELECT * FROM pet WHERE child_id = ?", (child_id,)).fetchone())


def add_pet_xp(db, child_id: int, xp: int) -> dict[str, Any] | None:
    pet = get_pet(db, child_id)
    if pet is None:
        return None

    level = int(pet["level"])
    current_xp = int(pet["xp"]) + xp
    while current_xp >= level * 100:
        current_xp -= level * 100
        level += 1

    db.execute(
        """
        UPDATE pet
        SET level = ?, xp = ?
        WHERE child_id = ?
        """,
        (level, current_xp, child_id),
    )
    return get_pet(db, child_id)


def add_inventory(db, child_id: int, item_key: str, item_name: str, item_type: str, quantity: int) -> None:
    db.execute(
        """
        INSERT INTO inventory_item (child_id, item_key, item_name, item_type, quantity)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(child_id, item_key)
        DO UPDATE SET quantity = quantity + excluded.quantity
        """,
        (child_id, item_key, item_name, item_type, quantity),
    )


def change_adventure_xp(db, child_id: int, xp: int) -> None:
    ensure_adventure_day(db, child_id)
    db.execute(
        """
        UPDATE adventure_day
        SET xp = xp + ?
        WHERE child_id = ? AND day = ?
        """,
        (xp, child_id, today()),
    )


def estimate_activity(distance_meters: int, steps: int | None, active_minutes: int | None) -> dict[str, Any]:
    estimated_steps = steps if steps is not None else round(distance_meters / STEP_LENGTH_METERS)
    estimated_minutes = active_minutes if active_minutes is not None else max(1, round(distance_meters / WALKING_METERS_PER_MINUTE))
    estimated_kcal = round((distance_meters / 1000) * DEFAULT_CHILD_WEIGHT_KG * 0.6, 1)
    activity_energy = max(1, round(distance_meters / 100 + estimated_minutes / 5))
    return {
        "steps": max(0, estimated_steps),
        "active_minutes": max(0, estimated_minutes),
        "estimated_kcal": estimated_kcal,
        "activity_energy": activity_energy,
    }


def progress_counts(db, child_id: int) -> dict[str, int]:
    scans = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM scan_log
        WHERE child_id = ? AND date(created_at, '+8 hours') = ?
        """,
        (child_id, today()),
    ).fetchone()["count"]
    animals = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM animal_clue_log
        WHERE child_id = ? AND date(created_at, '+8 hours') = ?
        """,
        (child_id, today()),
    ).fetchone()["count"]
    feeds = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM feed_log
        WHERE child_id = ? AND date(created_at, '+8 hours') = ?
        """,
        (child_id, today()),
    ).fetchone()["count"]
    interactions = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM animal_interaction_log
        WHERE child_id = ? AND date(created_at, '+8 hours') = ?
        """,
        (child_id, today()),
    ).fetchone()["count"]
    return {"plant_scans": scans, "animal_clues": animals, "feeds": feeds, "animal_interactions": interactions}


def enriched_animals(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for entry in entries:
        animal = animal_by_key(entry["entry_key"])
        enriched.append(
            {
                **entry,
                "favorite": animal.favorite if animal else "自然食材",
                "habitat": animal.habitat if animal else "安全户外区域",
                "greeting": animal.greeting if animal else "伙伴回应了你的观察。",
                "friendship_to_adopt": max(0, 100 - int(entry["friendship"])),
            }
        )
    return enriched


def next_action_for(adventure: dict[str, Any], animals: list[dict[str, Any]]) -> str:
    if not adventure["completed"]:
        for task in adventure["tasks"]:
            if not task["completed"] and not task.get("optional"):
                return f"下一步建议：{task['title']}。"
    active = next((animal for animal in animals if not animal["adopted"]), None)
    if active is not None:
        return f"可以和{active['name']}打招呼，继续提升友好度。"
    return "今天已经完成完整探险，明天可以继续观察新的植物和动物线索。"


def adventure_response(db, child_id: int) -> dict[str, Any]:
    adventure = ensure_adventure_day(db, child_id)
    settings = get_guardian_settings(db, child_id)
    walk_target = int(settings["daily_distance_goal"])
    counts = progress_counts(db, child_id)
    tasks = [
        {
            "key": "walk_daily_goal",
            "title": f"户外走 {walk_target} 米",
            "target": walk_target,
            "current": min(adventure["distance_meters"], walk_target),
            "completed": adventure["distance_meters"] >= walk_target,
        },
        {
            "key": "scan_2_plants",
            "title": "扫描 2 种植物",
            "target": 2,
            "current": min(counts["plant_scans"], 2),
            "completed": counts["plant_scans"] >= 2,
        },
        {
            "key": "find_1_animal_clue",
            "title": "发现 1 个动物线索",
            "target": 1,
            "current": min(counts["animal_clues"], 1),
            "completed": counts["animal_clues"] >= 1,
        },
        {
            "key": "feed_pet_once",
            "title": "喂养宠物 1 次",
            "target": 1,
            "current": min(counts["feeds"], 1),
            "completed": counts["feeds"] >= 1,
        },
        {
            "key": "animal_interact_once",
            "title": "和动物伙伴互动 1 次",
            "target": 1,
            "current": min(counts["animal_interactions"], 1),
            "completed": counts["animal_interactions"] >= 1,
            "optional": True,
        },
    ]
    completed = all(task["completed"] for task in tasks if not task.get("optional"))
    if completed and not adventure["completed"]:
        db.execute(
            """
            UPDATE adventure_day
            SET completed = 1, reward_claimed = 1, xp = xp + 50
            WHERE child_id = ? AND day = ?
            """,
            (child_id, today()),
        )
        add_pet_xp(db, child_id, 50)
        adventure = ensure_adventure_day(db, child_id)

    return {
        "child_id": child_id,
        "day": adventure["day"],
        "chapter": adventure["chapter"],
        "stage": adventure["stage"],
        "distance_meters": adventure["distance_meters"],
        "activity": {
            "steps": adventure["steps"],
            "active_minutes": adventure["active_minutes"],
            "estimated_kcal": round(float(adventure["estimated_kcal"]), 1),
            "activity_energy": adventure["activity_energy"],
            "kcal_note": "估算值，用于家长健康参考，不作为孩子奖励核心。",
        },
        "exploration_energy": adventure["exploration_energy"],
        "available_chances": {
            "plant": adventure["plant_chances"],
            "animal": adventure["animal_chances"],
        },
        "xp": adventure["xp"],
        "completed": bool(adventure["completed"]),
        "tasks": tasks,
        "rewards": {
            "completion_xp": 50,
            "badge_progress": "小小观察员",
        },
    }


def inventory_for_child(db, child_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT item_key, item_name, item_type, quantity
        FROM inventory_item
        WHERE child_id = ?
        ORDER BY item_type, item_name
        """,
        (child_id,),
    ).fetchall()
    return [dict(row) for row in rows]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/child/create")
def create_child(payload: ChildCreate) -> dict[str, Any]:
    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO child (name, age, guardian_name) VALUES (?, ?, ?)",
            (payload.name, payload.age, payload.guardian_name),
        )
        child_id = int(cursor.lastrowid)
        db.execute(
            """
            INSERT INTO guardian_settings
            (child_id, outdoor_enabled, animal_clues_enabled, daily_distance_goal, max_daily_distance)
            VALUES (?, 1, 1, 500, 3000)
            """,
            (child_id,),
        )
        ensure_adventure_day(db, child_id)
        child = require_child(db, child_id)
        settings = row_to_dict(
            db.execute("SELECT * FROM guardian_settings WHERE child_id = ?", (child_id,)).fetchone()
        )
        return {"child": child, "guardian_settings": settings}


@app.post("/api/pet/create")
def create_pet(payload: PetCreate) -> dict[str, Any]:
    with get_db() as db:
        require_child(db, payload.child_id)
        existing = get_pet(db, payload.child_id)
        if existing is not None:
            return {"pet": existing, "created": False}
        cursor = db.execute(
            "INSERT INTO pet (child_id, name) VALUES (?, ?)",
            (payload.child_id, payload.name),
        )
        pet = row_to_dict(db.execute("SELECT * FROM pet WHERE id = ?", (cursor.lastrowid,)).fetchone())
        return {"pet": pet, "created": True}


@app.get("/api/pet/status")
def pet_status(child_id: int) -> dict[str, Any]:
    with get_db() as db:
        require_child(db, child_id)
        pet = get_pet(db, child_id)
        if pet is None:
            raise HTTPException(status_code=404, detail="Pet not found")
        return {
            "pet": pet,
            "inventory": inventory_for_child(db, child_id),
            "next_level_xp": pet["level"] * 100,
        }


@app.get("/api/adventure/today")
def get_today_adventure(child_id: int) -> dict[str, Any]:
    with get_db() as db:
        return adventure_response(db, child_id)


@app.post("/api/adventure/walk")
def report_walk(payload: WalkReport) -> dict[str, Any]:
    with get_db() as db:
        require_child(db, payload.child_id)
        settings = row_to_dict(
            db.execute("SELECT * FROM guardian_settings WHERE child_id = ?", (payload.child_id,)).fetchone()
        )
        if not settings or not settings["outdoor_enabled"]:
            raise HTTPException(status_code=403, detail="Outdoor adventure is disabled by guardian")

        adventure = ensure_adventure_day(db, payload.child_id)
        before_distance = int(adventure["distance_meters"])
        after_distance = before_distance + payload.distance_delta_meters
        if after_distance > int(settings["max_daily_distance"]):
            raise HTTPException(status_code=400, detail="Daily distance exceeds guardian limit")

        new_energy = after_distance // 100 - before_distance // 100
        new_plant_chances = after_distance // 250 - before_distance // 250
        new_animal_chances = after_distance // 500 - before_distance // 500
        activity_delta = estimate_activity(
            payload.distance_delta_meters,
            payload.steps_delta,
            payload.active_minutes_delta,
        )

        db.execute(
            """
            UPDATE adventure_day
            SET distance_meters = ?,
                steps = steps + ?,
                active_minutes = active_minutes + ?,
                estimated_kcal = estimated_kcal + ?,
                activity_energy = activity_energy + ?,
                exploration_energy = exploration_energy + ?,
                plant_chances = plant_chances + ?,
                animal_chances = animal_chances + ?
            WHERE child_id = ? AND day = ?
            """,
            (
                after_distance,
                activity_delta["steps"],
                activity_delta["active_minutes"],
                activity_delta["estimated_kcal"],
                activity_delta["activity_energy"],
                new_energy,
                new_plant_chances,
                new_animal_chances,
                payload.child_id,
                today(),
            ),
        )
        response = adventure_response(db, payload.child_id)
        response["unlocked"] = {
            "exploration_energy": new_energy,
            "plant_chances": new_plant_chances,
            "animal_chances": new_animal_chances,
            "activity_energy": activity_delta["activity_energy"],
            "steps": activity_delta["steps"],
            "active_minutes": activity_delta["active_minutes"],
            "estimated_kcal": activity_delta["estimated_kcal"],
        }
        return response


@app.post("/api/scan/plant")
def scan_plant(payload: PlantScan) -> dict[str, Any]:
    with get_db() as db:
        require_child(db, payload.child_id)
        adventure = ensure_adventure_day(db, payload.child_id)
        if adventure["plant_chances"] <= 0:
            raise HTTPException(status_code=400, detail="No plant discovery chance available")

        scan_count = db.execute(
            "SELECT COUNT(*) AS count FROM scan_log WHERE child_id = ?",
            (payload.child_id,),
        ).fetchone()["count"]
        plant = choose_plant(scan_count, payload.image_name)

        db.execute(
            """
            INSERT INTO encyclopedia_entry
            (child_id, entry_type, entry_key, name, category, knowledge, safety_tip, count)
            VALUES (?, 'plant', ?, ?, ?, ?, ?, 1)
            ON CONFLICT(child_id, entry_type, entry_key)
            DO UPDATE SET count = count + 1, last_seen = CURRENT_TIMESTAMP
            """,
            (
                payload.child_id,
                plant.key,
                plant.name,
                plant.category,
                plant.knowledge,
                plant.safety_tip,
            ),
        )
        add_inventory(db, payload.child_id, plant.food_key, plant.food_name, "food", 1)
        db.execute(
            """
            INSERT INTO scan_log (child_id, plant_key, plant_name, food_key, food_name, xp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (payload.child_id, plant.key, plant.name, plant.food_key, plant.food_name, plant.xp),
        )
        db.execute(
            """
            UPDATE adventure_day
            SET plant_chances = plant_chances - 1, xp = xp + ?
            WHERE child_id = ? AND day = ?
            """,
            (plant.xp, payload.child_id, today()),
        )
        add_pet_xp(db, payload.child_id, plant.xp)

        return {
            "recognition": {
                "type": "mock",
                "plant_key": plant.key,
                "name": plant.name,
                "category": plant.category,
                "confidence": plant.confidence,
            },
            "knowledge_card": {
                "knowledge": plant.knowledge,
                "safety_tip": plant.safety_tip,
            },
            "drops": [{"item_key": plant.food_key, "item_name": plant.food_name, "quantity": 1}],
            "adventure": adventure_response(db, payload.child_id),
        }


@app.post("/api/discovery/animal-clue")
def discover_animal_clue(payload: AnimalClueDiscover) -> dict[str, Any]:
    with get_db() as db:
        require_child(db, payload.child_id)
        settings = row_to_dict(
            db.execute("SELECT * FROM guardian_settings WHERE child_id = ?", (payload.child_id,)).fetchone()
        )
        if not settings or not settings["animal_clues_enabled"]:
            raise HTTPException(status_code=403, detail="Animal clues are disabled by guardian")

        adventure = ensure_adventure_day(db, payload.child_id)
        if adventure["animal_chances"] <= 0:
            raise HTTPException(status_code=400, detail="No animal clue chance available")

        clue_count = db.execute(
            "SELECT COUNT(*) AS count FROM animal_clue_log WHERE child_id = ?",
            (payload.child_id,),
        ).fetchone()["count"]
        clue = choose_animal(clue_count)

        existing = row_to_dict(
            db.execute(
                """
                SELECT friendship
                FROM encyclopedia_entry
                WHERE child_id = ? AND entry_type = 'animal' AND entry_key = ?
                """,
                (payload.child_id, clue.key),
            ).fetchone()
        )
        current_friendship = int(existing["friendship"]) if existing else 0
        new_friendship = min(100, current_friendship + clue.friendship)
        adopted = 1 if new_friendship >= 100 else 0

        db.execute(
            """
            INSERT INTO encyclopedia_entry
            (child_id, entry_type, entry_key, name, category, knowledge, safety_tip, count, friendship, adopted)
            VALUES (?, 'animal', ?, ?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(child_id, entry_type, entry_key)
            DO UPDATE SET
                count = count + 1,
                friendship = ?,
                adopted = ?,
                last_seen = CURRENT_TIMESTAMP
            """,
            (
                payload.child_id,
                clue.key,
                clue.name,
                clue.category,
                clue.knowledge,
                clue.safety_tip,
                new_friendship,
                adopted,
                new_friendship,
                adopted,
            ),
        )
        db.execute(
            """
            INSERT INTO animal_clue_log (child_id, animal_key, animal_name, friendship_added, xp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (payload.child_id, clue.key, clue.name, clue.friendship, clue.xp),
        )
        db.execute(
            """
            UPDATE adventure_day
            SET animal_chances = animal_chances - 1, xp = xp + ?
            WHERE child_id = ? AND day = ?
            """,
            (clue.xp, payload.child_id, today()),
        )
        add_pet_xp(db, payload.child_id, clue.xp)

        return {
            "animal_clue": {
                "animal_key": clue.key,
                "name": clue.name,
                "category": clue.category,
                "rarity": clue.rarity,
                "friendship": new_friendship,
                "adopted": bool(adopted),
                "favorite": clue.favorite,
                "habitat": clue.habitat,
                "greeting": clue.greeting,
                "friendship_to_adopt": max(0, 100 - new_friendship),
            },
            "knowledge_card": {
                "knowledge": clue.knowledge,
                "safety_tip": clue.safety_tip,
            },
            "adventure": adventure_response(db, payload.child_id),
        }


@app.post("/api/animal/interact")
def interact_with_animal(payload: AnimalInteract) -> dict[str, Any]:
    with get_db() as db:
        require_child(db, payload.child_id)
        interaction = ANIMAL_INTERACTIONS.get(payload.action)
        if interaction is None:
            raise HTTPException(status_code=400, detail="Unsupported animal interaction")

        animal = animal_by_key(payload.animal_key)
        if animal is None:
            raise HTTPException(status_code=404, detail="Animal is not in catalog")

        entry = row_to_dict(
            db.execute(
                """
                SELECT *
                FROM encyclopedia_entry
                WHERE child_id = ? AND entry_type = 'animal' AND entry_key = ?
                """,
                (payload.child_id, payload.animal_key),
            ).fetchone()
        )
        if entry is None:
            raise HTTPException(status_code=400, detail="Discover this animal clue before interacting")

        friendship_added = int(interaction["friendship"])
        new_friendship = min(100, int(entry["friendship"]) + friendship_added)
        adopted = 1 if new_friendship >= 100 else 0
        xp = int(interaction["xp"])

        db.execute(
            """
            UPDATE encyclopedia_entry
            SET friendship = ?,
                adopted = ?,
                last_seen = CURRENT_TIMESTAMP
            WHERE child_id = ? AND entry_type = 'animal' AND entry_key = ?
            """,
            (new_friendship, adopted, payload.child_id, payload.animal_key),
        )
        db.execute(
            """
            INSERT INTO animal_interaction_log
            (child_id, animal_key, animal_name, action, friendship_added, xp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (payload.child_id, animal.key, animal.name, payload.action, friendship_added, xp),
        )
        change_adventure_xp(db, payload.child_id, xp)
        add_pet_xp(db, payload.child_id, xp)

        updated = row_to_dict(
            db.execute(
                """
                SELECT entry_type, entry_key, name, category, knowledge, safety_tip,
                       count, friendship, adopted, first_seen, last_seen
                FROM encyclopedia_entry
                WHERE child_id = ? AND entry_type = 'animal' AND entry_key = ?
                """,
                (payload.child_id, payload.animal_key),
            ).fetchone()
        )
        enriched = enriched_animals([updated])[0] if updated else {}
        return {
            "animal": enriched,
            "interaction": {
                "action": payload.action,
                "label": interaction["label"],
                "friendship_added": friendship_added,
                "xp": xp,
                "message": interaction["message"],
            },
            "safety_tip": "只做远距离观察和虚拟互动，不触摸、不追赶、不投喂真实动物。",
            "adventure": adventure_response(db, payload.child_id),
        }


@app.post("/api/pet/feed")
def feed_pet(payload: FeedPet) -> dict[str, Any]:
    with get_db() as db:
        require_child(db, payload.child_id)
        pet = get_pet(db, payload.child_id)
        if pet is None:
            raise HTTPException(status_code=404, detail="Pet not found")
        item = row_to_dict(
            db.execute(
                """
                SELECT *
                FROM inventory_item
                WHERE child_id = ? AND item_key = ? AND quantity > 0
                """,
                (payload.child_id, payload.food_key),
            ).fetchone()
        )
        if item is None:
            raise HTTPException(status_code=400, detail="Food is not available")
        effect = FOOD_EFFECTS.get(payload.food_key)
        if effect is None:
            raise HTTPException(status_code=400, detail="Item cannot be used as food")

        db.execute(
            """
            UPDATE inventory_item
            SET quantity = quantity - 1
            WHERE child_id = ? AND item_key = ?
            """,
            (payload.child_id, payload.food_key),
        )
        db.execute(
            """
            UPDATE pet
            SET hunger = MIN(100, hunger + ?),
                mood = MIN(100, mood + ?),
                bond = MIN(100, bond + ?)
            WHERE child_id = ?
            """,
            (effect["hunger"], effect["mood"], effect["bond"], payload.child_id),
        )
        db.execute(
            """
            INSERT INTO feed_log (child_id, pet_id, food_key, food_name, xp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (payload.child_id, pet["id"], payload.food_key, item["item_name"], effect["xp"]),
        )
        change_adventure_xp(db, payload.child_id, effect["xp"])
        updated_pet = add_pet_xp(db, payload.child_id, effect["xp"])

        return {
            "pet": updated_pet,
            "used_food": {"item_key": payload.food_key, "item_name": item["item_name"]},
            "effect": effect,
            "adventure": adventure_response(db, payload.child_id),
        }


@app.get("/api/encyclopedia/me")
def encyclopedia(child_id: int) -> dict[str, Any]:
    with get_db() as db:
        require_child(db, child_id)
        rows = db.execute(
            """
            SELECT entry_type, entry_key, name, category, knowledge, safety_tip,
                   count, friendship, adopted, first_seen, last_seen
            FROM encyclopedia_entry
            WHERE child_id = ?
            ORDER BY entry_type, name
            """,
            (child_id,),
        ).fetchall()
        entries = [dict(row) for row in rows]
        plants = [entry for entry in entries if entry["entry_type"] == "plant"]
        animals = enriched_animals([entry for entry in entries if entry["entry_type"] == "animal"])
        return {
            "child_id": child_id,
            "plants": plants,
            "animals": animals,
        }


@app.get("/api/parent/summary/today")
def parent_summary_today(child_id: int) -> dict[str, Any]:
    with get_db() as db:
        child = require_child(db, child_id)
        settings = get_guardian_settings(db, child_id)
        adventure = adventure_response(db, child_id)
        pet = get_pet(db, child_id)
        encyclopedia_data = encyclopedia(child_id)
        animals = encyclopedia_data["animals"]
        counts = progress_counts(db, child_id)
        learned = [entry["name"] for entry in encyclopedia_data["plants"][-3:]]
        learned.extend(entry["name"] for entry in animals[-2:])
        next_action = next_action_for(adventure, animals)
        return {
            "child": {"id": child["id"], "name": child["name"], "age": child["age"]},
            "day": today(),
            "outdoor": {
                "distance_meters": adventure["distance_meters"],
                "steps": adventure["activity"]["steps"],
                "active_minutes": adventure["activity"]["active_minutes"],
                "estimated_kcal": adventure["activity"]["estimated_kcal"],
                "activity_energy": adventure["activity"]["activity_energy"],
                "exploration_energy": adventure["exploration_energy"],
                "goal_meters": settings["daily_distance_goal"],
            },
            "adventure": {
                "chapter": adventure["chapter"],
                "stage": adventure["stage"],
                "completed": adventure["completed"],
                "tasks": adventure["tasks"],
                "xp": adventure["xp"],
            },
            "discoveries": {
                "plant_scan_count": counts["plant_scans"],
                "animal_clue_count": counts["animal_clues"],
                "animal_interaction_count": counts["animal_interactions"],
                "plants": [entry["name"] for entry in encyclopedia_data["plants"]],
                "animals": [
                    {
                        "name": entry["name"],
                        "friendship": entry["friendship"],
                        "adopted": bool(entry["adopted"]),
                        "favorite": entry["favorite"],
                        "habitat": entry["habitat"],
                        "friendship_to_adopt": entry["friendship_to_adopt"],
                    }
                    for entry in animals
                ],
            },
            "pet": pet,
            "today_value": {
                "worth_it": (
                    adventure["distance_meters"] > 0
                    or adventure["activity"]["active_minutes"] > 0
                    or counts["plant_scans"] > 0
                    or counts["animal_clues"] > 0
                ),
                "learned": learned,
                "next_action": next_action,
                "suggestion": (
                    "今日闭环已完成，可以把重点放在复盘孩子观察到的知识点。"
                    if adventure["completed"]
                    else next_action
                ),
            },
            "safety_notes": [
                "本版本不指定现实目的地，不做路线导航。",
                "动物发现只用于远距离观察和虚拟领养，不鼓励触摸、追赶或投喂。",
            ],
        }


@app.get("/api/parent/settings")
def parent_settings(child_id: int) -> dict[str, Any]:
    with get_db() as db:
        require_child(db, child_id)
        settings = get_guardian_settings(db, child_id)
        return {
            "child_id": child_id,
            "outdoor_enabled": bool(settings["outdoor_enabled"]),
            "animal_clues_enabled": bool(settings["animal_clues_enabled"]),
            "daily_distance_goal": settings["daily_distance_goal"],
            "max_daily_distance": settings["max_daily_distance"],
        }


@app.post("/api/parent/settings")
def update_parent_settings(payload: GuardianSettingsUpdate) -> dict[str, Any]:
    with get_db() as db:
        require_child(db, payload.child_id)
        db.execute(
            """
            UPDATE guardian_settings
            SET outdoor_enabled = ?,
                animal_clues_enabled = ?,
                daily_distance_goal = ?,
                max_daily_distance = ?
            WHERE child_id = ?
            """,
            (
                1 if payload.outdoor_enabled else 0,
                1 if payload.animal_clues_enabled else 0,
                payload.daily_distance_goal,
                payload.max_daily_distance,
                payload.child_id,
            ),
        )
        settings = get_guardian_settings(db, payload.child_id)
        return {
            "child_id": payload.child_id,
            "outdoor_enabled": bool(settings["outdoor_enabled"]),
            "animal_clues_enabled": bool(settings["animal_clues_enabled"]),
            "daily_distance_goal": settings["daily_distance_goal"],
            "max_daily_distance": settings["max_daily_distance"],
        }


@app.get("/api/catalog")
def catalog() -> dict[str, Any]:
    return {
        "plants": [plant.__dict__ for plant in PLANTS],
        "animal_clues": [clue.__dict__ for clue in ANIMAL_CLUES],
    }
