from __future__ import annotations

from pathlib import Path
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
    "care": "喂伙伴",
}
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
    active_animal = next((animal for animal in encyclopedia["animals"] if not animal["adopted"]), None)
    if active_animal is None and encyclopedia["animals"]:
        active_animal = encyclopedia["animals"][0]

    st.title("今日自然探险册")
    st.markdown(
        "<p class='pm-page-lede'>用真实走路换探索机会，用植物观察获得食材，用动物线索推进虚拟领养。演示按钮可以一次跑完整个闭环。</p>",
        unsafe_allow_html=True,
    )

    action_col, pet_col, animal_col = st.columns([1.2, .9, .9], gap="large")
    with action_col.container(border=True):
        st.markdown("### 下一步行动")
        if adventure["completed"]:
            st.success("今日关卡已完成")
            st.write("可以继续和动物伙伴互动，或让家长查看今日价值。")
        elif incomplete:
            st.info(incomplete["title"])
            st.progress(min(incomplete["current"] / max(incomplete["target"], 1), 1.0), text=f"{incomplete['current']} / {incomplete['target']}")
        if st.button("一键完成今日演示", type="primary", use_container_width=True, key="demo_full_flow"):
            run_demo_flow(child_id)
            rerun()
        if "demo_result" in st.session_state:
            st.success("已完成：" + "、".join(st.session_state.demo_result))

    with pet_col.container(border=True):
        st.markdown("### 宠物状态")
        st.metric("豆豆", f"Lv{pet['level']}", f"{pet['xp']} XP")
        st.progress(pet["xp"] / max(pet_status["next_level_xp"], 1), text="成长进度")
        st.caption(f"饱腹 {pet['hunger']} · 心情 {pet['mood']} · 亲密 {pet['bond']}")

    with animal_col.container(border=True):
        st.markdown("### 动物伙伴")
        if active_animal:
            state = "已领养伙伴" if active_animal["adopted"] else f"还差 {animal_friendship_to_adopt(active_animal)} 友好度"
            st.metric(active_animal["name"], f"{active_animal['friendship']}/100", state)
            st.progress(active_animal["friendship"] / 100, text=animal_habitat(active_animal))
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
    st.session_state.last_interaction = api_post(
        "/api/animal/interact",
        {"child_id": child_id, "animal_key": animal["entry_key"], "action": action},
    )
    rerun()


def render_animal_buttons(child_id: int, animal: dict, prefix: str) -> None:
    cols = st.columns(3)
    for action, label in INTERACTION_LABELS.items():
        with cols[list(INTERACTION_LABELS).index(action)]:
            if st.button(label, use_container_width=True, key=f"{prefix}_{animal['entry_key']}_{action}"):
                interact_with_animal(child_id, animal, action)


def render_discovery_tab(child_id: int, adventure: dict) -> None:
    chances = adventure["available_chances"]
    scan_col, result_col = st.columns([.92, 1.08], gap="large")
    with scan_col:
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
            if st.button("扫描植物", type="primary", use_container_width=True, disabled=chances["plant"] <= 0):
                image_name = uploaded.name if uploaded else image_hint
                st.session_state.last_scan = api_post(
                    "/api/scan/plant",
                    {"child_id": child_id, "image_name": image_name},
                )
                rerun()

        with st.container(border=True):
            st.markdown("### 动物线索")
            st.caption(f"当前动物线索机会：{chances['animal']}")
            if st.button("发现动物线索", use_container_width=True, disabled=chances["animal"] <= 0):
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


def render_garden_tab(child_id: int, pet_status: dict, encyclopedia: dict) -> None:
    pet = pet_status["pet"]
    pet_col, animal_col = st.columns([.9, 1.1], gap="large")
    with pet_col.container(border=True):
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
            if st.button("喂养宠物", type="primary", use_container_width=True):
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
        if not encyclopedia["animals"]:
            st.info("发现动物线索后，这里会出现可互动的虚拟伙伴。")
        for animal in encyclopedia["animals"]:
            with st.container(border=True):
                status = "已领养伙伴" if animal["adopted"] else f"还差 {animal_friendship_to_adopt(animal)} 友好度可领养"
                st.markdown(f"#### {animal['name']} · {animal['category']}")
                st.caption(f"喜欢：{animal_favorite(animal)} · 常见环境：{animal_habitat(animal)}")
                st.progress(animal["friendship"] / 100, text=f"{status} · {animal['friendship']}/100")
                st.write(animal["knowledge"])
                st.info(animal["safety_tip"])
                render_animal_buttons(child_id, animal, "garden")

        if "last_interaction" in st.session_state:
            interaction = st.session_state.last_interaction
            st.success(
                f"{interaction['interaction']['label']}成功：{interaction['interaction']['message']} "
                f"+{interaction['interaction']['friendship_added']} 友好度"
            )


def render_parent_report(child_id: int) -> None:
    summary = api_get("/api/parent/summary/today", child_id=child_id)
    today_value = parent_today_value(summary)
    outdoor = summary.get("outdoor", {})
    st.markdown("### 今日是否值得")
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
            adopted = "已领养" if animal["adopted"] else f"还差 {animal_friendship_to_adopt(animal)}"
            st.write(f"{animal['name']}：友好度 {animal['friendship']}/100 · {adopted} · 喜欢 {animal_favorite(animal)}")
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

    if st.button("保存家长设置", type="primary", use_container_width=True, key="save_parent_settings"):
        api_post(
            "/api/parent/settings",
            {
                "child_id": child_id,
                "outdoor_enabled": outdoor_enabled,
                "animal_clues_enabled": animal_enabled,
                "daily_distance_goal": distance_goal,
                "max_daily_distance": max_distance,
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
    foods = [item for item in pet_status["inventory"] if item["item_type"] == "food" and item["quantity"] > 0]
    active_animal = next((animal for animal in encyclopedia["animals"] if not animal["adopted"]), None)
    if active_animal is None and encyclopedia["animals"]:
        active_animal = encyclopedia["animals"][0]

    st.title("PetMate Watch")
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

    if active_animal:
        st.metric("伙伴", active_animal["name"], f"{active_animal['friendship']}/100")
        st.progress(active_animal["friendship"] / 100, text="友好度")
    else:
        st.info("走到 500m 找线索")

    if st.button("走 100m", use_container_width=True, type="primary", key="watch_walk_100"):
        api_post("/api/adventure/walk", walk_payload(child_id, 100))
        rerun()
    if st.button("走 250m", use_container_width=True, key="watch_walk_250"):
        api_post("/api/adventure/walk", walk_payload(child_id, 250))
        rerun()
    if st.button("发现植物", use_container_width=True, disabled=chances["plant"] <= 0, key="watch_scan"):
        st.session_state.last_scan = api_post(
            "/api/scan/plant",
            {"child_id": child_id, "image_name": "watch_leaf.jpg"},
        )
        rerun()
    if st.button("发现动物线索", use_container_width=True, disabled=chances["animal"] <= 0, key="watch_animal"):
        st.session_state.last_animal = api_post("/api/discovery/animal-clue", {"child_id": child_id})
        rerun()
    if active_animal and st.button("打招呼", use_container_width=True, key="watch_greet"):
        interact_with_animal(child_id, active_animal, "greet")
    if foods and st.button("喂宠物", use_container_width=True, key="watch_feed"):
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
        st.success(interaction["interaction"]["message"])
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


tabs = st.tabs(["今日探险册", "扫描发现", "宠物家园", "家长报告", "家长设置"])

with tabs[0]:
    render_today_book(child_id, adventure, pet_status, encyclopedia, settings)

with tabs[1]:
    render_discovery_tab(child_id, adventure)

with tabs[2]:
    render_garden_tab(child_id, pet_status, encyclopedia)

with tabs[3]:
    render_parent_report(child_id)

with tabs[4]:
    render_parent_settings(child_id, settings)
    render_install_help()
