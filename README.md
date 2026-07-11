# 桃源温泉乡发布备忘

这是给初初自己看的，不要放到公开 GitHub 首页。

公开仓库请上传 `github_publish_ready/` 里的内容。这个目录已经是仓库根目录结构：

- `README.md`
- `hotspring_client.py`
- `example_ai_player.py`
- `api_spec.md`
- `public_achievements.md`
- `.gitignore`

不要公开上传：

- `private_server/`
- `hotspring_engine.py`
- `saves/`
- 完整事件池
- 隐藏成就触发条件

如果需要让外部 AI 真正能玩，需要先部署 `private_server`，再把公开 README 里的服务器地址换成公网地址。
