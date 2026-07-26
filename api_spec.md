# API Spec

Base URL examples:

- Local: `http://127.0.0.1:8765`
- Official: `https://taoyuan-hotspring.onrender.com`

All responses are JSON.

## Health

`GET /health`

Response:

```json
{"ok": true, "game": "桃源温泉乡"}
```

## New Game

`POST /new`

Request body:

```json
{"detail":"compact"}
```

Response contains:

- `session_id`: save id for this AI player.
- `state`: public game state.
- `detail`: optional, `compact` or `full`; MCP tools default to `compact`.

## Get State

`GET /state?session_id=...&detail=compact`

Returns current public state.

The state includes `log_history_summary`, but not the complete history payload.

## History

`GET /history?session_id=...&page=1&page_size=50&order=newest`

Optional filters:

- `since_turn=20`: only return records from turn 20 onward.
- `search=水质`: only return log messages containing the keyword.
- `order=oldest`: return oldest matching entries first.

The equivalent MCP tool is `hot_spring_get_history`. The server retains up to 5000 structured entries per save. Each entry contains:

- `sequence`
- `turn`
- `season`
- `weather`
- `message`

## Act

`POST /act`

Examples:

```json
{"session_id":"...", "action":"wait"}
```

```json
{"session_id":"...", "action":"build", "facility":"室内温泉"}
```

```json
{"session_id":"...", "action":"clean", "worker":"owner"}
```

```json
{"session_id":"...", "action":"resolve_complaint", "worker":"owner"}
```

```json
{"session_id":"...", "action":"reply_review"}
```

```json
{"session_id":"...", "action":"promote_listing"}
```

```json
{"session_id":"...", "action":"make_video", "promoter":"网红博主", "detail":"compact"}
```

- `worker` 可使用 `owner`、员工内部编号或员工显示名。指定员工不在岗时，行动会明确失败，不会自动换人。
- `promoter` 可使用 `老板自拍` 或 `网红博主`。网红推广花费 120 金币，并要求达到公开条件。
- `detail` 可使用 `compact` 或 `full`。精简模式适合日常游玩，完整模式适合查阅历史档案。

The server returns the result state after the action.

Special guest story choice:

```json
{"session_id":"...", "action":"story_choice", "guest":"杰夫·贝索斯", "choice":"坚持慢生活"}
```

When a save already has `pending_story_choice`, a valid choice clears the pending state without consuming AP or advancing the date. For compatibility with different AI clients, the server also recognizes an exact legal option supplied through `story`, `facility`, or directly as `action`.

## Operate Day

`POST /operate-day`

```json
{
  "session_id": "...",
  "actions": [
    {"action": "clean", "worker": "employee"},
    {"action": "inspect_water", "worker": "owner"}
  ]
}
```

- 工作日共有 3 AP，周末/节假日共有 4 AP。
- AP 每天重置，不累积；`pause` 会深度清洁并清除已有虫害，然后直接结束当天。停业日不会滋生或传播虫害。
- `story_choice` 不消耗 AP 或推进日期。单独提交选择后，当天仍可继续经营；也可以把选择和后续行动放在同一次 `operate-day` 请求中。
- `hot_spring_execute_plan` 遇到待处理剧情时会先检查当前步骤是否为合法选择；合法选择会执行，不会再被 `decision` 状态提前拦截。
- 员工走神只影响 `clean`、`regular_water`、`restock` 等维护行动，不影响 `build` 和 `upgrade`。
- `upgrade` 每次只提升 1 级，设施最高为 `Lv.5`。
- `resolve_complaint` 消耗 1 AP 和补偿金；客诉只有整改完成后才会恢复声誉，逾期会追加赔偿。
- `community_service` 消耗 1 AP 和 120 金币，要求卫生与水质合格，可有限恢复声誉并有 3 天冷却。
- 点评行动包括 `reply_review`、`compensate_review`、`promote_listing`、`invite_reviewer` 和 `buy_fake_reviews`，均消耗 1 AP。
- 人气只提高评价出现概率，不直接改变星级；声誉影响回复成功率；星级由实际顾客体验和经营状态决定。
- `promote_listing` 只增加三天曝光，不保证好评。`buy_fake_reviews` 会累积异常指数，并可能触发删评、浮动罚款和三天限流。
- `team_build` 是独立的整日行动，会自动暂停营业并结束当天，无需先传 `pause`。它提高员工默契，但不会降低偷懒率或提高工作效率。
- 计划中连续写入 `pause`、`team_build` 时，服务器会自动把两步合并成同一天的聚餐行动。

## Economy

- 正常营业按当日营业额扣除 10% 营业税；人气达到 80 后按 12% 扣除。
- 日常成本还包括人工、维护、水电、洗涤耗材、周末加班与周期合规费用。
- 安全、消防、卫生、水质和重大客诉罚款按近期营业额与设施规模浮动。

## Review Platform

`review_platform` contains the independent 「桃源点评」state:

- `average` / `display`
- `active_reviews` and `star_counts`
- `real_reviews`, `professional_reviews`, `fake_reviews`
- `unresolved_negative`
- `promotion_turns`, `suspicion`, `suspension_turns`
- `recent_reviews`, `total_spend`, `penalties_paid`

## State Fields

Common fields include:

- `turn`
- `gold`
- `popularity`
- `reputation`
- `season`
- `weather`
- `daily_expense`
- `expense_breakdown`
- `log_history_summary`
- `facilities`
- `guests`
- `operations`
- `staff`
- `staff_teamwork`
- `achievements`
- `next_day`
- `tips`
- `log`

The state intentionally does not expose hidden achievement conditions or the full event table.

`expense_breakdown` contains labor, standard and hidden facility maintenance, guest consumables, weather costs, incident repairs, modifiers, and the final total. High-level facilities use a progressively steeper maintenance curve.
