import sys

from hotspring_client import HotSpringClient

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def safe_act(client: HotSpringClient, action: str = "wait", **kwargs):
    result = client.act(action, **kwargs)
    action_result = result["result"].get("action_result", {})
    if action != "wait" and action_result.get("success") is False:
        result = client.act("wait")
    return result


client = HotSpringClient()
client.new_game()

for _ in range(20):
    state = client.state()["state"]
    gold = state["gold"]
    facilities = state["facilities"]

    if gold > 260 and len(facilities) < 3:
        result = safe_act(client, "build", facility="室内温泉")
    elif gold > 700 and facilities:
        result = safe_act(client, "upgrade", facility=facilities[0]["name"])
    else:
        result = safe_act(client, "wait")

    new_state = result["result"]
    print(
        f"第 {new_state['turn']} 回合 | 金币 {new_state['gold']} | "
        f"人气 {new_state['popularity']} | 声誉 {new_state['reputation']} | "
        f"季节 {new_state['season']} | 天气 {new_state['weather']}"
    )
    for line in new_state.get("log", [])[-2:]:
        print("  ", line)
