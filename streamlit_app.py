from __future__ import annotations

from pathlib import Path
from datetime import time
import json
import sys

import streamlit as st
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app.database import init_db  # noqa: E402
from app.main import app  # noqa: E402


init_db()
api = TestClient(app)


st.set_page_config(
    page_title="PetMate 自然探险",
    page_icon="PM",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
      :root {
        --pm-ink: #24352b;
        --pm-soft-ink: rgba(36, 53, 43, .72);
        --pm-line: rgba(36, 53, 43, .14);
        --pm-green: #2f7d57;
        --pm-moss: #5c7c46;
        --pm-sun: #b86f2a;
        --pm-paper: #f6f3ec;
      }
      [data-testid="stAppViewContainer"] {
        background:
          radial-gradient(circle at 12% 0%, rgba(47, 125, 87, .11), transparent 26rem),
          radial-gradient(circle at 98% 10%, rgba(184, 111, 42, .08), transparent 22rem),
          linear-gradient(180deg, #f6f3ec 0%, #edf3ed 100%);
      }
      [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--pm-line);
      }
      html, body, [class*="css"], [data-testid="stAppViewContainer"],
      [data-testid="stAppViewContainer"] *,
      [data-testid="stSidebar"] *,
      [data-testid="stMarkdownContainer"],
      [data-testid="stMarkdownContainer"] *,
      [data-testid="stMetric"],
      [data-testid="stMetric"] *,
      [data-testid="stCaptionContainer"],
      [data-testid="stCaptionContainer"] *,
      [data-testid="stTabs"] button,
      [data-testid="stTabs"] button *,
      label, p, span, div, h1, h2, h3, h4, h5, h6 {
        color: var(--pm-ink) !important;
      }
      [data-testid="stAlert"] *, [data-testid="stNotification"] *,
      [data-testid="stException"] * {
        color: inherit !important;
      }
      .block-container {
        padding-top: 3.2rem;
        max-width: 1180px;
      }
      [data-testid="stTabs"] [role="tablist"] {
        min-height: 3.2rem;
        padding-top: .35rem;
        overflow: visible;
      }
      [data-testid="stTabs"] button[role="tab"] {
        min-height: 2.6rem;
        line-height: 1.35;
        padding-top: .55rem;
        padding-bottom: .55rem;
      }
      h1, h2, h3 {
        letter-spacing: 0 !important;
      }
      button[kind="primary"] {
        background: var(--pm-green) !important;
        border-color: var(--pm-green) !important;
      }
      div[data-testid="stButton"] > button {
        min-height: 2.8rem;
        border-radius: 8px;
      }
      .pm-page-lede {
        max-width: 780px;
        color: var(--pm-soft-ink) !important;
        line-height: 1.65;
        margin-bottom: .6rem;
      }
      .pm-section-note {
        color: var(--pm-soft-ink) !important;
        font-size: .94rem;
      }
      .pm-watch .block-container {
        max-width: 420px;
      }
      @media (max-width: 760px) {
        .block-container {
          padding-top: 3.8rem;
          padding-left: .9rem;
          padding-right: .9rem;
        }
        div[data-testid="column"] {
          width: 100% !important;
          flex: 1 1 100% !important;
        }
        div[data-testid="stButton"] > button {
          min-height: 3.2rem;
          width: 100%;
        }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


VIEW_LABELS = {
    "完整网页演示": "full",
    "家长端": "parent",
    "手表模式": "watch",
}
VIEW_BY_KEY = {value: key for key, value in VIEW_LABELS.items()}
INTERACTION_LABELS = {
    "observe": "观察",
    "greet": "打招呼",
    "share_food": "分享食材",
    "play": "一起玩",
    "mini_adventure": "小探险",
    "decorate_home": "布置小窝",
}
INTERACTION_COSTS = {
    "observe": 1,
    "greet": 1,
    "share_food": 2,
    "play": 3,
    "mini_adventure": 4,
    "decorate_home": 3,
}
DEMO_FRIEND_GARDENS = [
    {
        "id": "friend_momo",
        "child_name": "沐沐",
        "guardian_status": "双方家长已批准",
        "garden_name": "风铃草小园",
        "likes": 18,
        "help_count": 3,
        "weekly_distance": 820,
        "plant_count": 3,
        "sent_leaf_today": True,
        "passport": "草地记录员",
        "recent_discovery": "蒲公英、蝴蝶线索",
        "partners": [
            {"name": "蝴蝶线索", "stage": "熟悉", "friendship": 72, "mood": 86, "home": "花间颜色小窝"},
            {"name": "麻雀线索", "stage": "初遇", "friendship": 38, "mood": 64, "home": "屋檐歌声角"},
        ],
    },
    {
        "id": "friend_an",
        "child_name": "安安",
        "guardian_status": "双方家长已批准",
        "garden_name": "慢慢叶片屋",
        "likes": 11,
        "help_count": 1,
        "weekly_distance": 540,
        "plant_count": 2,
        "sent_leaf_today": False,
        "passport": "见习观察员",
        "recent_discovery": "三叶草、蜗牛线索",
        "partners": [
            {"name": "蜗牛线索", "stage": "同行", "friendship": 91, "mood": 79, "home": "潮湿树荫小窝"},
        ],
    },
]


def parse_time_value(value: str, fallback: time) -> time:
    try:
        hour, minute = [int(part) for part in str(value).split(":", 1)]
        return time(hour=hour, minute=minute)
    except (ValueError, TypeError):
        return fallback


def format_time_value(value: time) -> str:
    return value.strftime("%H:%M")
STEP_LENGTH_METERS = 0.65
WALKING_METERS_PER_MINUTE = 75


def current_view_label() -> str:
    raw_view = st.query_params.get("view", "full")
    if isinstance(raw_view, list):
        raw_view = raw_view[0] if raw_view else "full"
    return VIEW_BY_KEY.get(str(raw_view), "完整网页演示")


def api_get(path: str, **params):
    response = api.get(path, params=params)
    if response.status_code >= 400:
        st.error(response.json().get("detail", response.text))
        st.stop()
    return response.json()


def api_post(path: str, payload: dict):
    response = api.post(path, json=payload)
    if response.status_code >= 400:
        st.error(response.json().get("detail", response.text))
        st.stop()
    return response.json()


def create_demo_child() -> int:
    child = api_post(
        "/api/child/create",
        {"name": "小林", "age": 8, "guardian_name": "林妈妈"},
    )
    child_id = int(child["child"]["id"])
    api_post("/api/pet/create", {"child_id": child_id, "name": "豆豆"})
    return child_id


def ensure_demo_child() -> int:
    if "child_id" not in st.session_state:
        st.session_state.child_id = create_demo_child()
    return int(st.session_state.child_id)


def reset_result_state() -> None:
    for key in ["last_scan", "last_animal", "last_feed", "last_interaction", "demo_result"]:
        st.session_state.pop(key, None)


def rerun() -> None:
    st.rerun()


def task_by_key(adventure: dict, key: str) -> dict | None:
    return next((task for task in adventure["tasks"] if task["key"] == key), None)


def first_incomplete_task(adventure: dict) -> dict | None:
    return next((task for task in adventure["tasks"] if not task["completed"] and not task.get("optional")), None)


def compact_names(items: list[dict], fallback: str) -> str:
    return "、".join(item["name"] for item in items) if items else fallback


def estimate_steps(distance_meters: int) -> int:
    return round(distance_meters / STEP_LENGTH_METERS)


def estimate_active_minutes(distance_meters: int) -> int:
    return max(1, round(distance_meters / WALKING_METERS_PER_MINUTE))


def walk_payload(child_id: int, distance_meters: int, active_minutes: int | None = None) -> dict:
    return {
        "child_id": child_id,
        "distance_delta_meters": distance_meters,
        "steps_delta": estimate_steps(distance_meters),
        "active_minutes_delta": active_minutes if active_minutes is not None else estimate_active_minutes(distance_meters),
    }


def activity_for(adventure: dict) -> dict:
    activity = adventure.get("activity") or {}
    distance = int(adventure.get("distance_meters", 0))
    return {
        "steps": int(activity.get("steps", estimate_steps(distance) if distance else 0)),
        "active_minutes": int(activity.get("active_minutes", estimate_active_minutes(distance) if distance else 0)),
        "estimated_kcal": float(activity.get("estimated_kcal", round((distance / 1000) * 25 * 0.6, 1))),
        "activity_energy": int(activity.get("activity_energy", round(distance / 100) if distance else 0)),
        "kcal_note": activity.get("kcal_note", "估算值，用于家长健康参考。"),
    }


def animal_friendship_to_adopt(animal: dict) -> int:
    return int(animal.get("friendship_to_adopt", max(0, 100 - int(animal.get("friendship", 0)))))


def animal_favorite(animal: dict) -> str:
    return str(animal.get("favorite") or "自然食材")


def animal_habitat(animal: dict) -> str:
    return str(animal.get("habitat") or "安全户外区域")


def animal_life_stage(animal: dict) -> dict:
    return animal.get("life_stage") or {
        "label": "初遇",
        "growth_points": int(animal.get("growth_points", 0)),
        "next_target": 100,
        "science": "保持距离观察，认识它喜欢的环境。",
    }


def animal_care_state(animal: dict) -> dict:
    return animal.get("care_state") or {
        "state": animal.get("away_state", "home"),
        "label": "陪伴中",
        "severity": "ok",
        "reason": "状态稳定，适合继续探险和互动。",
        "recovery_hint": "继续用活动能量和它留下新记忆。",
        "can_interact": True,
        "keepsake": animal.get("keepsake") or "自然回忆徽章",
    }


def render_partner_feedback(feedback: dict | None) -> None:
    if not feedback:
        return
    with st.container(border=True):
        st.markdown("### 伙伴反馈")
        st.caption(f"{feedback.get('personality', '温和')} · {feedback.get('emotion', '好奇')}")
        st.write(feedback.get("scene", "伙伴在安全距离外看着你。"))
        st.success(f"“{feedback.get('partner_line', '我记住了今天的陪伴。')}”")
        st.info(feedback.get("science_link", "自然伙伴适合观察和记录，不适合触摸或追赶。"))
        st.caption(f"下一步：{feedback.get('next_suggestion', '继续完成今日探险。')}")


def render_rhythm_notice(rhythm: dict | None, compact: bool = False) -> None:
    if not rhythm:
        return
    state = rhythm.get("state", "free")
    message = rhythm.get("child_message", "")
    label = rhythm.get("label", "可探险")
    if state == "sleep":
        st.info(f"{label}：{message}")
    elif state == "study":
        st.warning(f"{label}：{message}")
    elif not compact:
        st.caption(f"{label}：{message}")


def parent_today_value(summary: dict) -> dict:
    existing = summary.get("today_value")
    if isinstance(existing, dict):
        return {
            "worth_it": bool(existing.get("worth_it", False)),
            "learned": list(existing.get("learned", [])),
            "next_action": str(existing.get("next_action", "继续完成今日探险。")),
            "suggestion": str(existing.get("suggestion", existing.get("next_action", "继续完成今日探险。"))),
        }

    discoveries = summary.get("discoveries", {})
    adventure = summary.get("adventure", {})
    outdoor = summary.get("outdoor", {})
    learned = list(discoveries.get("plants", []))
    learned.extend(animal.get("name", "动物线索") for animal in discoveries.get("animals", []))
    worth_it = (
        int(outdoor.get("distance_meters", 0)) > 0
        or int(outdoor.get("active_minutes", 0)) > 0
        or int(discoveries.get("plant_scan_count", 0)) > 0
        or int(discoveries.get("animal_clue_count", 0)) > 0
    )

    next_action = "继续完成今日探险。"
    for task in adventure.get("tasks", []):
        if not task.get("completed") and not task.get("optional"):
            next_action = f"下一步建议：{task.get('title', '完成未完成任务')}。"
            break
    else:
        animals = discoveries.get("animals", [])
        if animals:
            next_action = f"可以和{animals[0].get('name', '动物伙伴')}打招呼，继续提升友好度。"
        elif adventure.get("completed"):
            next_action = "今日闭环已完成，可以复盘孩子观察到的知识点。"

    return {
        "worth_it": worth_it,
        "learned": learned,
        "next_action": next_action,
        "suggestion": "今天已经产生可复盘的自然探险记录。" if worth_it else "今天还没有产生户外探险记录，可以从走 100m 开始。",
    }


def run_demo_flow(child_id: int) -> None:
    result: list[str] = []
    settings = api_get("/api/parent/settings", child_id=child_id)
    adventure = api_get("/api/adventure/today", child_id=child_id)

    target_distance = min(int(settings["daily_distance_goal"]), int(settings["max_daily_distance"]))
    if adventure["distance_meters"] < target_distance:
        delta = target_distance - adventure["distance_meters"]
        api_post("/api/adventure/walk", walk_payload(child_id, delta))
        result.append(f"走路 {delta}m")

    for image_name in ["dandelion_test.jpg", "clover_test.jpg"]:
        adventure = api_get("/api/adventure/today", child_id=child_id)
        plant_task = task_by_key(adventure, "scan_2_plants")
        if plant_task and plant_task["completed"]:
            break
        if adventure["available_chances"]["plant"] <= 0:
            api_post("/api/adventure/walk", walk_payload(child_id, 250))
            result.append("补充走路 250m")
        scan = api_post("/api/scan/plant", {"child_id": child_id, "image_name": image_name})
        st.session_state.last_scan = scan
        result.append(f"扫描 {scan['recognition']['name']}")

    adventure = api_get("/api/adventure/today", child_id=child_id)
    animal_task = task_by_key(adventure, "find_1_animal_clue")
    if animal_task and not animal_task["completed"]:
        if adventure["available_chances"]["animal"] <= 0:
            api_post("/api/adventure/walk", walk_payload(child_id, 500))
            result.append("补充走路 500m")
        animal = api_post("/api/discovery/animal-clue", {"child_id": child_id})
        st.session_state.last_animal = animal
        result.append(f"发现 {animal['animal_clue']['name']}")

    status = api_get("/api/pet/status", child_id=child_id)
    feed_task = task_by_key(api_get("/api/adventure/today", child_id=child_id), "feed_pet_once")
    if feed_task and not feed_task["completed"]:
        foods = [item for item in status["inventory"] if item["item_type"] == "food" and item["quantity"] > 0]
        if foods:
            feed = api_post("/api/pet/feed", {"child_id": child_id, "food_key": foods[0]["item_key"]})
            st.session_state.last_feed = feed
            result.append(f"喂养 {foods[0]['item_name']}")

    encyclopedia = api_get("/api/encyclopedia/me", child_id=child_id)
    if encyclopedia["animals"]:
        active = next((animal for animal in encyclopedia["animals"] if not animal["adopted"]), encyclopedia["animals"][0])
        interaction = api_post(
            "/api/animal/interact",
            {"child_id": child_id, "animal_key": active["entry_key"], "action": "greet"},
        )
        st.session_state.last_interaction = interaction
        result.append(f"和{interaction['animal']['name']}打招呼")

    st.session_state.demo_result = result


def render_task(task: dict) -> None:
    status = "完成" if task["completed"] else "进行中"
    if task.get("optional"):
        status = f"{status} · 可选"
    st.markdown(f"**{task['title']}**")
    st.progress(min(task["current"] / max(task["target"], 1), 1.0), text=f"{status} · {task['current']} / {task['target']}")


def render_passport(passport: dict | None, compact: bool = False) -> None:
    if not passport:
        return
    badges = passport.get("badges", [])
    st.markdown("### 探险护照")
    st.caption(
        f"{passport.get('level', '见习观察员')} · "
        f"{passport.get('completed_badges', 0)} / {passport.get('total_badges', len(badges))} 枚徽章"
    )
    next_badge = passport.get("next_badge")
    if next_badge:
        st.info(
            f"下一枚：{next_badge.get('title')} "
            f"{next_badge.get('current', 0)} / {next_badge.get('target', 1)}"
        )
    if compact:
        return
    cols = st.columns(3, gap="large")
    for index, badge in enumerate(badges):
        with cols[index % 3].container(border=True):
            if badge.get("completed"):
                st.success(f"{badge.get('category', '徽章')} · 已获得")
            else:
                st.caption(f"{badge.get('category', '徽章')} · 进行中")
            st.markdown(f"**{badge.get('title', '探险徽章')}**")
            st.progress(
                min(badge.get("current", 0) / max(badge.get("target", 1), 1), 1.0),
                text=f"{badge.get('current', 0)} / {badge.get('target', 1)}",
            )
            st.caption(badge.get("description", "继续完成自然探险。"))


def render_partner_story(animal: dict, compact: bool = False) -> None:
    story = animal.get("story") or {}
    if not story:
        return
    st.markdown("**伙伴故事**")
    st.progress(
        min(story.get("completed_chapters", 0) / max(story.get("total_chapters", 1), 1), 1.0),
        text=f"{story.get('completed_chapters', 0)} / {story.get('total_chapters', 1)} 段",
    )
    st.caption(f"下一段：{story.get('current_title', '继续相处')} · {story.get('next_hint', '继续完成今日探险。')}")
    if compact:
        return
    chapters = story.get("chapters", [])
    if chapters:
        st.write(" · ".join(("已解锁 " if chapter.get("completed") else "待解锁 ") + chapter.get("title", "故事") for chapter in chapters))


def render_partner_wish(animal: dict, compact: bool = False) -> None:
    request = animal.get("daily_request") or {}
    if not request:
        return
    event = animal.get("daily_event") or {}
    title = request.get("title", "想一起互动")
    current = request.get("current", 0)
    target = request.get("target", 1)
    completed = bool(request.get("completed"))
    if compact:
        if event:
            st.caption(f"今日事件：{event.get('title', '今天的小发现')}")
        st.caption(f"愿望：{title} {current}/{target}")
        return
    st.markdown("**每日事件卡**")
    if event:
        st.caption(event.get("title", "今天的小发现"))
        st.write(event.get("scene", "伙伴在安全距离外等你带回一个自然观察。"))
    if completed:
        st.success(f"{title} · 已完成")
    else:
        st.info(f"{title} · 进行中")
    st.progress(min(current / max(target, 1), 1.0), text=f"{current} / {target}")
    st.caption(event.get("next_action") or request.get("hint", "继续探险，完成伙伴今天的小愿望。"))
    st.caption(f"完成反馈：{event.get('complete_text', '完成后伙伴会留下新的故事线索。')}")
    st.caption(f"奖励：{event.get('reward') or request.get('reward', '完成后伙伴会留下新的故事线索。')}")
    if event.get("badge_hint"):
        st.caption(event["badge_hint"])


def render_home_display(animal: dict, compact: bool = False) -> None:
    home = animal.get("home_display") or {}
    if not home:
        return
    st.markdown("**伙伴小窝**")
    st.progress(
        min(home.get("unlocked_count", 0) / max(home.get("total_count", 1), 1), 1.0),
        text=f"Lv{home.get('level', 1)} · {home.get('unlocked_count', 0)} / {home.get('total_count', 1)} 件装饰",
    )
    st.caption(home.get("theme", "自然小窝"))
    if compact:
        return
    decorations = home.get("decorations", [])
    if decorations:
        st.write(" · ".join(("已摆放 " if item.get("unlocked") else "待解锁 ") + item.get("name", "装饰") for item in decorations))
    next_item = home.get("next_decoration")
    if next_item:
        st.caption(f"下一件：{next_item.get('name')} · 来自{next_item.get('source')}")
    st.caption(home.get("note", "小窝装饰先展示，不做复杂编辑。"))


def friend_action_key(action: str, friend_id: str, day: str) -> str:
    return f"friend_{action}_{friend_id}_{day}"


def render_own_public_garden(encyclopedia: dict, adventure: dict) -> None:
    with st.container(border=True):
        st.markdown("### 我的公开花园预览")
        st.caption("好友只能看到伙伴、小窝、护照和系统生成发现，不显示路线、位置、学校或自由文本。")
        render_passport(adventure.get("passport"), compact=True)
        if not encyclopedia.get("animals"):
            st.info("还没有可展示的动物伙伴。发现动物线索后会出现在花园。")
            return
        for animal in encyclopedia["animals"][:3]:
            life_stage = animal_life_stage(animal)
            home = animal.get("home_display") or {}
            st.write(
                f"{animal['name']} · {life_stage.get('label', '初遇')} · "
                f"友好度 {animal.get('friendship', 0)}/100 · {home.get('theme', '自然小窝')}"
            )


def render_friend_quests(encyclopedia: dict, adventure: dict) -> None:
    st.markdown("### 好友共同任务")
    st.caption("共同任务只合并线上进度，不要求同时在线、不约同一地点、不公开排名。")
    friend_distance = sum(friend.get("weekly_distance", 0) for friend in DEMO_FRIEND_GARDENS)
    friend_plants = sum(friend.get("plant_count", 0) for friend in DEMO_FRIEND_GARDENS)
    friend_leaf_sent = any(friend.get("sent_leaf_today", False) for friend in DEMO_FRIEND_GARDENS)
    child_leaf_sent = any(
        bool(st.session_state.get(friend_action_key("like", friend["id"], adventure.get("day", "today"))))
        for friend in DEMO_FRIEND_GARDENS
    )
    quests = [
        {
            "title": "今天一起走 1500m",
            "current": min(int(adventure.get("distance_meters", 0)) + friend_distance, 1500),
            "target": 1500,
            "reward": "共同探险章进度 +1，双方花园出现友谊叶环。",
        },
        {
            "title": "一起认识 4 种植物",
            "current": min(len(encyclopedia.get("plants", [])) + friend_plants, 4),
            "target": 4,
            "reward": "伙伴故事出现一句朋友带来的自然消息。",
        },
        {
            "title": "互相送一片叶子",
            "current": int(child_leaf_sent) + int(friend_leaf_sent),
            "target": 2,
            "reward": "双方收到一次温和鼓励，不进入排行榜。",
        },
    ]
    cols = st.columns(3, gap="large")
    for index, quest in enumerate(quests):
        with cols[index].container(border=True):
            completed = quest["current"] >= quest["target"]
            if completed:
                st.success("已完成")
            else:
                st.caption("进行中")
            st.markdown(f"**{quest['title']}**")
            st.progress(quest["current"] / max(quest["target"], 1), text=f"{quest['current']} / {quest['target']}")
            st.caption(quest["reward"])


def render_friend_garden(child_id: int, settings: dict, encyclopedia: dict, adventure: dict) -> None:
    st.markdown("### 好友花园")
    st.caption("儿童手表式好友：必须家长开启并批准。当前是演示好友，不接陌生人搜索、不聊天、不显示真实位置。")

    if not settings.get("friends_enabled", False):
        st.warning("家长尚未开启好友花园。开启后才能参观已批准好友的小窝。")
        st.info("请到“家长设置”打开“允许好友花园”。默认关闭是为了避免陌生社交风险。")
        render_own_public_garden(encyclopedia, adventure)
        return

    render_own_public_garden(encyclopedia, adventure)
    render_friend_quests(encyclopedia, adventure)
    st.markdown("### 已批准好友")
    st.caption("V0 使用内置示例好友验证体验。正式版需要家长访问码、同意记录、删除好友和举报/拉黑。")

    day = adventure.get("day", "today")
    for friend in DEMO_FRIEND_GARDENS:
        with st.container(border=True):
            h1, h2 = st.columns([1.1, .9], gap="large")
            with h1:
                st.markdown(f"#### {friend['garden_name']}")
                st.caption(f"{friend['child_name']} · {friend['guardian_status']} · {friend['passport']}")
                st.write("最近发现：" + friend["recent_discovery"])
                for partner in friend["partners"]:
                    st.progress(partner["friendship"] / 100, text=f"{partner['name']} · {partner['stage']} · 友好度 {partner['friendship']}/100")
                    st.caption(f"心情 {partner['mood']} · {partner['home']}")
            with h2:
                like_key = friend_action_key("like", friend["id"], day)
                feed_key = friend_action_key("feed", friend["id"], day)
                liked = bool(st.session_state.get(like_key))
                helped = bool(st.session_state.get(feed_key))
                like_total = friend["likes"] + (1 if liked else 0)
                help_total = friend["help_count"] + (1 if helped else 0)
                st.metric("收到鼓励", like_total)
                st.metric("帮忙投喂", help_total)
                if st.button(
                    "送一片叶子",
                    use_container_width=True,
                    disabled=liked or not settings.get("garden_likes_enabled", True),
                    key=f"like_{friend['id']}",
                ):
                    st.session_state[like_key] = True
                    rerun()
                if st.button(
                    "帮忙投喂",
                    use_container_width=True,
                    disabled=helped or not settings.get("garden_help_enabled", True),
                    key=f"feed_{friend['id']}",
                ):
                    st.session_state[feed_key] = True
                    rerun()
                if liked:
                    st.success("今天已送出鼓励。")
                if helped:
                    st.success("今天已帮忙投喂。")
                st.caption("每天每个好友限一次，避免刷赞和打扰。")


def render_chapter_path(adventure: dict, encyclopedia: dict) -> None:
    adopted = any(animal["adopted"] for animal in encyclopedia["animals"])
    chapters = [
        {
            "title": "小小观察员",
            "goal": "500m、2 种植物、1 个动物线索、喂宠物",
            "done": adventure["completed"],
            "active": True,
        },
        {
            "title": "草地探险家",
            "goal": "900m、3 种植物、2 次动物线索",
            "done": False,
            "active": adventure["completed"],
        },
        {
            "title": "动物侦探",
            "goal": "和伙伴互动，把友好度提升到 100",
            "done": adopted,
            "active": adventure["completed"] and bool(encyclopedia["animals"]),
        },
    ]
    cols = st.columns(3, gap="large")
    for index, chapter in enumerate(chapters, start=1):
        with cols[index - 1].container(border=True):
            if chapter["done"]:
                st.success(f"第 {index} 关 · 已完成")
            elif chapter["active"]:
                st.info(f"第 {index} 关 · 已解锁")
            else:
                st.caption(f"第 {index} 关 · 待解锁")
            st.markdown(f"### {chapter['title']}")
            st.write(chapter["goal"])


def render_today_book(child_id: int, adventure: dict, pet_status: dict, encyclopedia: dict, settings: dict) -> None:
    pet = pet_status["pet"]
    chances = adventure["available_chances"]
    activity = activity_for(adventure)
    incomplete = first_incomplete_task(adventure)
    active_animal = next(
        (animal for animal in encyclopedia["animals"] if animal_care_state(animal).get("can_interact", True) and not animal["adopted"]),
        None,
    )
    if active_animal is None and encyclopedia["animals"]:
        active_animal = encyclopedia["animals"][0]

    st.title("今日自然探险册")
    st.markdown(
        "<p class='pm-page-lede'>用真实走路换探索机会，用植物观察获得食材，用动物线索推进虚拟领养。演示按钮可以一次跑完整个闭环。</p>",
        unsafe_allow_html=True,
    )
    rhythm = adventure.get("rhythm", settings.get("rhythm", {}))
    render_rhythm_notice(rhythm)

    action_col, pet_col, animal_col = st.columns([1.2, .9, .9], gap="large")
    with action_col.container(border=True):
        st.markdown("### 下一步行动")
        if active_animal and active_animal.get("daily_event"):
            event = active_animal["daily_event"]
            st.caption(f"今日事件：{event.get('title', '今天的小发现')}")
            st.write(event.get("scene", "伙伴在等你带回一个自然观察。"))
        if adventure["completed"]:
            st.success("今日关卡已完成")
            st.write("可以继续和动物伙伴互动，或让家长查看今日价值。")
        elif incomplete:
            st.info(incomplete["title"])
            st.progress(min(incomplete["current"] / max(incomplete["target"], 1), 1.0), text=f"{incomplete['current']} / {incomplete['target']}")
        if st.button(
            "一键完成今日演示",
            type="primary",
            use_container_width=True,
            key="demo_full_flow",
            disabled=not rhythm.get("can_adventure", True),
        ):
            run_demo_flow(child_id)
            rerun()
        if "demo_result" in st.session_state:
            st.success("已完成：" + "、".join(st.session_state.demo_result))
        if "last_interaction" in st.session_state:
            render_partner_feedback(st.session_state.last_interaction.get("feedback"))

    with pet_col.container(border=True):
        st.markdown("### 宠物状态")
        st.metric("豆豆", f"Lv{pet['level']}", f"{pet['xp']} XP")
        st.progress(pet["xp"] / max(pet_status["next_level_xp"], 1), text="成长进度")
        st.caption(f"饱腹 {pet['hunger']} · 心情 {pet['mood']} · 亲密 {pet['bond']}")

    with animal_col.container(border=True):
        st.markdown("### 动物伙伴")
        if active_animal:
            life_stage = animal_life_stage(active_animal)
            care_state = animal_care_state(active_animal)
            state = "已领养伙伴" if active_animal["adopted"] else f"还差 {animal_friendship_to_adopt(active_animal)} 友好度"
            st.metric(active_animal["name"], f"{active_animal['friendship']}/100", state)
            st.progress(active_animal["friendship"] / 100, text=animal_habitat(active_animal))
            st.caption(f"{life_stage['label']} · {care_state['label']}")
            render_partner_wish(active_animal, compact=True)
            render_home_display(active_animal, compact=True)
        else:
            st.info("走到 500m 后可发现动物线索")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("累计距离", f"{adventure['distance_meters']}m", f"目标 {settings['daily_distance_goal']}m")
    m2.metric("探索能量", adventure["exploration_energy"], "每 100m +1")
    m3.metric("植物机会", chances["plant"], "每 250m +1")
    m4.metric("动物线索", chances["animal"], "每 500m +1")

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("今日步数", f"{activity['steps']}")
    a2.metric("活动分钟", f"{activity['active_minutes']} 分钟")
    a3.metric("活动能量", activity["activity_energy"], "用于活力反馈")
    a4.metric("估算消耗", f"{activity['estimated_kcal']:.1f} kcal", "家长参考")

    st.markdown("### 三关成就路径")
    render_chapter_path(adventure, encyclopedia)

    render_passport(adventure.get("passport"))

    st.markdown("### 今日任务")
    task_cols = st.columns(2, gap="large")
    for index, task in enumerate(adventure["tasks"]):
        with task_cols[index % 2].container(border=True):
            render_task(task)

    st.markdown("### 最近发现")
    d1, d2 = st.columns(2, gap="large")
    with d1.container(border=True):
        st.markdown("**植物图鉴**")
        st.write(compact_names(encyclopedia["plants"][-4:], "还没有植物发现"))
    with d2.container(border=True):
        st.markdown("**动物伙伴进度**")
        if encyclopedia["animals"]:
            for animal in encyclopedia["animals"][-3:]:
                st.write(f"{animal['name']} · 友好度 {animal['friendship']}/100")
        else:
            st.write("还没有动物线索")


def render_plant_result(scan: dict | None) -> None:
    if not scan:
        st.info("走到 250m 会解锁植物发现机会。扫描后会获得知识点和宠物食材。")
        return
    recognition = scan["recognition"]
    st.markdown(f"### {recognition['name']}")
    st.caption(f"{recognition['category']} · 模拟可信度 {recognition['confidence']:.0%}")
    st.progress(recognition["confidence"], text="识别结果")
    st.write(scan["knowledge_card"]["knowledge"])
    st.info(scan["knowledge_card"]["safety_tip"])
    st.success("掉落资源：" + "、".join(item["item_name"] for item in scan["drops"]))
    plant_task = task_by_key(scan["adventure"], "scan_2_plants")
    if plant_task:
        render_task(plant_task)


def render_animal_result(result: dict | None) -> None:
    if not result:
        st.info("走到 500m 会解锁动物线索。动物只做远距离观察和虚拟领养。")
        return
    animal = result["animal_clue"]
    favorite = animal.get("favorite", "自然食材")
    greeting = animal.get("greeting", "伙伴回应了你的观察。")
    st.markdown(f"### {animal['name']}")
    st.caption(f"{animal['category']} · {animal['rarity']} · 喜欢 {favorite}")
    st.progress(animal["friendship"] / 100, text=f"友好度 {animal['friendship']}/100")
    st.write(result["knowledge_card"]["knowledge"])
    st.info(result["knowledge_card"]["safety_tip"])
    st.success(greeting)
    animal_task = task_by_key(result["adventure"], "find_1_animal_clue")
    if animal_task:
        render_task(animal_task)


def interact_with_animal(child_id: int, animal: dict, action: str) -> None:
    for key in ["last_scan", "last_animal", "last_feed"]:
        st.session_state.pop(key, None)
    st.session_state.last_interaction = api_post(
        "/api/animal/interact",
        {"child_id": child_id, "animal_key": animal["entry_key"], "action": action},
    )
    rerun()


def render_animal_buttons(child_id: int, animal: dict, prefix: str, available_energy: int) -> None:
    rhythm = api_get("/api/adventure/today", child_id=child_id).get("rhythm", {})
    rhythm_allows = rhythm.get("can_interact", True)
    actions = list(INTERACTION_LABELS.items())
    for row_start in range(0, len(actions), 3):
        cols = st.columns(3)
        for col, (action, label) in zip(cols, actions[row_start:row_start + 3]):
            cost = INTERACTION_COSTS[action]
            disabled = available_energy < cost or not rhythm_allows
            with col:
                if st.button(
                    f"{label} · {cost}能量",
                    use_container_width=True,
                    disabled=disabled,
                    key=f"{prefix}_{animal['entry_key']}_{action}",
                ):
                    interact_with_animal(child_id, animal, action)
    if available_energy <= 0:
        st.caption("活动能量不足，先走一段路再和伙伴互动。")
    if not rhythm_allows:
        st.caption(rhythm.get("child_message", "当前不是互动时间。"))


def render_discovery_tab(child_id: int, adventure: dict) -> None:
    chances = adventure["available_chances"]
    rhythm = adventure.get("rhythm", {})
    can_adventure = rhythm.get("can_adventure", True)
    scan_col, result_col = st.columns([.92, 1.08], gap="large")
    with scan_col:
        render_rhythm_notice(rhythm, compact=True)
        with st.container(border=True):
            st.markdown("### 植物扫描")
            image_hint = st.selectbox(
                "模拟照片",
                ["dandelion_test.jpg", "clover_test.jpg", "plane_leaf_test.jpg"],
                format_func=lambda x: {
                    "dandelion_test.jpg": "蒲公英测试图",
                    "clover_test.jpg": "三叶草测试图",
                    "plane_leaf_test.jpg": "梧桐叶测试图",
                }[x],
            )
            uploaded = st.file_uploader("上传植物照片", type=["jpg", "jpeg", "png"])
            st.caption(f"当前植物机会：{chances['plant']}")
            if st.button("扫描植物", type="primary", use_container_width=True, disabled=chances["plant"] <= 0 or not can_adventure):
                image_name = uploaded.name if uploaded else image_hint
                st.session_state.last_scan = api_post(
                    "/api/scan/plant",
                    {"child_id": child_id, "image_name": image_name},
                )
                rerun()

        with st.container(border=True):
            st.markdown("### 动物线索")
            st.caption(f"当前动物线索机会：{chances['animal']}")
            if st.button("发现动物线索", use_container_width=True, disabled=chances["animal"] <= 0 or not can_adventure):
                st.session_state.last_animal = api_post("/api/discovery/animal-clue", {"child_id": child_id})
                rerun()
            st.caption("安全规则：不触摸、不追赶、不投喂真实动物。")

    with result_col:
        with st.container(border=True):
            st.markdown("## 最近植物发现")
            render_plant_result(st.session_state.get("last_scan"))
        with st.container(border=True):
            st.markdown("## 最近动物线索")
            render_animal_result(st.session_state.get("last_animal"))


def render_garden_tab(child_id: int, pet_status: dict, encyclopedia: dict, adventure: dict) -> None:
    pet = pet_status["pet"]
    available_energy = activity_for(adventure)["activity_energy"]
    rhythm = adventure.get("rhythm", {})
    can_feed = rhythm.get("can_feed", True)
    pet_col, animal_col = st.columns([.9, 1.1], gap="large")
    with pet_col.container(border=True):
        render_rhythm_notice(rhythm, compact=True)
        st.markdown("### 主宠物 · 豆豆")
        st.metric("等级", f"Lv{pet['level']}", f"{pet['xp']} XP")
        st.progress(pet["xp"] / max(pet_status["next_level_xp"], 1), text=f"下一等级需要 {pet_status['next_level_xp']} XP")
        s1, s2, s3 = st.columns(3)
        s1.metric("饱腹", pet["hunger"])
        s2.metric("心情", pet["mood"])
        s3.metric("亲密", pet["bond"])

        foods = [item for item in pet_status["inventory"] if item["item_type"] == "food" and item["quantity"] > 0]
        if foods:
            food_labels = {f"{food['item_name']} x{food['quantity']}": food["item_key"] for food in foods}
            selected = st.selectbox("选择食材", list(food_labels.keys()))
            if st.button("喂养宠物", type="primary", use_container_width=True, disabled=not can_feed):
                st.session_state.last_feed = api_post(
                    "/api/pet/feed",
                    {"child_id": child_id, "food_key": food_labels[selected]},
                )
                rerun()
        else:
            st.info("还没有可用食材。先走路并扫描植物。")

        if "last_feed" in st.session_state:
            feed = st.session_state.last_feed
            st.success(f"已喂养 {feed['used_food']['item_name']}，豆豆心情提升。")

    with animal_col:
        st.markdown("### 动物伙伴")
        st.metric("可用活动能量", available_energy, "互动会消耗")
        if not encyclopedia["animals"]:
            st.info("发现动物线索后，这里会出现可互动的虚拟伙伴。")
        for animal in encyclopedia["animals"]:
            with st.container(border=True):
                life_stage = animal_life_stage(animal)
                care_state = animal_care_state(animal)
                status = "已领养伙伴" if animal["adopted"] else f"还差 {animal_friendship_to_adopt(animal)} 友好度可领养"
                st.markdown(f"#### {animal['name']} · {animal['category']}")
                st.caption(f"喜欢：{animal_favorite(animal)} · 常见环境：{animal_habitat(animal)}")
                st.progress(animal["friendship"] / 100, text=f"{status} · {animal['friendship']}/100")
                stage_cols = st.columns(3)
                stage_cols[0].metric("成长阶段", life_stage["label"])
                stage_cols[1].metric("成长点", life_stage.get("growth_points", 0))
                stage_cols[2].metric("照护状态", care_state["label"])
                if life_stage.get("next_target"):
                    st.progress(
                        min(life_stage.get("growth_points", 0) / max(life_stage["next_target"], 1), 1.0),
                        text=f"距离下一阶段 {max(0, life_stage['next_target'] - life_stage.get('growth_points', 0))} 成长点",
                    )
                st.info(life_stage["science"])
                if care_state["state"] == "returned_to_nature":
                    st.success(f"留下纪念物：{care_state.get('keepsake', animal.get('keepsake', '自然回忆徽章'))}")
                    st.caption(care_state["reason"])
                    st.caption(care_state["recovery_hint"])
                elif care_state["state"] in {"resting", "quiet"}:
                    st.warning(f"{care_state['reason']} {care_state['recovery_hint']}")
                stat_cols = st.columns(4)
                stat_cols[0].metric("心情", animal.get("mood", 50))
                stat_cols[1].metric("信任", animal.get("trust", 20))
                stat_cols[2].metric("好奇", animal.get("curiosity", 40))
                stat_cols[3].metric("小窝", f"Lv{animal.get('home_level', 1)}")
                render_partner_wish(animal)
                render_partner_story(animal)
                render_home_display(animal)
                st.caption(f"记忆：{animal.get('memory') or '还没有留下伙伴记忆。'}")
                st.write(animal["knowledge"])
                st.info(animal["safety_tip"])
                if care_state.get("can_interact", True):
                    render_animal_buttons(child_id, animal, "garden", available_energy)
                else:
                    st.caption("它已经回到自然，图鉴和回忆会保留。重新发现线索后有机会再次遇见。")

        if "last_interaction" in st.session_state:
            interaction = st.session_state.last_interaction
            st.success(
                f"{interaction['interaction']['label']}成功：{interaction['interaction']['message']} "
                f"-{interaction['interaction']['energy_cost']} 能量，"
                f"+{interaction['interaction']['friendship_added']} 友好度"
            )
            st.caption(f"新记忆：{interaction['interaction'].get('memory', '')}")
            render_partner_feedback(interaction.get("feedback"))


def render_parent_report(child_id: int) -> None:
    summary = api_get("/api/parent/summary/today", child_id=child_id)
    today_value = parent_today_value(summary)
    outdoor = summary.get("outdoor", {})
    rhythm = summary.get("rhythm", {})
    st.markdown("### 今日是否值得")
    if rhythm:
        st.info(f"当前伙伴作息：{rhythm.get('label')}。{rhythm.get('parent_message')}")
    if today_value["worth_it"]:
        st.success(today_value["suggestion"])
    else:
        st.info("今天还没有产生户外探险记录，可以从走 100m 开始。")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("户外距离", f"{outdoor.get('distance_meters', 0)}m", f"目标 {outdoor.get('goal_meters', 0)}m")
    m2.metric("活动分钟", f"{outdoor.get('active_minutes', 0)} 分钟")
    m3.metric("估算消耗", f"{float(outdoor.get('estimated_kcal', 0)):.1f} kcal")
    m4.metric("今日 XP", summary["adventure"]["xp"])

    h1, h2, h3, h4 = st.columns(4)
    h1.metric("今日步数", outdoor.get("steps", 0))
    h2.metric("活动能量", outdoor.get("activity_energy", 0))
    h3.metric("植物扫描", summary["discoveries"]["plant_scan_count"])
    h4.metric("动物线索", summary["discoveries"]["animal_clue_count"])

    render_passport(summary.get("adventure", {}).get("passport"), compact=False)

    r1, r2 = st.columns([1, 1], gap="large")
    with r1.container(border=True):
        st.markdown("### 孩子今日建议")
        st.write(today_value["next_action"])
        learned = today_value["learned"]
        st.caption("学到：" + ("、".join(learned) if learned else "暂无发现"))
    with r2.container(border=True):
        st.markdown("### 安全提醒")
        for note in summary["safety_notes"]:
            st.write(f"- {note}")

    st.markdown("### 关卡进度")
    for task in summary["adventure"]["tasks"]:
        render_task(task)

    st.markdown("### 发现内容")
    st.write("植物：" + ("、".join(summary["discoveries"]["plants"]) if summary["discoveries"]["plants"] else "暂无"))
    if summary["discoveries"]["animals"]:
        for animal in summary["discoveries"]["animals"]:
            life_stage = animal_life_stage(animal)
            care_state = animal_care_state(animal)
            adopted = "已领养" if animal["adopted"] else f"还差 {animal_friendship_to_adopt(animal)}"
            st.write(f"{animal['name']}：友好度 {animal['friendship']}/100 · {adopted} · 喜欢 {animal_favorite(animal)}")
            st.caption(
                f"心情 {animal.get('mood', 50)} · 信任 {animal.get('trust', 20)} · "
                f"好奇 {animal.get('curiosity', 40)} · 小窝 Lv{animal.get('home_level', 1)}"
            )
            st.caption(
                f"阶段：{life_stage['label']} · 状态：{care_state['label']} · "
                f"成长点 {life_stage.get('growth_points', animal.get('growth_points', 0))}"
            )
            if animal.get("memory"):
                st.caption(f"最近记忆：{animal['memory']}")
            home = animal.get("home_display") or {}
            if home:
                st.caption(
                    f"小窝：{home.get('theme', '自然小窝')} · "
                    f"{home.get('unlocked_count', 0)} / {home.get('total_count', 1)} 件装饰"
                )
            if care_state["state"] == "returned_to_nature":
                st.caption(f"留下纪念物：{care_state.get('keepsake', animal.get('keepsake', '自然回忆徽章'))}")
            elif care_state["state"] in {"resting", "quiet"}:
                st.caption(f"恢复建议：{care_state['recovery_hint']}")
            request = animal.get("daily_request") or {}
            if request:
                st.caption(f"今日请求：{request.get('title')} · {'已完成' if request.get('completed') else request.get('hint')}")
            event = animal.get("daily_event") or {}
            if event:
                st.caption(f"每日事件：{event.get('title')} · {event.get('complete_text')}")
            story = animal.get("story") or {}
            if story:
                st.caption(
                    f"伙伴故事：{story.get('completed_chapters', 0)} / {story.get('total_chapters', 1)} · "
                    f"下一段 {story.get('current_title', '继续相处')}"
                )
    else:
        st.write("动物线索：暂无")

    st.download_button(
        "下载今日摘要 JSON",
        data=json.dumps(summary, ensure_ascii=False, indent=2),
        file_name="petmate_today_summary.json",
        mime="application/json",
        use_container_width=True,
    )


def render_parent_settings(child_id: int, settings: dict) -> None:
    st.markdown("### 家长设置")
    outdoor_enabled = st.toggle("允许户外探险", value=settings["outdoor_enabled"], key="parent_outdoor_enabled")
    animal_enabled = st.toggle("允许动物线索", value=settings["animal_clues_enabled"], key="parent_animal_enabled")
    st.markdown("### 好友花园")
    friends_enabled = st.toggle("允许好友花园", value=settings.get("friends_enabled", False), key="parent_friends_enabled")
    garden_help_enabled = st.toggle(
        "允许好友帮忙投喂",
        value=settings.get("garden_help_enabled", True),
        key="parent_garden_help_enabled",
        disabled=not friends_enabled,
    )
    garden_likes_enabled = st.toggle(
        "允许好友送鼓励",
        value=settings.get("garden_likes_enabled", True),
        key="parent_garden_likes_enabled",
        disabled=not friends_enabled,
    )
    st.caption("好友必须由家长批准；不开放陌生人搜索、私聊、评论、位置和路线。")
    distance_goal = st.slider(
        "每日目标距离",
        min_value=100,
        max_value=3000,
        value=settings["daily_distance_goal"],
        step=100,
        key="parent_distance_goal",
    )
    max_distance = st.slider(
        "每日最大计入距离",
        min_value=500,
        max_value=10000,
        value=settings["max_daily_distance"],
        step=500,
        key="parent_max_distance",
    )
    st.markdown("### 伙伴作息")
    sleep_cols = st.columns(2)
    with sleep_cols[0]:
        sleep_start = st.time_input(
            "睡眠开始",
            value=parse_time_value(settings.get("sleep_start", "21:00"), time(21, 0)),
            key="parent_sleep_start",
        )
    with sleep_cols[1]:
        sleep_end = st.time_input(
            "睡眠结束",
            value=parse_time_value(settings.get("sleep_end", "07:00"), time(7, 0)),
            key="parent_sleep_end",
        )
    study_enabled = st.toggle("工作日学习时间安静模式", value=settings.get("study_mode_enabled", True), key="parent_study_enabled")
    study_cols = st.columns(2)
    with study_cols[0]:
        study_start = st.time_input(
            "学习开始",
            value=parse_time_value(settings.get("study_start", "08:00"), time(8, 0)),
            key="parent_study_start",
            disabled=not study_enabled,
        )
    with study_cols[1]:
        study_end = st.time_input(
            "学习结束",
            value=parse_time_value(settings.get("study_end", "17:00"), time(17, 0)),
            key="parent_study_end",
            disabled=not study_enabled,
        )
    if settings.get("rhythm"):
        st.info(f"当前状态：{settings['rhythm'].get('label')}。{settings['rhythm'].get('parent_message')}")

    if st.button("保存家长设置", type="primary", use_container_width=True, key="save_parent_settings"):
        api_post(
            "/api/parent/settings",
            {
                "child_id": child_id,
                "outdoor_enabled": outdoor_enabled,
                "animal_clues_enabled": animal_enabled,
                "friends_enabled": friends_enabled,
                "garden_help_enabled": garden_help_enabled,
                "garden_likes_enabled": garden_likes_enabled,
                "daily_distance_goal": distance_goal,
                "max_daily_distance": max_distance,
                "sleep_start": format_time_value(sleep_start),
                "sleep_end": format_time_value(sleep_end),
                "study_mode_enabled": study_enabled,
                "study_start": format_time_value(study_start),
                "study_end": format_time_value(study_end),
            },
        )
        rerun()

    st.info("V0 不记录轨迹、不做路线导航、不指定现实目的地。正式产品还需要登录、家长同意、数据删除和异常检测流程。")


def render_install_help() -> None:
    st.markdown("### 添加到 Android 主屏幕")
    st.info("用手机浏览器打开家长端地址，点击浏览器菜单里的“添加到主屏幕”。这是免费的 PWA-like 体验，不需要安装 APK。")


def render_parent_app(child_id: int, settings: dict) -> None:
    st.title("PetMate 家长端")
    st.markdown(
        "<p class='pm-page-lede'>先看今天是否有价值，再决定要不要调整目标和安全边界。</p>",
        unsafe_allow_html=True,
    )
    render_parent_report(child_id)
    render_parent_settings(child_id, settings)
    render_install_help()


def render_watch_mode(child_id: int, adventure: dict, pet_status: dict, encyclopedia: dict) -> None:
    st.markdown("<div class='pm-watch'></div>", unsafe_allow_html=True)
    pet = pet_status["pet"]
    chances = adventure["available_chances"]
    activity = activity_for(adventure)
    rhythm = adventure.get("rhythm", {})
    can_adventure = rhythm.get("can_adventure", True)
    can_interact = rhythm.get("can_interact", True)
    can_feed = rhythm.get("can_feed", True)
    foods = [item for item in pet_status["inventory"] if item["item_type"] == "food" and item["quantity"] > 0]
    active_animal = next(
        (animal for animal in encyclopedia["animals"] if animal_care_state(animal).get("can_interact", True) and not animal["adopted"]),
        None,
    )
    if active_animal is None and encyclopedia["animals"]:
        active_animal = encyclopedia["animals"][0]

    st.title("PetMate Watch")
    render_rhythm_notice(rhythm, compact=True)
    st.metric("今日距离", f"{adventure['distance_meters']}m")
    st.progress(min(adventure["distance_meters"] / max(adventure["tasks"][0]["target"], 1), 1.0), text=adventure["tasks"][0]["title"])

    c1, c2 = st.columns(2)
    c1.metric("能量", adventure["exploration_energy"])
    c2.metric("宠物", f"Lv{pet['level']}")
    c3, c4 = st.columns(2)
    c3.metric("植物机会", chances["plant"])
    c4.metric("动物线索", chances["animal"])
    c5, c6 = st.columns(2)
    c5.metric("活动分钟", f"{activity['active_minutes']}")
    c6.metric("活动能量", activity["activity_energy"])
    render_passport(adventure.get("passport"), compact=True)

    if active_animal:
        life_stage = animal_life_stage(active_animal)
        care_state = animal_care_state(active_animal)
        st.metric("伙伴", active_animal["name"], f"{active_animal['friendship']}/100")
        st.progress(active_animal["friendship"] / 100, text="友好度")
        st.caption(f"{life_stage['label']} · {care_state['label']} · 心情 {active_animal.get('mood', 50)} · 小窝 Lv{active_animal.get('home_level', 1)}")
        render_partner_wish(active_animal, compact=True)
        render_partner_story(active_animal, compact=True)
        render_home_display(active_animal, compact=True)
    else:
        st.info("走到 500m 找线索")

    if st.button("走 100m", use_container_width=True, type="primary", disabled=not can_adventure, key="watch_walk_100"):
        api_post("/api/adventure/walk", walk_payload(child_id, 100))
        rerun()
    if st.button("走 250m", use_container_width=True, disabled=not can_adventure, key="watch_walk_250"):
        api_post("/api/adventure/walk", walk_payload(child_id, 250))
        rerun()
    if st.button("发现植物", use_container_width=True, disabled=chances["plant"] <= 0 or not can_adventure, key="watch_scan"):
        st.session_state.last_scan = api_post(
            "/api/scan/plant",
            {"child_id": child_id, "image_name": "watch_leaf.jpg"},
        )
        rerun()
    if st.button("发现动物线索", use_container_width=True, disabled=chances["animal"] <= 0 or not can_adventure, key="watch_animal"):
        st.session_state.last_animal = api_post("/api/discovery/animal-clue", {"child_id": child_id})
        rerun()
    if active_animal and st.button("互动一次", use_container_width=True, disabled=activity["activity_energy"] < 1 or not can_interact, key="watch_greet"):
        interact_with_animal(child_id, active_animal, "greet")
    if active_animal and st.button("分享食材", use_container_width=True, disabled=activity["activity_energy"] < 2 or not can_interact, key="watch_share"):
        interact_with_animal(child_id, active_animal, "share_food")
    if active_animal and st.button("小探险", use_container_width=True, disabled=activity["activity_energy"] < 4 or not can_interact, key="watch_mini_adventure"):
        interact_with_animal(child_id, active_animal, "mini_adventure")
    if foods and st.button("喂宠物", use_container_width=True, disabled=not can_feed, key="watch_feed"):
        st.session_state.last_feed = api_post(
            "/api/pet/feed",
            {"child_id": child_id, "food_key": foods[0]["item_key"]},
        )
        rerun()

    if "last_scan" in st.session_state:
        scan = st.session_state.last_scan
        st.success(f"发现 {scan['recognition']['name']}，获得 {scan['drops'][0]['item_name']}。")
    elif "last_animal" in st.session_state:
        animal = st.session_state.last_animal["animal_clue"]
        st.success(f"发现 {animal['name']}，友好度 {animal['friendship']}/100。")
    elif "last_interaction" in st.session_state:
        interaction = st.session_state.last_interaction
        st.success(f"{interaction['interaction']['message']} -{interaction['interaction']['energy_cost']}能量")
        feedback = interaction.get("feedback") or {}
        if feedback:
            st.info(feedback.get("partner_line", "我记住了今天的陪伴。"))
    elif adventure["completed"]:
        st.success("今日关卡完成")
    else:
        next_task = first_incomplete_task(adventure)
        st.info(next_task["title"] if next_task else "继续探险")


with st.sidebar:
    st.markdown("### PetMate")
    st.caption("走路探险 V0 成品演示")

    selected_label = st.radio(
        "入口模式",
        list(VIEW_LABELS.keys()),
        index=list(VIEW_LABELS.keys()).index(current_view_label()),
    )
    selected_view = VIEW_LABELS[selected_label]
    if st.query_params.get("view", "full") != selected_view:
        st.query_params["view"] = selected_view

    st.link_button("打开完整演示", "?view=full", use_container_width=True)
    st.link_button("打开家长端", "?view=parent", use_container_width=True)
    st.link_button("打开手表模式", "?view=watch", use_container_width=True)

    child_id = ensure_demo_child()
    child_id = int(st.number_input("当前孩子 ID", min_value=1, value=child_id, step=1))
    st.session_state.child_id = child_id

    st.divider()
    st.markdown("**演示操作**")
    quick_walk = st.selectbox("本次上报距离", [100, 250, 500, 750], index=2, format_func=lambda x: f"{x} 米")
    quick_minutes = st.number_input(
        "本次活动分钟",
        min_value=1,
        max_value=120,
        value=estimate_active_minutes(int(quick_walk)),
        step=1,
    )
    st.caption(f"估算步数：{estimate_steps(int(quick_walk))} 步。未来接手表后可替换为真实设备数据。")
    if st.button("上报走路", use_container_width=True, type="primary"):
        api_post("/api/adventure/walk", walk_payload(child_id, int(quick_walk), int(quick_minutes)))
        rerun()

    if st.button("新建演示孩子", use_container_width=True):
        st.session_state.child_id = create_demo_child()
        reset_result_state()
        rerun()

    st.caption("V0 记录累计距离、步数、活动分钟和估算消耗，不记录轨迹或路线。")


adventure = api_get("/api/adventure/today", child_id=child_id)
pet_status = api_get("/api/pet/status", child_id=child_id)
encyclopedia = api_get("/api/encyclopedia/me", child_id=child_id)
settings = api_get("/api/parent/settings", child_id=child_id)


if selected_view == "parent":
    render_parent_app(child_id, settings)
    st.stop()

if selected_view == "watch":
    render_watch_mode(child_id, adventure, pet_status, encyclopedia)
    st.stop()


tabs = st.tabs(["今日探险册", "扫描发现", "宠物家园", "好友花园", "家长报告", "家长设置"])

with tabs[0]:
    render_today_book(child_id, adventure, pet_status, encyclopedia, settings)

with tabs[1]:
    render_discovery_tab(child_id, adventure)

with tabs[2]:
    render_garden_tab(child_id, pet_status, encyclopedia, adventure)

with tabs[3]:
    render_friend_garden(child_id, settings, encyclopedia, adventure)

with tabs[4]:
    render_parent_report(child_id)

with tabs[5]:
    render_parent_settings(child_id, settings)
    render_install_help()
