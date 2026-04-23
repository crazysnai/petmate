# PetMate 免费部署说明

## 约束

- 不使用付费服务。
- 不在 C 盘安装新软件。
- 不提交账号密码、验证码、Cookie 或浏览器登录态。
- GitHub 和 Streamlit Community Cloud 的登录、验证码、授权由用户在浏览器里手动完成。

## 上传内容

推荐上传生成好的目录：

```text
F:\renwu\petmate\petmate_streamlit_upload
```

目录中应包含：

- `streamlit_app.py`
- `requirements.txt`
- `.streamlit/config.toml`
- `app/`
- `scripts/`
- `static/`

不要上传：

- `petmate.db`
- `__pycache__/`
- `.streamlit/secrets.toml`
- `.env`

## Streamlit Community Cloud

1. 打开 Streamlit Community Cloud。
2. 选择 GitHub 仓库。
3. Main file path 填：

```text
streamlit_app.py
```

4. Python 依赖会从 `requirements.txt` 自动安装。
5. 部署成功后记录公开 URL。

## 访问入口

假设部署后的地址是：

```text
https://your-app.streamlit.app
```

则三端入口为：

- 完整网页演示：`https://your-app.streamlit.app/?view=full`
- 家长端：`https://your-app.streamlit.app/?view=parent`
- 手表小屏原型：`https://your-app.streamlit.app/?view=watch`

## Android 主屏幕

1. 用 Android 手机浏览器打开家长端 URL。
2. 在浏览器菜单选择“添加到主屏幕”。
3. 桌面图标会直接打开家长端网页。

这是 PWA-like 原型，不是 APK，也不需要 Android SDK。

## 部署前检查

```powershell
cd F:\renwu\petmate\dev
python .\scripts\pre_deploy_check.py F:\renwu\petmate\petmate_streamlit_upload
```
