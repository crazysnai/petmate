# PetMate Adventure V0

PetMate 是一个儿童户外自然探险宠物产品原型。本版本用同一个 Streamlit 应用完成三端演示：

- 完整网页演示：`?view=full`
- 家长端 PWA-like 网页：`?view=parent`
- 小天才手表小屏原型：`?view=watch`

核心闭环：

```text
走路/步数/活动分钟 -> 解锁植物/动物发现机会 -> 扫描植物获得食材和知识
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
- 新增“探险护照”：像多邻国一样可持续扩展徽章，当前包含户外、植物、动物、图鉴、伙伴互动、活动分钟、喂养和领养等徽章。
- 展示累计距离、步数、活动分钟、活动能量和估算消耗。
- 植物/动物发现卡片展示知识点、安全提示、掉落资源和任务进度。

家长端：

- 展示“今日是否值得”、户外距离、步数、活动分钟、估算消耗、完成情况、学到的知识、植物/动物发现、安全提醒。
- 展示探险护照、伙伴故事进度和下一步建议，方便家长复盘孩子当天的正向收获。
- 支持设置户外探险开关、动物线索开关、每日目标距离、每日最大计入距离。
- 支持好友花园开关、好友帮忙投喂开关、好友送鼓励开关；好友必须经过家长批准。
- 支持“伙伴作息”：睡眠时间、工作日学习时间安静模式、学习开始/结束时间。
- 睡眠和学习安静模式下，孩子端不能消耗活动能量、唤醒伙伴、喂养或刷任务，只保留图鉴和回忆查看。
- 提供 Android 浏览器“添加到主屏幕”的 PWA-like 使用说明。

手表模式：

- 小屏查看今日距离、探索能量、活动能量、活动分钟、植物机会、动物线索、宠物状态、动物伙伴状态。
- 小屏展示下一枚护照徽章、伙伴今日愿望和故事进度。
- 大按钮支持走 100m、走 250m、发现植物、发现动物线索、打招呼、喂宠物。
- 反馈文案短句化，保留安全边界。
- 睡眠/学习时段按钮会禁用，提示伙伴正在休息或安静陪伴学习。

动物伙伴：

- 动物有友好度、领养状态、喜欢的食材、常见环境、最近互动反馈。
- 支持观察、打招呼、分享食材、一起玩、小探险、布置小窝六种虚拟互动。
- 每次互动会消耗活动能量，孩子需要通过走路和户外活动赚取互动机会。
- 动物有心情、信任、好奇心、小窝等级和最近记忆。
- 每个伙伴有今日请求，例如看一种植物、活动 5 分钟、慢慢走 300 米。
- 伙伴愿望升级为“每日事件卡”：包含今日场景、愿望目标、完成反馈、奖励和安全提示。
- 每日伙伴愿望会展示完成奖励，完成后再互动会推进伙伴故事反馈。
- 每个伙伴有故事章节：第一次相遇、记住你的方式、成为同行伙伴、一段自然回忆、留下纪念物。
- 小窝装饰先做展示：根据小窝等级自动显示已摆放装饰和下一件装饰，不做复杂编辑器。
- 伙伴有本地规则智能反馈：根据性格、状态、今天发现的植物和互动动作生成动作描写、伙伴一句话、知识关联和下一步建议。
- 动物有长期生命周期：初遇、熟悉、同行、远行准备、回到自然。
- 长期没有互动或状态过低时，伙伴会先进入“自然休养”，再长期未恢复才“回到自然”。
- 回到自然不删除伙伴，图鉴、名字、最近记忆和纪念物会保留，未来重新发现线索后有机会再遇见。
- 友好度达到 100 后显示为“已领养伙伴”。

好友花园：

- V0 是家长授权的轻社交演示，不开放陌生人搜索、私聊、评论、定位或路线。
- 可查看已批准好友的伙伴、小窝、成长阶段、护照等级和最近发现。
- 支持每天给每个好友“送一片叶子”和“帮忙投喂”各一次，用于验证分享和互助动机。
- 支持好友共同任务展示：一起走路、一起认识植物、互送叶子；只合并线上进度，不要求同一地点或同时在线。

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
- 步数、活动分钟和消耗第一版可由原型估算；未来接入手表后替换为真实设备数据。
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
