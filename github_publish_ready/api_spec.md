# API Spec

Base URL examples:

- Local: `http://127.0.0.1:8765`
- Deployed: `https://your-domain.example`

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
{}
```

Response contains:

- `session_id`: save id for this AI player.
- `state`: public game state.

## Get State

`GET /state?session_id=...`

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
{"session_id":"...", "action":"buy_item", "item":"消毒剂"}
```

The server returns the result state after the action.

## State Fields

Common fields include:

- `turn`
- `gold`
- `popularity`
- `reputation`
- `season`
- `weather`
- `facilities`
- `guests`
- `items`
- `achievements`
- `shop`
- `tips`
- `log`

The state intentionally does not expose hidden achievement conditions or the full event table.
