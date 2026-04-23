# PetMate Adventure V0

PetMate 是一个儿童户外自然探险宠物产品原型。本版本用同一个 Streamlit 应用完成三端演示：

- 完整网页演示：`?view=full`
- 家长端 PWA-like 网页：`?view=parent`
- 小天才手表小屏原型：`?view=watch`

核心闭环：

```text
走路 -> 解锁植物/动物发现机会 -> 扫描植物获得食材和知识
-> 发现动物线索 -> 和动物伙伴互动 -> 喂养宠物
-> 完成今日关卡 -> 家长查看今日价值和安全提醒
```

## 技术栈

- Python 3.12
- Streamlit
- FastAPI TestClient
- SQLite

## 本地启动

```powershell
cd F:\renwu\petmate\dev
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py --server.port 8501
```

本地入口：

```text
完整网页演示：http://localhost:8501/?view=full
家长端：http://localhost:8501/?view=parent
手表模式：http://localhost:8501/?view=watch
```

## 当前功能

完整网页演示：

- 首页是“今日自然探险册”，展示今日任务、下一步行动、宠物状态、最近发现、动物伙伴进度和家长价值摘要。
- 支持“一键完成今日演示”，自动完成 500m、2 次植物扫描、1 次动物线索、动物互动和宠物喂养。
- 三关路径：小小观察员、草地探险家、动物侦探。
- 植物/动物发现卡片展示知识点、安全提示、掉落资源和任务进度。

家长端：

- 展示“今日是否值得”、户外距离、完成情况、学到的知识、植物/动物发现、安全提醒。
- 支持设置户外探险开关、动物线索开关、每日目标距离、每日最大计入距离。
- 提供 Android 浏览器“添加到主屏幕”的 PWA-like 使用说明。

手表模式：

- 小屏查看今日距离、探索能量、植物机会、动物线索、宠物状态、动物伙伴状态。
- 大按钮支持走 100m、走 250m、发现植物、发现动物线索、打招呼、喂宠物。
- 反馈文案短句化，保留安全边界。

动物伙伴：

- 动物有友好度、领养状态、喜欢的食材、常见环境、最近互动反馈。
- 支持观察、打招呼、喂伙伴三种虚拟互动。
- 友好度达到 100 后显示为“已领养伙伴”。

## 自测

```powershell
cd F:\renwu\petmate\dev
python -m py_compile streamlit_app.py app\database.py app\main.py app\schemas.py scripts\pre_deploy_check.py
python .\scripts\run_demo.py
python .\scripts\pre_deploy_check.py
```

检查上传包：

```powershell
python .\scripts\pre_deploy_check.py F:\renwu\petmate\petmate_streamlit_upload
```

## 主要 API

- `POST /api/child/create`
- `POST /api/pet/create`
- `GET /api/pet/status`
- `GET /api/adventure/today`
- `POST /api/adventure/walk`
- `POST /api/scan/plant`
- `POST /api/discovery/animal-clue`
- `POST /api/animal/interact`
- `POST /api/pet/feed`
- `GET /api/encyclopedia/me`
- `GET /api/parent/summary/today`
- `GET /api/parent/settings`
- `POST /api/parent/settings`

## 安全边界

- 不指定现实目的地。
- 不做路线导航。
- 不展示其他人位置。
- 不记录完整轨迹，只记录累计距离和任务完成状态。
- 动物只做远距离观察提示和虚拟领养，不鼓励触摸、追赶或投喂。
- 家长可控制每日目标距离、最大计入距离和动物线索开关。

## 免费部署

优先使用 Streamlit Community Cloud：

1. 上传 `F:\renwu\petmate\petmate_streamlit_upload` 里的文件到 GitHub 仓库。
2. 在 Streamlit Community Cloud 选择该仓库。
3. Main file path 填 `streamlit_app.py`。
4. 部署成功后访问 `https://your-app.streamlit.app/?view=full`。

不要上传：

- `petmate.db`
- `__pycache__/`
- `.streamlit/secrets.toml`
- `.env`

Streamlit 免费部署适合原型演示。正式儿童产品上线前还需要真实账号体系、权限、家长同意、数据删除、合规审计和可靠数据库。
