import sys

from hotspring_client import HotSpringClient

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROUNDS = 24
BUILD_ORDER = ["室内温泉", "餐厅", "休息厅", "小卖部", "桑拿房"]


def safe_act(client: HotSpringClient, action: str = "wait", **kwargs):
    result = client.act(action, **kwargs)
    action_result = result["result"].get("action_result", {})
    if action != "wait" and action_result.get("success") is False:
        return client.act("wait")
    return result


def decide(state: dict) -> tuple[str, dict]:
    gold = state["gold"]
    facilities = state["facilities"]
    items = state.get("items", [])
    tips = " ".join(state.get("tips", []))
    reserve = max(180, state.get("daily_expense", 0) * 7)

    if "捡到钱包" in tips:
        return "return_wallet", {}
    if any(f.get("roach") for f in facilities):
        if "杀虫剂" in items:
            return "use_item", {"item": "杀虫剂"}
        if gold >= reserve + 40:
            return "buy_item", {"item": "杀虫剂"}
    if "水质报警" in tips:
        if "消毒剂" in items:
            return "use_item", {"item": "消毒剂"}
        if gold >= reserve + 50:
            return "buy_item", {"item": "消毒剂"}
    if state["reputation"] < 60 and gold >= reserve + 60:
        return "buy_item", {"item": "公关稿"}

    owned = {f["name"] for f in facilities}
    for name in BUILD_ORDER:
        if name not in owned and gold >= reserve + 220:
            return "build", {"facility": name}

    upgradeable = sorted(
        (f for f in facilities if not f.get("closed") and f["level"] < 5),
        key=lambda f: (f["level"], f["income"]),
    )
    if upgradeable and gold >= reserve + 500:
        return "upgrade", {"facility": upgradeable[0]["name"]}
    return "wait", {}


client = HotSpringClient()
client.new_game()

for _ in range(ROUNDS):
    state = client.state()["state"]
    action, kwargs = decide(state)
    result = safe_act(client, action, **kwargs)
    new_state = result["result"]
    print(
        f"第 {new_state['turn']} 回合 | {action} | 金币 {new_state['gold']} | "
        f"人气 {new_state['popularity']} | 声誉 {new_state['reputation']} | "
        f"季节 {new_state['season']} | 天气 {new_state['weather']}"
    )
    for line in new_state.get("log", [])[-2:]:
        print("  ", line)
