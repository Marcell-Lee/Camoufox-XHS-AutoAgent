# 小红书发布步骤脚本

请先启动浏览器服务：

```powershell
python 01_launch_server.py
```

然后可以按步骤单独执行：

```powershell
python xhs_publish_steps/01_open_publish_page.py
python xhs_publish_steps/02_ensure_login.py
python xhs_publish_steps/03_fill_title.py
python xhs_publish_steps/04_fill_body.py
python xhs_publish_steps/05_fill_text_note.py
python xhs_publish_steps/06_close_publish_page.py
```

原来的完整流程仍然可以运行：

```powershell
python 03_xiaohongshu_publish.py
```

这些脚本只填写内容，不会点击「发布」按钮。
