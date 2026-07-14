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
{"session_id":"...", "action":"make_video", "promoter":"网红博主", "detail":"compact"}
```

- `worker` 可使用 `owner`、员工内部编号或员工显示名。指定员工不在岗时，行动会明确失败，不会自动换人。
- `promoter` 可使用 `老板自拍` 或 `网红博主`。网红推广花费 120 金币，并要求达到公开条件。
- `detail` 可使用 `compact` 或 `full`。精简模式适合日常游玩，完整模式适合查阅历史档案。

The server returns the result state after the action.

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
- 员工走神只影响 `clean`、`regular_water`、`restock` 等维护行动，不影响 `build` 和 `upgrade`。
- `team_build` 是独立的整日行动，会自动暂停营业并结束当天，无需先传 `pause`。它提高员工默契，但不会降低偷懒率或提高工作效率。
- 计划中连续写入 `pause`、`team_build` 时，服务器会自动把两步合并成同一天的聚餐行动。

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
