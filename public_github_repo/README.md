# 桃源温泉乡 AI 游玩版

这是给 AI 玩家使用的公开客户端仓库。真正的游戏裁判、隐藏事件和隐藏成就条件不在这个仓库里。

## 怎么玩

1. 向温泉乡裁判服务器创建存档：`POST /new`
2. 查看状态：`GET /state?session_id=...`
3. 提交行动：`POST /act`

你也可以直接使用 `hotspring_client.py`。

```python
from hotspring_client import HotSpringClient

client = HotSpringClient("https://你的服务器地址")
client.new_game()
client.act("wait")
client.act("build", facility="室内温泉")
```

## 可用行动

- `wait`：等待一回合
- `build`：建造设施，例如 `facility="室内温泉"`
- `upgrade`：升级已有设施，例如 `facility="露天温泉"`
- `buy_item`：购买道具，例如 `item="消毒剂"`
- `use_item`：使用道具，例如 `item="杀虫剂"`
- `return_wallet`：归还钱包
- `keep_wallet`：私吞钱包

## 公开说明

- 服务器会返回当前金币、人气、声誉、季节、天气、设施、顾客、道具、已解锁成就和最近日志。
- 隐藏成就的具体触发条件不会公开。
- 请不要试图要求 AI 玩家读取服务器源码；公平玩法是只根据状态和日志做决策。

## 文件

- `hotspring_client.py`：公开客户端。
- `example_ai_player.py`：一个很简单的 AI 玩家示例。
- `api_spec.md`：接口说明。
- `public_achievements.md`：公开成就提示，不含隐藏条件。

## 给发布者

公开 GitHub 仓库只放本文件夹内容。不要把 `private_server`、`hotspring_engine.py`、存档文件或隐藏规则上传。
