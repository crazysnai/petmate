# PetMate Adventure V0

儿童户外自然探险宠物产品的 V0 后端。

核心闭环：

```text
创建孩子和宠物
-> 上报走路距离
-> 解锁植物/动物发现机会
-> 扫描植物获得图鉴和食材
-> 发现动物线索推进虚拟领养
-> 喂养宠物
-> 完成多邻国式今日关卡
-> 家长查看今日摘要
```

## 技术栈

- Python 3.12
- FastAPI
- SQLite
- sqlite3 标准库

## 安装

```powershell
cd F:\renwu\petmate\dev
python -m pip install -r requirements.txt
```

## 启动 API

```powershell
cd F:\renwu\petmate\dev
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

## 启动网页版原型

```powershell
cd F:\renwu\petmate\dev
python -m streamlit run streamlit_app.py --server.port 8501
```

访问：

```text
http://localhost:8501
```

网页版包含：

1. 今日探险：距离、探索能量、植物/动物机会、关卡进度。
2. 扫描发现：植物 mock 扫描、动物线索发现、知识卡和安全提示。
3. 宠物家园：宠物状态、食材喂养、自然图鉴、虚拟领养进度。
4. 家长报告：户外距离、发现内容、今日 XP、任务完成和安全提醒。
5. 家长设置：户外探险开关、动物线索开关、每日目标距离、每日最大计入距离。
6. 手表模式：小屏查看距离、探索能量、发现机会、宠物状态，并用单按钮完成发现反馈。

侧边栏提供：

1. 快速上报走路距离。
2. 新建演示孩子，用于重开一轮演示。
3. 入口模式切换：完整演示、家长端、手表模式。

## 访问入口

本地运行时：

```text
完整演示：http://localhost:8501/?view=full
家长端：http://localhost:8501/?view=parent
手表模式：http://localhost:8501/?view=watch
```

Streamlit Cloud 部署后，把域名替换成线上地址即可：

```text
完整演示：https://your-app.streamlit.app/?view=full
家长端：https://your-app.streamlit.app/?view=parent
手表模式：https://your-app.streamlit.app/?view=watch
```

家长 Android 端第一版使用手机浏览器打开家长端地址，然后通过浏览器菜单“添加到主屏幕”。这是免费的 PWA-like 体验，不是 APK。

## 跑完整自测

```powershell
cd F:\renwu\petmate\dev
python .\scripts\run_demo.py
```

部署前检查：

```powershell
cd F:\renwu\petmate\dev
python .\scripts\pre_deploy_check.py
```

检查 GitHub 上传包：

```powershell
cd F:\renwu\petmate\dev
python .\scripts\pre_deploy_check.py F:\renwu\petmate\petmate_streamlit_upload
```

自测会重置本地 `petmate.db`，然后验证：

1. 创建孩子和宠物。
2. 上报 500 米，解锁植物和动物发现机会。
3. 扫描 2 种植物。
4. 发现 1 个动物线索。
5. 喂养宠物并完成今日关卡。
6. 额外走 250 米并扫描第 3 种植物。
7. 宠物升级到 Lv2。
8. 家长摘要返回今日户外、发现、图鉴、宠物成长和安全提醒。

## P0 API

- `POST /api/child/create`
- `POST /api/pet/create`
- `GET /api/pet/status`
- `GET /api/adventure/today`
- `POST /api/adventure/walk`
- `POST /api/scan/plant`
- `POST /api/discovery/animal-clue`
- `POST /api/pet/feed`
- `GET /api/encyclopedia/me`
- `GET /api/parent/summary/today`
- `GET /api/parent/settings`
- `POST /api/parent/settings`

## V0 安全边界

1. 不指定现实地点。
2. 不做路线导航。
3. 不展示他人位置。
4. 不记录完整轨迹，只记录累计距离和任务完成。
5. 动物只做远距离观察提示和虚拟领养，不鼓励触摸、追赶或投喂。
6. 家长控制每日目标距离和动物线索开关。

## 免费部署建议

优先使用 Streamlit Community Cloud：

1. 把 `F:\renwu\petmate\dev` 推到 GitHub 仓库。
2. 在 Streamlit Community Cloud 选择该仓库。
3. Main file path 填 `streamlit_app.py`。
4. Python 依赖会从 `requirements.txt` 自动安装。

建议不要上传：

- `petmate.db`
- `__pycache__/`
- `.streamlit/secrets.toml`
- `.env`

注意：Streamlit 免费部署适合产品原型和演示，不适合作为正式儿童产品后端。正式上线前需要替换为可靠数据库、登录、权限、合规审计和数据删除能力。
