# InsightCart — API Conventions

> **Shared contract.** Owned by both developers. Agree changes before
> implementing; preserve backward compatibility.

## Base

- All endpoints are under the `/api` prefix.
- The root API router `backend/app/api/router.py` mounts every domain router.
- Responses are JSON. Errors use FastAPI's default `{"detail": "..."}` shape.

## Health

```
GET /api/health
→ 200 {"status": "ok", "environment": "development"}
```

## Domain routers

| Prefix           | Owner        | File                       |
|------------------|--------------|----------------------------|
| `/api/customers` | Developer 1  | `backend/app/api/customers.py` |
| `/api/products`  | Developer 2  | `backend/app/api/products.py`  |
| `/api/business`  | Developer 2  | `backend/app/api/business.py`  |
| `/api/opportunities` | Developer 2 | `backend/app/api/opportunities.py` |
| `/api/data`      | Both         | `backend/app/api/upload.py` |
| `/api/ml`        | Both         | `backend/app/api/ml.py`     |

## Resource conventions

- List endpoints: `GET /api/customers` → `{"items": [...], "total": n}`.
- Detail endpoints: `GET /api/customers/{id}` → object.
- Insights/opportunities are returned as a consistent object:
  `{id, type, severity, title, summary, evidence, business_impact, recommended_action, confidence}`.
- Human-friendly display values by default; raw technical metrics available
  behind a `technical` or `details` field.

> The full planned endpoint list is documented in `README.md` → "API Structure".

## Ask Your Data

| Prefix | Owner | File |
|---|---|---|
| `/api/ask` | Developer 2 | `backend/app/api/ask.py` |

```
POST /api/ask
{"question": "Show me last month's best customer.", "mode": "engine", "clarifications": []}
-> {"status": "needs_clarification", "clarifications": [{"term": "best_customer", "options": [...]}], ...}

POST /api/ask   (same question + {"clarifications": [{"term": "best_customer", "option_id": "orders"}]})
-> {"status": "answered", "sql": "...", "columns": [...], "rows": [...], "assumptions": [...], ...}
```

`status` is one of `needs_clarification | answered | unsupported | rejected | error` (HTTP 200);
malformed requests return 422. Full contract: `docs/ask/PRD.md` §6.
