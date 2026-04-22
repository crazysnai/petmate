# PetMate 免费部署说明

## 约束

- 不使用付费服务。
- 不在 C 盘安装新软件。
- 不提交账号密码、验证码、Cookie 或浏览器登录态。
- GitHub、Streamlit Community Cloud 的登录和授权由用户在浏览器中手动完成。

## GitHub 网页上传

当前电脑没有可用的 `git` 命令，所以优先走 GitHub 网页上传：

1. 打开 GitHub，创建一个新仓库，例如 `petmate-adventure`。
2. 上传 `F:\renwu\petmate\dev` 目录内的文件和文件夹。
3. 确保仓库根目录里能看到：
   - `streamlit_app.py`
   - `requirements.txt`
   - `.streamlit/config.toml`
   - `app/`
   - `scripts/`
   - `static/`

不要上传个人账号、密码、验证码截图或浏览器缓存。

## Streamlit Community Cloud

1. 打开 Streamlit Community Cloud。
2. 选择 GitHub 仓库。
3. Main file path 填：

```text
streamlit_app.py
```

4. Python 依赖会从 `requirements.txt` 安装。
5. 部署成功后记录公开 URL。

## 访问入口

假设部署后的地址是：

```text
https://your-app.streamlit.app
```

则入口为：

- 完整演示：`https://your-app.streamlit.app/?view=full`
- 家长端：`https://your-app.streamlit.app/?view=parent`
- 手表原型：`https://your-app.streamlit.app/?view=watch`

同一个地址即可覆盖网页端、家长手机端和小天才手表小屏原型。

## 手机添加到主屏幕

Android 浏览器：

1. 用手机打开家长端 URL。
2. 浏览器菜单选择“添加到主屏幕”。
3. 桌面图标会打开家长端入口。

说明：这是 PWA-like 原型，不是上架 APK。

