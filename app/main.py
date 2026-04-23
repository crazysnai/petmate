from __future__ import annotations

from datetime import date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException

from app.catalog import (
    ANIMAL_CLUES,
    ANIMAL_DAILY_REQUESTS,
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
LOCAL_TZ = ZoneInfo("Asia/Shanghai")
LIFE_STAGE_RULES = [
    (0, 100, "初遇", "保持距离观察，认识它喜欢的环境。"),
    (100, 400, "熟悉", "伙伴开始记住你的问候，可以解锁更多互动。"),
    (400, 1000, "同行", "伙伴愿意陪你完成探险，留下更完整的自然记忆。"),
    (1000, 10_000_000, "远行准备", "伙伴长大了，正在准备回到更广阔的自然。"),
]
ANIMAL_KEEPSAKES = {
    "sparrow": "屋檐歌声羽章",
    "butterfly": "花间飞行贴纸",
    "snail": "安静小路徽记",
}
ANIMAL_PERSONALITIES = {
    "sparrow": {
        "trait": "活泼",
        "voice": "短促、轻快，喜欢回应问候。",
        "scene": "它跳到远处的栏杆上，歪着头看你。",
    },
    "butterfly": {
        "trait": "好奇",
        "voice": "轻柔、喜欢植物和颜色。",
        "scene": "它绕着花丛飞了一圈，又停在一片叶子旁。",
    },
    "snail": {
        "trait": "慢热",
        "voice": "安静、慢慢回应，喜欢稳定的陪伴。",
        "scene": "它慢慢探出触角，在湿润的叶片旁停下。",
    },
}


@app.on_event("startup")
def startup() -> None:
    init_db()


def today() -> str:
    return datetime.now(LOCAL_TZ).date().isoformat()


def local_now() -> datetime:
    return datetime.now(LOCAL_TZ)


def parse_hhmm(value: str, fallback: str) -> time:
    try:
        hour, minute = [int(part) for part in str(value).split(":", 1)]
        return time(hour=hour, minute=minute)
    except (ValueError, TypeError):
        hour, minute = [int(part) for part in fallback.split(":", 1)]
        return time(hour=hour, minute=minute)


def time_in_range(current: time, start: time, end: time) -> bool:
    if start <= end:
        return start <= current < end
    return current >= start or current < end


def rhythm_response(settings: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    current = now or local_now()
    current_time = current.time()
    sleep_start = parse_hhmm(settings.get("sleep_start", "21:00"), "21:00")
    sleep_end = parse_hhmm(settings.get("sleep_end", "07:00"), "07:00")
    study_start = parse_hhmm(settings.get("study_start", "08:00"), "08:00")
    study_end = parse_hhmm(settings.get("study_end", "17:00"), "17:00")
    is_sleep = time_in_range(current_time, sleep_start, sleep_end)
    is_study = bool(settings.get("study_mode_enabled", 1)) and current.weekday() < 5 and time_in_range(
        current_time, study_start, study_end
    )

    if is_sleep:
        return {
            "state": "sleep",
            "label": "伙伴睡觉中",
            "can_interact": False,
            "can_adventure": False,
            "can_feed": False,
            "can_review": True,
            "child_message": "伙伴和豆豆已经睡了。今天的发现已经保存，明天醒来还能继续。",
            "parent_message": "当前为睡眠时段，孩子端不允许消耗能量或唤醒伙伴。",
        }
    if is_study:
        return {
            "state": "study",
            "label": "学习安静模式",
            "can_interact": False,
            "can_adventure": False,
            "can_feed": False,
            "can_review": True,
            "child_message": "伙伴先安静陪你学习。放学后再一起探险。",
            "parent_message": "当前为工作日学习时段，孩子端保留图鉴和回忆，弱化互动入口。",
        }
    return {
        "state": "free",
        "label": "可探险",
        "can_interact": True,
        "can_adventure": True,
        "can_feed": True,
        "can_review": True,
        "child_message": "现在可以适度探险和互动，记得保持安全距离。",
        "parent_message": "当前不在睡眠或学习时段，可以进行户外探险与伙伴互动。",
    }


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


def clamp_stat(value: int) -> int:
    return max(0, min(100, value))


def request_for_animal(animal_key: str, adventure: dict[str, Any], counts: dict[str, int]) -> dict[str, Any]:
    request = ANIMAL_DAILY_REQUESTS.get(
        animal_key,
        {"title": "想一起完成一次互动", "hint": "今天和伙伴互动 1 次后，它会留下新的记忆。"},
    )
    if animal_key == "sparrow":
        current = min(counts["plant_scans"], 1)
        target = 1
    elif animal_key == "butterfly":
        current = min(int(adventure["active_minutes"]), 5)
        target = 5
    elif animal_key == "snail":
        current = min(int(adventure["distance_meters"]), 300)
        target = 300
    else:
        current = min(counts["animal_interactions"], 1)
        target = 1
    return {
        "title": request["title"],
        "hint": request["hint"],
        "current": current,
        "target": target,
        "completed": current >= target,
        "reward": "愿望完成：下一次互动会留下更完整的伙伴故事。",
        "reward_status": "可触发" if current >= target else "未完成",
    }


def daily_event_for_animal(animal: dict[str, Any], request: dict[str, Any], adventure: dict[str, Any]) -> dict[str, Any]:
    animal_key = animal.get("entry_key", "")
    completed = bool(request.get("completed"))
    if animal_key == "sparrow":
        title = "风里的小伞"
        scene = "麻雀看到草地上有会飞的小种子，想知道今天有没有新的植物。"
        complete_text = "麻雀把你的植物发现记成一段轻快的歌。"
        badge_hint = "适合推进植物观察和图鉴徽章。"
    elif animal_key == "butterfly":
        title = "花间颜色信"
        scene = "蝴蝶在花和叶之间绕了一圈，想找一种今天最特别的颜色。"
        complete_text = "蝴蝶留下了一句关于颜色和花蜜的小秘密。"
        badge_hint = "适合推进活动分钟和植物观察徽章。"
    elif animal_key == "snail":
        title = "慢慢路上的痕迹"
        scene = "蜗牛喜欢安静湿润的小路，想让你慢慢走一段再回来。"
        complete_text = "蜗牛把今天的路线记在叶片旁边。"
        badge_hint = "适合推进 500m 启程和活动徽章。"
    else:
        title = "今天的小发现"
        scene = "伙伴在安全距离外等你带回一个自然观察。"
        complete_text = "伙伴记住了今天的陪伴。"
        badge_hint = "适合推进伙伴互动徽章。"

    return {
        "title": title,
        "scene": scene,
        "wish_title": request.get("title", "完成一个小观察"),
        "wish_progress": f"{request.get('current', 0)} / {request.get('target', 1)}",
        "completed": completed,
        "complete_text": complete_text if completed else "完成愿望后会解锁伙伴的一句今日反馈。",
        "reward": request.get("reward", "完成后伙伴会留下新的故事线索。"),
        "badge_hint": badge_hint,
        "safety_tip": "只观察和记录，不触摸、不追赶、不投喂真实动物。",
        "next_action": (
            "现在可以用活动能量和伙伴互动，听听它的今日反馈。"
            if completed and int(adventure.get("activity_energy", 0)) > 0
            else request.get("hint", "继续完成今天的小观察。")
        ),
    }


def passport_for_child(db, child_id: int, adventure: dict[str, Any], counts: dict[str, int]) -> dict[str, Any]:
    plant_total = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM encyclopedia_entry
        WHERE child_id = ? AND entry_type = 'plant'
        """,
        (child_id,),
    ).fetchone()["count"]
    animal_total = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM encyclopedia_entry
        WHERE child_id = ? AND entry_type = 'animal'
        """,
        (child_id,),
    ).fetchone()["count"]
    adopted_total = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM encyclopedia_entry
        WHERE child_id = ? AND entry_type = 'animal' AND adopted = 1
        """,
        (child_id,),
    ).fetchone()["count"]
    all_interactions = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM animal_interaction_log
        WHERE child_id = ?
        """,
        (child_id,),
    ).fetchone()["count"]
    badges = [
        {
            "key": "first_500m",
            "title": "500m 启程章",
            "category": "户外",
            "description": "用真实步行解锁完整观察机会。",
            "current": min(int(adventure["distance_meters"]), 500),
            "target": 500,
            "completed": int(adventure["distance_meters"]) >= 500,
        },
        {
            "key": "two_plants_today",
            "title": "植物观察章",
            "category": "植物",
            "description": "今天扫描 2 种植物，获得可喂养食材。",
            "current": min(counts["plant_scans"], 2),
            "target": 2,
            "completed": counts["plant_scans"] >= 2,
        },
        {
            "key": "animal_clue_today",
            "title": "动物线索章",
            "category": "动物",
            "description": "发现 1 个动物线索，只做远距离观察。",
            "current": min(counts["animal_clues"], 1),
            "target": 1,
            "completed": counts["animal_clues"] >= 1,
        },
        {
            "key": "plant_collector",
            "title": "三种植物图鉴章",
            "category": "图鉴",
            "description": "累计认识 3 种身边植物。",
            "current": min(plant_total, 3),
            "target": 3,
            "completed": plant_total >= 3,
        },
        {
            "key": "partner_chat",
            "title": "三次伙伴互动章",
            "category": "伙伴",
            "description": "用活动能量换取伙伴故事反馈。",
            "current": min(all_interactions, 3),
            "target": 3,
            "completed": all_interactions >= 3,
        },
        {
            "key": "active_minutes",
            "title": "10 分钟活动章",
            "category": "运动",
            "description": "累计完成 10 分钟户外活动。",
            "current": min(int(adventure["active_minutes"]), 10),
            "target": 10,
            "completed": int(adventure["active_minutes"]) >= 10,
        },
        {
            "key": "feed_once",
            "title": "第一次喂养章",
            "category": "宠物",
            "description": "用植物发现获得的食材喂养主宠物。",
            "current": min(counts["feeds"], 1),
            "target": 1,
            "completed": counts["feeds"] >= 1,
        },
        {
            "key": "adopt_partner",
            "title": "第一位同行伙伴章",
            "category": "伙伴",
            "description": "把一位动物伙伴友好度提升到 100。",
            "current": min(adopted_total, 1),
            "target": 1,
            "completed": adopted_total >= 1,
        },
    ]
    completed_count = sum(1 for badge in badges if badge["completed"])
    if completed_count >= 5:
        level = "自然探险家"
    elif completed_count >= 3:
        level = "草地记录员"
    else:
        level = "见习观察员"
    next_badge = next((badge for badge in badges if not badge["completed"]), None)
    return {
        "level": level,
        "completed_badges": completed_count,
        "total_badges": len(badges),
        "plant_total": plant_total,
        "animal_total": animal_total,
        "badges": badges,
        "next_badge": next_badge,
    }


def home_display_for_animal(animal: dict[str, Any]) -> dict[str, Any]:
    home_level = int(animal.get("home_level", 1))
    favorite = animal.get("favorite") or "自然食材"
    habitat = animal.get("habitat") or "安全户外区域"
    decorations = [
        {"name": "叶片地垫", "source": "第一次发现线索", "unlocked": home_level >= 1},
        {"name": f"{favorite}小碟", "source": "分享食材", "unlocked": home_level >= 2},
        {"name": "安静观察角", "source": "观察互动", "unlocked": home_level >= 3},
        {"name": f"{habitat}背景", "source": "小探险记忆", "unlocked": home_level >= 4},
        {"name": "纪念物展示台", "source": "长期陪伴", "unlocked": home_level >= 5},
    ]
    unlocked = [item for item in decorations if item["unlocked"]]
    next_item = next((item for item in decorations if not item["unlocked"]), None)
    return {
        "level": home_level,
        "theme": f"{habitat}小窝",
        "decorations": decorations,
        "unlocked_count": len(unlocked),
        "total_count": len(decorations),
        "next_decoration": next_item,
        "note": "小窝装饰由探险和互动自动解锁，当前版本先展示，不做复杂编辑。",
    }


def story_for_animal(animal: dict[str, Any]) -> dict[str, Any]:
    care_state = animal.get("care_state") or care_state_for(animal, animal["entry_key"])
    growth_points = int(animal.get("growth_points", 0))
    friendship = int(animal.get("friendship", 0))
    trust = int(animal.get("trust", 20))
    memory = animal.get("memory") or ""
    chapters = [
        {
            "title": "第一次相遇",
            "completed": int(animal.get("count", 1)) >= 1,
            "hint": "发现一次动物线索。",
        },
        {
            "title": "记住你的方式",
            "completed": friendship >= 50 or trust >= 35,
            "hint": "用观察、问候和分享食材建立信任。",
        },
        {
            "title": "成为同行伙伴",
            "completed": bool(animal.get("adopted")),
            "hint": "友好度达到 100 后进入家园陪伴。",
        },
        {
            "title": "一段自然回忆",
            "completed": growth_points >= 400 and bool(memory),
            "hint": "继续互动，积累成长点和共同记忆。",
        },
        {
            "title": "留下纪念物",
            "completed": care_state["state"] == "returned_to_nature",
            "hint": "伙伴未来回到自然时，图鉴会保留名字、记忆和纪念物。",
        },
    ]
    completed_count = sum(1 for chapter in chapters if chapter["completed"])
    current = next((chapter for chapter in chapters if not chapter["completed"]), chapters[-1])
    return {
        "completed_chapters": completed_count,
        "total_chapters": len(chapters),
        "current_title": current["title"],
        "next_hint": current["hint"],
        "chapters": chapters,
    }


def parse_sqlite_date(value: Any) -> date:
    if not value:
        return today_date()
    text = str(value).replace("T", " ")
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return today_date()


def today_date() -> date:
    return local_now().date()


def days_since(value: Any) -> int:
    return max(0, (today_date() - parse_sqlite_date(value)).days)


def life_stage_for(growth_points: int) -> dict[str, Any]:
    for lower, upper, label, science in LIFE_STAGE_RULES:
        if lower <= growth_points < upper:
            next_target = upper if upper < 10_000_000 else None
            return {
                "label": label,
                "growth_points": growth_points,
                "next_target": next_target,
                "science": science,
            }
    return {
        "label": "远行准备",
        "growth_points": growth_points,
        "next_target": None,
        "science": "伙伴长大了，正在准备回到更广阔的自然。",
    }


def care_state_for(entry: dict[str, Any], animal_key: str) -> dict[str, Any]:
    inactive_days = days_since(entry.get("last_seen"))
    mood = int(entry.get("mood", 50))
    trust = int(entry.get("trust", 20))
    keepsake = entry.get("keepsake") or ANIMAL_KEEPSAKES.get(animal_key, "自然回忆徽章")

    if inactive_days >= 30:
        return {
            "state": "returned_to_nature",
            "label": "回到自然",
            "severity": "away",
            "reason": "它已经很久没有和你相遇，先回到熟悉的自然环境生活。",
            "recovery_hint": "重新走 500 米并发现动物线索，就有机会再次遇见它。",
            "can_interact": False,
            "keepsake": keepsake,
        }
    if inactive_days >= 10 or mood < 20 or trust < 15:
        return {
            "state": "resting",
            "label": "自然休养",
            "severity": "resting",
            "reason": "它需要安静一阵子，暂时保持距离。",
            "recovery_hint": "完成 300 米轻松步行、扫描 1 种植物，再用观察或打招呼慢慢恢复。",
            "can_interact": True,
            "keepsake": keepsake,
        }
    if inactive_days >= 3 or mood < 40 or trust < 25:
        return {
            "state": "quiet",
            "label": "有点安静",
            "severity": "warning",
            "reason": "它最近互动较少，正在远处观察你。",
            "recovery_hint": "一次安静观察或分享食材可以让它放松。",
            "can_interact": True,
            "keepsake": keepsake,
        }
    return {
        "state": "home",
        "label": "陪伴中",
        "severity": "ok",
        "reason": "状态稳定，适合继续探险和互动。",
        "recovery_hint": "继续用活动能量和它留下新记忆。",
        "can_interact": True,
        "keepsake": keepsake,
    }


def latest_plant_name(db, child_id: int) -> str | None:
    row = row_to_dict(
        db.execute(
            """
            SELECT plant_name
            FROM scan_log
            WHERE child_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (child_id,),
        ).fetchone()
    )
    return row["plant_name"] if row else None


def next_suggestion_for_interaction(adventure: dict[str, Any], counts: dict[str, int]) -> str:
    if adventure["plant_chances"] > 0:
        return "还有植物机会，可以去扫描一种今天看到的植物。"
    if adventure["animal_chances"] > 0:
        return "还有动物线索机会，可以保持距离寻找新的线索。"
    if counts["feeds"] == 0:
        return "如果背包里有食材，可以回家园喂一次主宠物。"
    return "再走 250 米可以换来新的植物发现机会。"


def science_link_for(animal_key: str, action: str, latest_plant: str | None) -> str:
    if latest_plant:
        return f"它记住了你今天发现的{latest_plant}，这会变成你们共同的自然记忆。"
    if animal_key == "sparrow":
        return "麻雀常在灌木和屋檐附近活动，远距离观察比投喂更安全。"
    if animal_key == "butterfly":
        return "蝴蝶和植物关系很密切，观察花和叶能帮助理解传粉。"
    if animal_key == "snail":
        return "蜗牛喜欢潮湿环境，慢慢观察能看到它留下的移动痕迹。"
    return "自然伙伴适合观察和记录，不适合触摸或追赶。"


def partner_line_for(animal_key: str, action: str, mood: int, trust: int, curiosity: int, latest_plant: str | None) -> str:
    plant_text = f"我还记得你发现的{latest_plant}。" if latest_plant else "我想看看你今天的新发现。"
    if animal_key == "sparrow":
        if mood >= 70:
            return f"啾，我在这儿。{plant_text}"
        if trust < 30:
            return "我会站远一点看你，慢慢熟悉就好。"
        return "我听见你的声音了，今天也一起观察吧。"
    if animal_key == "butterfly":
        if curiosity >= 70:
            return f"那片叶子的颜色真特别，{plant_text}"
        if action == "share_food":
            return "谢谢你讲给我听，植物的味道像一段小故事。"
        return "我会跟着风飞一小段，你也慢慢看。"
    if animal_key == "snail":
        if trust < 30:
            return "我还需要一点时间，慢慢来就很好。"
        if action == "mini_adventure":
            return "这次小探险不需要很快，稳稳走就可以。"
        return "我把今天的路记在叶片旁边了。"
    return "我记住了今天的陪伴。"


def generate_partner_feedback(
    db,
    child_id: int,
    animal_key: str,
    action: str,
    updated_animal: dict[str, Any],
    adventure: dict[str, Any],
    counts: dict[str, int],
) -> dict[str, Any]:
    personality = ANIMAL_PERSONALITIES.get(
        animal_key,
        {"trait": "温和", "voice": "安静回应", "scene": "伙伴在安全距离外看着你。"},
    )
    latest_plant = latest_plant_name(db, child_id)
    mood = int(updated_animal.get("mood", 50))
    trust = int(updated_animal.get("trust", 20))
    curiosity = int(updated_animal.get("curiosity", 40))
    care_state = updated_animal.get("care_state") or care_state_for(updated_animal, animal_key)
    life_stage = updated_animal.get("life_stage") or life_stage_for(int(updated_animal.get("growth_points", 0)))
    emotion = "开心" if mood >= 70 else "安心" if trust >= 45 else "谨慎" if care_state["state"] != "home" else "好奇"
    return {
        "personality": personality["trait"],
        "voice": personality["voice"],
        "scene": personality["scene"],
        "partner_line": partner_line_for(animal_key, action, mood, trust, curiosity, latest_plant),
        "emotion": emotion,
        "science_link": science_link_for(animal_key, action, latest_plant),
        "next_suggestion": next_suggestion_for_interaction(adventure, counts),
        "life_stage": life_stage["label"],
        "care_label": care_state["label"],
    }


def enriched_animals(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for entry in entries:
        animal = animal_by_key(entry["entry_key"])
        growth_points = int(entry.get("growth_points", 0))
        care_state = care_state_for(entry, entry["entry_key"])
        life_stage = life_stage_for(growth_points)
        if care_state["state"] == "returned_to_nature":
            life_stage = {
                **life_stage,
                "label": "回到自然",
                "science": "自然朋友拥有自己的生活。它留下回忆，也可能在未来重新出现。",
            }
        enriched.append(
            {
                **entry,
                "favorite": animal.favorite if animal else "自然食材",
                "habitat": animal.habitat if animal else "安全户外区域",
                "greeting": animal.greeting if animal else "伙伴回应了你的观察。",
                "friendship_to_adopt": max(0, 100 - int(entry["friendship"])),
                "mood": int(entry.get("mood", 50)),
                "trust": int(entry.get("trust", 20)),
                "curiosity": int(entry.get("curiosity", 40)),
                "home_level": int(entry.get("home_level", 1)),
                "growth_points": growth_points,
                "life_stage": life_stage,
                "care_state": care_state,
                "away_state": care_state["state"],
                "away_reason": care_state["reason"],
                "keepsake": entry.get("keepsake") or care_state["keepsake"],
                "inactive_days": days_since(entry.get("last_seen")),
                "memory": entry.get("memory") or "还没有留下伙伴记忆。",
            }
        )
        enriched[-1]["home_display"] = home_display_for_animal(enriched[-1])
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


def build_adventure_tasks(adventure: dict[str, Any], walk_target: int, counts: dict[str, int]) -> list[dict[str, Any]]:
    return [
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


def finalize_adventure_completion(
    db,
    child_id: int,
    adventure: dict[str, Any] | None = None,
    counts: dict[str, int] | None = None,
) -> bool:
    adventure = adventure or ensure_adventure_day(db, child_id)
    counts = counts or progress_counts(db, child_id)
    settings = get_guardian_settings(db, child_id)
    tasks = build_adventure_tasks(adventure, int(settings["daily_distance_goal"]), counts)
    completed = all(task["completed"] for task in tasks if not task.get("optional"))
    if not completed or adventure["completed"]:
        return False

    cursor = db.execute(
        """
        UPDATE adventure_day
        SET completed = 1, reward_claimed = 1, xp = xp + 50
        WHERE child_id = ? AND day = ? AND completed = 0
        """,
        (child_id, today()),
    )
    if not cursor.rowcount:
        return False

    add_pet_xp(db, child_id, 50)
    return True


def adventure_response(db, child_id: int) -> dict[str, Any]:
    adventure = ensure_adventure_day(db, child_id)
    settings = get_guardian_settings(db, child_id)
    rhythm = rhythm_response(settings)
    walk_target = int(settings["daily_distance_goal"])
    counts = progress_counts(db, child_id)
    tasks = build_adventure_tasks(adventure, walk_target, counts)

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
        "rhythm": rhythm,
        "exploration_energy": adventure["exploration_energy"],
        "available_chances": {
            "plant": adventure["plant_chances"],
            "animal": adventure["animal_chances"],
        },
        "xp": adventure["xp"],
        "completed": bool(adventure["completed"]),
        "tasks": tasks,
        "passport": passport_for_child(db, child_id, adventure, counts),
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
        return {"child": child, "guardian_settings": settings, "rhythm": rhythm_response(settings)}


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
        rhythm = rhythm_response(settings)
        if not rhythm["can_adventure"]:
            raise HTTPException(status_code=403, detail=rhythm["child_message"])

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
        finalize_adventure_completion(db, payload.child_id)
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
        rhythm = rhythm_response(get_guardian_settings(db, payload.child_id))
        if not rhythm["can_adventure"]:
            raise HTTPException(status_code=403, detail=rhythm["child_message"])
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
        finalize_adventure_completion(db, payload.child_id)

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
        rhythm = rhythm_response(settings)
        if not rhythm["can_adventure"]:
            raise HTTPException(status_code=403, detail=rhythm["child_message"])
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
            (child_id, entry_type, entry_key, name, category, knowledge, safety_tip,
             count, friendship, mood, trust, curiosity, home_level, growth_points,
             away_state, away_reason, keepsake, away_at, memory, adopted)
            VALUES (?, 'animal', ?, ?, ?, ?, ?, 1, ?, 55, 25, 45, 1, ?, 'home', '', ?, NULL, ?, ?)
            ON CONFLICT(child_id, entry_type, entry_key)
            DO UPDATE SET
                count = count + 1,
                friendship = ?,
                mood = MAX(mood, 55),
                trust = MAX(trust, 25),
                curiosity = MAX(curiosity, 45),
                growth_points = growth_points + ?,
                away_state = 'home',
                away_reason = '',
                away_at = NULL,
                memory = ?,
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
                clue.friendship,
                ANIMAL_KEEPSAKES.get(clue.key, "自然回忆徽章"),
                clue.greeting,
                adopted,
                new_friendship,
                clue.friendship,
                clue.greeting,
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
        finalize_adventure_completion(db, payload.child_id)

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
        rhythm = rhythm_response(get_guardian_settings(db, payload.child_id))
        if not rhythm["can_interact"]:
            raise HTTPException(status_code=403, detail=rhythm["child_message"])
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
        current_care = care_state_for(entry, payload.animal_key)
        if not current_care["can_interact"]:
            raise HTTPException(status_code=400, detail=current_care["recovery_hint"])

        friendship_added = int(interaction["friendship"])
        energy_cost = int(interaction["energy_cost"])
        adventure = ensure_adventure_day(db, payload.child_id)
        if int(adventure["activity_energy"]) < energy_cost:
            raise HTTPException(status_code=400, detail=f"Activity energy is not enough. Need {energy_cost}.")

        new_friendship = min(100, int(entry["friendship"]) + friendship_added)
        new_mood = clamp_stat(int(entry.get("mood", 50)) + int(interaction.get("mood", 0)))
        new_trust = clamp_stat(int(entry.get("trust", 20)) + int(interaction.get("trust", 0)))
        new_curiosity = clamp_stat(int(entry.get("curiosity", 40)) + int(interaction.get("curiosity", 0)))
        new_home_level = min(5, int(entry.get("home_level", 1)) + int(interaction.get("home", 0)))
        xp = int(interaction["xp"])
        growth_added = friendship_added + xp
        new_growth_points = int(entry.get("growth_points", 0)) + growth_added
        adopted = 1 if new_friendship >= 100 else 0
        memory = str(interaction["memory"])

        db.execute(
            """
            UPDATE encyclopedia_entry
            SET friendship = ?,
                mood = ?,
                trust = ?,
                curiosity = ?,
                home_level = ?,
                growth_points = ?,
                away_state = 'home',
                away_reason = '',
                away_at = NULL,
                memory = ?,
                adopted = ?,
                last_seen = CURRENT_TIMESTAMP
            WHERE child_id = ? AND entry_type = 'animal' AND entry_key = ?
            """,
            (
                new_friendship,
                new_mood,
                new_trust,
                new_curiosity,
                new_home_level,
                new_growth_points,
                memory,
                adopted,
                payload.child_id,
                payload.animal_key,
            ),
        )
        db.execute(
            """
            UPDATE adventure_day
            SET activity_energy = MAX(0, activity_energy - ?)
            WHERE child_id = ? AND day = ?
            """,
            (energy_cost, payload.child_id, today()),
        )
        db.execute(
            """
            INSERT INTO animal_interaction_log
            (child_id, animal_key, animal_name, action, friendship_added, energy_cost, xp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (payload.child_id, animal.key, animal.name, payload.action, friendship_added, energy_cost, xp),
        )
        change_adventure_xp(db, payload.child_id, xp)
        add_pet_xp(db, payload.child_id, xp)
        finalize_adventure_completion(db, payload.child_id)

        updated = row_to_dict(
            db.execute(
                """
                SELECT entry_type, entry_key, name, category, knowledge, safety_tip,
                       count, friendship, mood, trust, curiosity, home_level,
                       growth_points, away_state, away_reason, keepsake, away_at,
                       memory, adopted, first_seen, last_seen
                FROM encyclopedia_entry
                WHERE child_id = ? AND entry_type = 'animal' AND entry_key = ?
                """,
                (payload.child_id, payload.animal_key),
            ).fetchone()
        )
        enriched = enriched_animals([updated])[0] if updated else {}
        response_adventure = adventure_response(db, payload.child_id)
        response_counts = progress_counts(db, payload.child_id)
        if enriched:
            enriched["daily_request"] = request_for_animal(
                enriched["entry_key"],
                ensure_adventure_day(db, payload.child_id),
                response_counts,
            )
            enriched["daily_event"] = daily_event_for_animal(
                enriched,
                enriched["daily_request"],
                ensure_adventure_day(db, payload.child_id),
            )
            enriched["story"] = story_for_animal(enriched)
        feedback = generate_partner_feedback(
            db,
            payload.child_id,
            animal.key,
            payload.action,
            enriched,
            ensure_adventure_day(db, payload.child_id),
            response_counts,
        )
        return {
            "animal": enriched,
            "interaction": {
                "action": payload.action,
                "label": interaction["label"],
                "energy_cost": energy_cost,
                "friendship_added": friendship_added,
                "mood_added": int(interaction.get("mood", 0)),
                "trust_added": int(interaction.get("trust", 0)),
                "curiosity_added": int(interaction.get("curiosity", 0)),
                "xp": xp,
                "memory": memory,
                "message": interaction["message"],
            },
            "safety_tip": "只做远距离观察和虚拟互动，不触摸、不追赶、不投喂真实动物。",
            "feedback": feedback,
            "adventure": response_adventure,
        }


@app.post("/api/pet/feed")
def feed_pet(payload: FeedPet) -> dict[str, Any]:
    with get_db() as db:
        require_child(db, payload.child_id)
        rhythm = rhythm_response(get_guardian_settings(db, payload.child_id))
        if not rhythm["can_feed"]:
            raise HTTPException(status_code=403, detail=rhythm["child_message"])
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
        finalize_adventure_completion(db, payload.child_id)

        return {
            "pet": updated_pet,
            "used_food": {"item_key": payload.food_key, "item_name": item["item_name"]},
            "effect": effect,
            "adventure": adventure_response(db, payload.child_id),
        }


def encyclopedia_for_child(db, child_id: int) -> dict[str, Any]:
    require_child(db, child_id)
    rows = db.execute(
        """
        SELECT entry_type, entry_key, name, category, knowledge, safety_tip,
               count, friendship, mood, trust, curiosity, home_level,
               growth_points, away_state, away_reason, keepsake, away_at,
               memory, adopted, first_seen, last_seen
        FROM encyclopedia_entry
        WHERE child_id = ?
        ORDER BY entry_type, name
        """,
        (child_id,),
    ).fetchall()
    entries = [dict(row) for row in rows]
    plants = [entry for entry in entries if entry["entry_type"] == "plant"]
    animals = enriched_animals([entry for entry in entries if entry["entry_type"] == "animal"])
    adventure = ensure_adventure_day(db, child_id)
    counts = progress_counts(db, child_id)
    for animal in animals:
        animal["daily_request"] = request_for_animal(animal["entry_key"], adventure, counts)
        animal["daily_event"] = daily_event_for_animal(animal, animal["daily_request"], adventure)
        animal["story"] = story_for_animal(animal)
    return {
        "child_id": child_id,
        "plants": plants,
        "animals": animals,
    }


@app.get("/api/encyclopedia/me")
def encyclopedia(child_id: int) -> dict[str, Any]:
    with get_db() as db:
        return encyclopedia_for_child(db, child_id)


@app.get("/api/parent/summary/today")
def parent_summary_today(child_id: int) -> dict[str, Any]:
    with get_db() as db:
        child = require_child(db, child_id)
        settings = get_guardian_settings(db, child_id)
        adventure = adventure_response(db, child_id)
        pet = get_pet(db, child_id)
        encyclopedia_data = encyclopedia_for_child(db, child_id)
        animals = encyclopedia_data["animals"]
        counts = progress_counts(db, child_id)
        for animal in animals:
            animal["daily_request"] = request_for_animal(animal["entry_key"], ensure_adventure_day(db, child_id), counts)
            animal["daily_event"] = daily_event_for_animal(animal, animal["daily_request"], ensure_adventure_day(db, child_id))
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
            "rhythm": adventure["rhythm"],
            "adventure": {
                "chapter": adventure["chapter"],
                "stage": adventure["stage"],
                "completed": adventure["completed"],
                "tasks": adventure["tasks"],
                "passport": adventure.get("passport", {}),
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
                        "mood": entry["mood"],
                        "trust": entry["trust"],
                        "curiosity": entry["curiosity"],
                        "home_level": entry["home_level"],
                        "home_display": entry.get("home_display"),
                        "memory": entry["memory"],
                        "growth_points": entry["growth_points"],
                        "life_stage": entry["life_stage"],
                        "care_state": entry["care_state"],
                        "away_state": entry["away_state"],
                        "away_reason": entry["away_reason"],
                        "keepsake": entry["keepsake"],
                        "inactive_days": entry["inactive_days"],
                        "daily_request": entry.get("daily_request"),
                        "daily_event": entry.get("daily_event"),
                        "story": entry.get("story"),
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
            "friends_enabled": bool(settings["friends_enabled"]),
            "garden_help_enabled": bool(settings["garden_help_enabled"]),
            "garden_likes_enabled": bool(settings["garden_likes_enabled"]),
            "daily_distance_goal": settings["daily_distance_goal"],
            "max_daily_distance": settings["max_daily_distance"],
            "sleep_start": settings["sleep_start"],
            "sleep_end": settings["sleep_end"],
            "study_mode_enabled": bool(settings["study_mode_enabled"]),
            "study_start": settings["study_start"],
            "study_end": settings["study_end"],
            "rhythm": rhythm_response(settings),
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
                friends_enabled = ?,
                garden_help_enabled = ?,
                garden_likes_enabled = ?,
                daily_distance_goal = ?,
                max_daily_distance = ?,
                sleep_start = ?,
                sleep_end = ?,
                study_mode_enabled = ?,
                study_start = ?,
                study_end = ?
            WHERE child_id = ?
            """,
            (
                1 if payload.outdoor_enabled else 0,
                1 if payload.animal_clues_enabled else 0,
                1 if payload.friends_enabled else 0,
                1 if payload.garden_help_enabled else 0,
                1 if payload.garden_likes_enabled else 0,
                payload.daily_distance_goal,
                payload.max_daily_distance,
                payload.sleep_start,
                payload.sleep_end,
                1 if payload.study_mode_enabled else 0,
                payload.study_start,
                payload.study_end,
                payload.child_id,
            ),
        )
        settings = get_guardian_settings(db, payload.child_id)
        return {
            "child_id": payload.child_id,
            "outdoor_enabled": bool(settings["outdoor_enabled"]),
            "animal_clues_enabled": bool(settings["animal_clues_enabled"]),
            "friends_enabled": bool(settings["friends_enabled"]),
            "garden_help_enabled": bool(settings["garden_help_enabled"]),
            "garden_likes_enabled": bool(settings["garden_likes_enabled"]),
            "daily_distance_goal": settings["daily_distance_goal"],
            "max_daily_distance": settings["max_daily_distance"],
            "sleep_start": settings["sleep_start"],
            "sleep_end": settings["sleep_end"],
            "study_mode_enabled": bool(settings["study_mode_enabled"]),
            "study_start": settings["study_start"],
            "study_end": settings["study_end"],
            "rhythm": rhythm_response(settings),
        }


@app.get("/api/catalog")
def catalog() -> dict[str, Any]:
    return {
        "plants": [plant.__dict__ for plant in PLANTS],
        "animal_clues": [clue.__dict__ for clue in ANIMAL_CLUES],
    }
