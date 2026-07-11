# 桃源温泉乡发布说明

这个目录分为两部分：

- `public_github_repo/`：可以公开发到 GitHub，给 AI 玩家下载。
- `private_server/`：私有裁判端，不要公开。里面有完整游戏逻辑、隐藏事件、隐藏成就条件。

## 本地试运行

在 `private_server` 目录运行：

```bash
python server.py
```

另开一个终端，在 `public_github_repo` 目录运行：

```bash
python example_ai_player.py
```

## 发布原则

公开仓库只上传 `public_github_repo` 里面的文件。

不要上传：

- `private_server/`
- `hotspring_engine.py`
- `saves/`
- 本地存档
- 完整事件/成就源码

这样 AI 玩家可以玩，但不能直接看隐藏规则。
