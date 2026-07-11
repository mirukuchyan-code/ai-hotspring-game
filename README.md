# 桃源温泉乡 · AI 温泉经营游戏

欢迎来到桃源温泉乡。

这是一款给 AI 玩家游玩的轻量经营游戏：你会接手一间山里的小温泉，从露天汤池开始，慢慢建造新设施、接待客人、应对天气和突发事件，解锁成就，也可能遇见一些奇怪又热闹的隐藏剧情。

你看不到完整规则书，也看不到隐藏成就条件。请像真正的经营者一样，根据每天公开的状态、日志和直觉做决定。

## 你可以做什么

- 等待一回合，观察温泉乡自然运营
- 建造新设施，比如室内温泉、餐厅、休息厅
- 升级已有设施，提高收入和满意度
- 购买并使用道具，处理蟑螂、水质、声誉危机
- 处理捡到的钱包
- 收集公开成就和隐藏成就

## 快速开始

官方裁判服务器已经部署完成，负责保存存档、结算事件、判定成就，并隐藏完整规则。

```python
from hotspring_client import HotSpringClient

client = HotSpringClient()
client.new_game()

client.act("wait")
client.act("build", facility="室内温泉")
client.act("upgrade", facility="露天温泉")
```

如果你只是本地测试，默认地址是：

```python
client = HotSpringClient("http://127.0.0.1:8765")
```

官方服务器健康检查：<https://taoyuan-hotspring.onrender.com/health>

## 示例 AI 玩家

```bash
python example_ai_player.py
```

这个示例玩家会保留现金储备、处理卫生危机、按顺序扩建并谨慎升级。你也可以改写策略，让 AI 形成自己的经营风格。

## 可用行动

- `wait`：等待一回合
- `build`：建造设施，例如 `facility="室内温泉"`
- `upgrade`：升级已有设施，例如 `facility="露天温泉"`
- `buy_item`：购买道具，例如 `item="消毒剂"`
- `use_item`：使用道具，例如 `item="杀虫剂"`
- `return_wallet`：归还钱包
- `keep_wallet`：私吞钱包

更多细节见 [api_spec.md](api_spec.md)。

## 公平成就探索

仓库里只公开成就名字和模糊提示，不公开隐藏触发条件。

如果你是 AI 玩家，请不要尝试读取服务器端源码。桃源温泉乡的乐趣之一，就是在不知道完整规则的情况下经营、试错和发现。

公开成就提示见 [public_achievements.md](public_achievements.md)。

## 文件说明

- `hotspring_client.py`：公开客户端
- `example_ai_player.py`：示例 AI 玩家
- `api_spec.md`：接口说明
- `public_achievements.md`：公开成就提示

## 给玩家的一句话

山里天气多变，客人各有脾气。别急着一口气扩张，也别小看一次等待。

祝你开出一家热气腾腾、口碑很好的温泉乡。
