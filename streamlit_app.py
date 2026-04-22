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
      [data-testid="stAppViewContainer"] {
        background:
          radial-gradient(circle at 10% 4%, rgba(47, 125, 87, .13), transparent 28rem),
          radial-gradient(circle at 96% 15%, rgba(184, 111, 42, .08), transparent 24rem),
          linear-gradient(180deg, #f6f3ec 0%, #edf3ed 100%);
      }
      [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid rgba(36, 53, 43, .12);
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
        color: #24352b !important;
      }
      [data-testid="stAlert"] *,
      [data-testid="stNotification"] *,
      [data-testid="stException"] * {
        color: inherit !important;
      }
      .block-container {
        padding-top: 1.6rem;
        max-width: 1200px;
      }
      h1, h2, h3 {
        letter-spacing: 0 !important;
      }
      .pm-hero {
        padding: 1.45rem 0 1.05rem 0;
        border-bottom: 1px solid rgba(36, 53, 43, .14);
        margin-bottom: 1rem;
      }
      .pm-brand {
        font-size: .82rem;
        text-transform: uppercase;
        letter-spacing: .08rem;
        color: #2f7d57;
        font-weight: 800;
      }
      .pm-title {
        font-size: clamp(2rem, 5vw, 4.7rem);
        line-height: .96;
        margin: .35rem 0 .55rem 0;
        font-weight: 900;
        color: #24352b;
      }
      .pm-subtitle {
        font-size: 1.05rem;
        line-height: 1.65;
        max-width: 820px;
        color: rgba(36, 53, 43, .78);
      }
      .pm-strip {
        display: flex;
        gap: .65rem;
        flex-wrap: wrap;
        margin-top: 1rem;
      }
      .pm-chip {
        border: 1px solid rgba(36, 53, 43, .14);
        background: rgba(255,255,255,.72);
        padding: .45rem .7rem;
        border-radius: 999px;
        font-size: .88rem;
        color: #24352b;
      }
      .pm-panel {
        border: 1px solid rgba(36, 53, 43, .12);
        background: rgba(255,255,255,.82);
        border-radius: 8px;
        padding: 1rem 1.1rem;
        min-height: 116px;
      }
      .pm-kicker {
        color: #2f7d57;
        font-weight: 800;
        font-size: .8rem;
        text-transform: uppercase;
      }
      .pm-big-number {
        font-size: 2.55rem;
        line-height: 1;
        font-weight: 900;
        color: #24352b;
        margin: .35rem 0;
      }
      .pm-muted {
        color: rgba(36, 53, 43, .66);
      }
      button[kind="primary"] {
        background: #2f7d57 !important;
        border-color: #2f7d57 !important;
      }
      @media (max-width: 760px) {
        .pm-stage {
          grid-template-columns: 1fr;
        }
        .pm-title {
          font-size: 2.15rem;
        }
        .pm-panel {
          min-height: auto;
        }
        div[data-testid="column"] {
          width: 100% !important;
          flex: 1 1 100% !important;
        }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


VIEW_LABELS = {
    "完整演示": "full",
    "家长端": "parent",
    "手表模式": "watch",
}
VIEW_BY_KEY = {value: key for key, value in VIEW_LABELS.items()}


def current_view_label() -> str:
    raw_view = st.query_params.get("view", "full")
    if isinstance(raw_view, list):
        raw_view = raw_view[0] if raw_view else "full"
    return VIEW_BY_KEY.get(str(raw_view), "完整演示")


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


def rerun() -> None:
    st.rerun()


def render_metric_panel(label: str, value: str, note: str) -> None:
    st.metric(label, value)
    st.caption(note)


def render_task(task: dict) -> None:
    done = "完成" if task["completed"] else "进行中"
    st.markdown(f"**{task['title']}** · {done}")
    ratio = task["current"] / task["target"] if task["target"] else 0
    st.progress(min(ratio, 1.0), text=f"{task['current']} / {task['target']}")


def render_path(adventure: dict) -> None:
    distance = adventure["distance_meters"]
    chances = adventure["available_chances"]
    completed = adventure["completed"]
    nodes = [
        ("起步", "打开今日探险", True),
        ("100m", "探索能量 +1", distance >= 100),
        ("250m", "植物机会 +1", distance >= 250 or chances["plant"] > 0),
        ("500m", "动物线索 +1", distance >= 500 or chances["animal"] > 0),
        ("完成", "领取关卡奖励", completed),
    ]
    cols = st.columns(len(nodes))
    done_count = 0
    for col, (title, copy, done) in zip(cols, nodes):
        if done:
            done_count += 1
        with col:
            st.markdown(f"**{'完成' if done else '待解锁'}**")
            st.metric(title, "已解锁" if done else "未解锁")
            st.caption(copy)
    st.progress(done_count / len(nodes), text=f"成就路径 {done_count}/{len(nodes)}")


def compact_names(items: list[dict], fallback: str) -> str:
    return "、".join(item["name"] for item in items) if items else fallback


def render_parent_report(child_id: int) -> None:
    summary = api_get("/api/parent/summary/today", child_id=child_id)
    st.markdown("### 今日摘要")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("走路距离", f"{summary['outdoor']['distance_meters']}m")
    m2.metric("植物扫描", summary["discoveries"]["plant_scan_count"])
    m3.metric("动物线索", summary["discoveries"]["animal_clue_count"])
    m4.metric("今日 XP", summary["adventure"]["xp"])

    st.markdown("### 家长可读结论")
    if summary["adventure"]["completed"]:
        st.success("今天已完成一次完整自然探险：走路、植物观察、动物线索和宠物照顾都已发生。")
    else:
        st.info("今天还没有完成完整探险，建议优先完成未结束的关卡任务。")

    st.markdown("### 关卡进度")
    for task in summary["adventure"]["tasks"]:
        render_task(task)

    st.markdown("### 发现内容")
    st.write("植物：", "、".join(summary["discoveries"]["plants"]) if summary["discoveries"]["plants"] else "暂无")
    if summary["discoveries"]["animals"]:
        for animal in summary["discoveries"]["animals"]:
            st.write(f"{animal['name']}：友好度 {animal['friendship']}/100")
    else:
        st.write("动物线索：暂无")

    st.markdown("### 安全提醒")
    for note in summary["safety_notes"]:
        st.info(note)

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

    st.info("V0 的安全策略是奖励已经发生的走路行为，而不是把孩子引导到指定现实地点。正式产品还需要登录、家长同意、数据删除、异常检测和更细的未成年人保护流程。")


def render_install_help() -> None:
    st.markdown("### 添加到 Android 主屏幕")
    st.info("用手机浏览器打开家长端地址，点浏览器菜单里的“添加到主屏幕”。这是免费的 PWA-like 体验，不需要安装 APK，也不需要上架应用商店。")


def render_watch_mode(child_id: int, adventure: dict, pet_status: dict, encyclopedia: dict) -> None:
    pet = pet_status["pet"]
    chances = adventure["available_chances"]
    foods = [item for item in pet_status["inventory"] if item["item_type"] == "food" and item["quantity"] > 0]
    last_animal = encyclopedia["animals"][-1] if encyclopedia["animals"] else None

    st.markdown("### PetMate Watch")
    st.markdown("## 今天的小探险")
    stat_cols = st.columns(2)
    stat_cols[0].metric("今日距离", f"{adventure['distance_meters']}m")
    stat_cols[1].metric("探索能量", adventure["exploration_energy"])
    chance_cols = st.columns(2)
    chance_cols[0].metric("植物机会", chances["plant"])
    chance_cols[1].metric("动物线索", chances["animal"])

    st.progress(min(adventure["distance_meters"] / max(adventure["tasks"][0]["target"], 1), 1.0), text=adventure["tasks"][0]["title"])
    st.metric("宠物豆豆", f"Lv{pet['level']}", f"{pet['xp']} XP")

    action_cols = st.columns(2)
    with action_cols[0]:
        if st.button("走 100m", use_container_width=True, type="primary", key="watch_walk_100"):
            api_post("/api/adventure/walk", {"child_id": child_id, "distance_delta_meters": 100})
            rerun()
    with action_cols[1]:
        if st.button("走 250m", use_container_width=True, key="watch_walk_250"):
            api_post("/api/adventure/walk", {"child_id": child_id, "distance_delta_meters": 250})
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

    if foods:
        if st.button(f"喂 {foods[0]['item_name']}", use_container_width=True, key="watch_feed"):
            st.session_state.last_feed = api_post(
                "/api/pet/feed",
                {"child_id": child_id, "food_key": foods[0]["item_key"]},
            )
            rerun()

    if "last_scan" in st.session_state:
        scan = st.session_state.last_scan
        st.success(f"发现 {scan['recognition']['name']}，获得 {scan['drops'][0]['item_name']}")
    elif last_animal:
        st.info(f"最近线索：{last_animal['name']}，友好度 {last_animal['friendship']}/100")
    else:
        st.info("继续走路，解锁发现机会。")

    if adventure["completed"]:
        st.success("今日关卡完成")


with st.sidebar:
    st.markdown("### PetMate")
    st.caption("走路探险 V0 原型")

    selected_label = st.radio(
        "入口模式",
        list(VIEW_LABELS.keys()),
        index=list(VIEW_LABELS.keys()).index(current_view_label()),
    )
    selected_view = VIEW_LABELS[selected_label]

    st.markdown(
        """
        <small>
        <a href="?view=full" target="_self">完整演示</a> ·
        <a href="?view=parent" target="_self">家长端</a> ·
        <a href="?view=watch" target="_self">手表模式</a>
        </small>
        """,
        unsafe_allow_html=True,
    )

    child_id = ensure_demo_child()
    child_id = int(st.number_input("当前孩子 ID", min_value=1, value=child_id, step=1))
    st.session_state.child_id = child_id

    st.divider()
    st.markdown("**演示操作**")
    quick_walk = st.selectbox("本次上报距离", [100, 250, 500, 750], index=2, format_func=lambda x: f"{x} 米")
    if st.button("上报走路", use_container_width=True, type="primary"):
        api_post("/api/adventure/walk", {"child_id": child_id, "distance_delta_meters": quick_walk})
        rerun()

    if st.button("新建演示孩子", use_container_width=True):
        st.session_state.child_id = create_demo_child()
        for key in ["last_scan", "last_animal", "last_feed"]:
            st.session_state.pop(key, None)
        rerun()

    st.caption("V0 只记录累计距离，不记录轨迹或路线。")


adventure = api_get("/api/adventure/today", child_id=child_id)
pet_status = api_get("/api/pet/status", child_id=child_id)
pet = pet_status["pet"]
encyclopedia = api_get("/api/encyclopedia/me", child_id=child_id)
settings = api_get("/api/parent/settings", child_id=child_id)


st.markdown(
    """
    <div class="pm-hero">
      <div class="pm-brand">PetMate Adventure</div>
      <div class="pm-title">走路，发现，领养自然伙伴。</div>
      <div class="pm-subtitle">
        孩子不用被导航到指定地点。只要在家长允许的边界内多走一段路，就会解锁植物扫描和动物线索，像闯关一样推进自然探险。
      </div>
      <div class="pm-strip">
        <span class="pm-chip">距离驱动</span>
        <span class="pm-chip">多邻国式关卡</span>
        <span class="pm-chip">植物图鉴</span>
        <span class="pm-chip">虚拟动物领养</span>
        <span class="pm-chip">家长安全报告</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


if selected_view == "parent":
    st.markdown("### 家长端")
    render_parent_report(child_id)
    render_parent_settings(child_id, settings)
    render_install_help()
    st.stop()


if selected_view == "watch":
    render_watch_mode(child_id, adventure, pet_status, encyclopedia)
    st.stop()


tabs = st.tabs(["今日探险", "扫描发现", "宠物家园", "家长报告", "家长设置"])


with tabs[0]:
    left, mid, right = st.columns([1.1, 1, 1], gap="large")
    with left:
        render_metric_panel("累计距离", f"{adventure['distance_meters']}m", f"今日目标 {settings['daily_distance_goal']}m")
    with mid:
        render_metric_panel("探索能量", str(adventure["exploration_energy"]), "每 100m +1")
    with right:
        chances = adventure["available_chances"]
        render_metric_panel("发现机会", f"{chances['plant']} / {chances['animal']}", "植物 / 动物")

    st.markdown("### 小小观察员 · 成就路径")
    render_path(adventure)

    st.markdown("### 今日关卡")
    task_cols = st.columns(2, gap="large")
    for index, task in enumerate(adventure["tasks"]):
        with task_cols[index % 2]:
            render_task(task)

    if adventure["completed"]:
        st.success("今日关卡已完成，宠物获得了完成奖励。")
    else:
        st.info("继续走路、扫描植物、发现动物线索并喂养宠物，就能完成今日关卡。")


with tabs[1]:
    scan_col, result_col = st.columns([.95, 1.05], gap="large")
    with scan_col:
        st.markdown("### 植物扫描")
        image_hint = st.selectbox(
            "选择一张模拟图片",
            ["dandelion_test.jpg", "clover_test.jpg", "plane_leaf_test.jpg"],
            format_func=lambda x: {
                "dandelion_test.jpg": "蒲公英测试图",
                "clover_test.jpg": "三叶草测试图",
                "plane_leaf_test.jpg": "梧桐叶测试图",
            }[x],
        )
        uploaded = st.file_uploader("也可以上传一张植物照片", type=["jpg", "jpeg", "png"])
        if st.button("扫描植物", type="primary", use_container_width=True):
            image_name = uploaded.name if uploaded else image_hint
            st.session_state.last_scan = api_post(
                "/api/scan/plant",
                {"child_id": child_id, "image_name": image_name},
            )
            rerun()

        st.markdown("### 动物线索")
        if st.button("发现动物线索", use_container_width=True):
            st.session_state.last_animal = api_post("/api/discovery/animal-clue", {"child_id": child_id})
            rerun()

        st.caption("动物线索用于虚拟领养进度，不鼓励靠近真实动物。")

    with result_col:
        if "last_scan" in st.session_state:
            scan = st.session_state.last_scan
            recognition = scan["recognition"]
            st.markdown("### 最近植物发现")
            st.markdown(f"**{recognition['name']}** · {recognition['category']}")
            st.progress(recognition["confidence"], text=f"模拟可信度 {recognition['confidence']:.0%}")
            st.write(scan["knowledge_card"]["knowledge"])
            st.info(scan["knowledge_card"]["safety_tip"])
            st.write("掉落：", "、".join(item["item_name"] for item in scan["drops"]))
        else:
            st.markdown("### 最近植物发现")
            st.write("走到 250 米会解锁植物发现机会。")

        st.divider()
        if "last_animal" in st.session_state:
            animal = st.session_state.last_animal["animal_clue"]
            card = st.session_state.last_animal["knowledge_card"]
            st.markdown("### 最近动物线索")
            st.markdown(f"**{animal['name']}** · {animal['category']} · 友好度 {animal['friendship']}/100")
            st.progress(animal["friendship"] / 100)
            st.write(card["knowledge"])
            st.info(card["safety_tip"])
        else:
            st.markdown("### 最近动物线索")
            st.write("走到 500 米会解锁动物线索机会。")


with tabs[2]:
    pet_col, book_col = st.columns([.9, 1.1], gap="large")
    with pet_col:
        st.markdown("### 豆豆的状态")
        st.metric("等级", f"Lv{pet['level']}", f"{pet['xp']} XP")
        st.progress(pet["xp"] / pet_status["next_level_xp"], text=f"下一级需要 {pet_status['next_level_xp']} XP")
        stat_cols = st.columns(3)
        stat_cols[0].metric("饱腹", pet["hunger"])
        stat_cols[1].metric("心情", pet["mood"])
        stat_cols[2].metric("亲密", pet["bond"])

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

    with book_col:
        st.markdown("### 自然图鉴")
        st.write("植物：", compact_names(encyclopedia["plants"], "尚未发现"))
        for animal in encyclopedia["animals"]:
            st.markdown(f"**{animal['name']}** · {animal['category']}")
            st.progress(animal["friendship"] / 100, text=f"虚拟领养友好度 {animal['friendship']}/100")
            st.caption(animal["safety_tip"])
            if animal["adopted"]:
                st.success("已成为家园伙伴")


with tabs[3]:
    render_parent_report(child_id)


with tabs[4]:
    render_parent_settings(child_id, settings)
    render_install_help()
