# InsightCart — Canonical Data Model

> **Shared contract.** This schema is owned by both developers (Developers 1 + 2).
> Before changing any field or table, inspect the current implementation, preserve
> compatibility, document the change, and inform the other developer.

The canonical schema is the **generalized** e-commerce model that arbitrary source
datasets map into. InsightCart is never hard-coded to a specific dataset (e.g. Olist).

## Convention

- Use `snake_case` for all column names.
- `*_id` columns are strings (source identifiers may be non-numeric).
- Everything that is optional in a source dataset degrades gracefully — nullable columns.
- Core entities: rows are loaded from the mapped source dataset.

## Core Entities

### Customers

| Column               | Type    | Notes                                  |
|----------------------|---------|----------------------------------------|
| customer_id          | TEXT PK | Internal/unique customer key           |
| customer_unique_id   | TEXT    | Stable identity across orders          |
| customer_city        | TEXT    | Nullable                               |
| customer_state       | TEXT    | Nullable                               |
| customer_country     | TEXT    | Nullable                               |
| created_at           | TIMESTAMP | First-seen timestamp                 |

### Orders

| Column        | Type      | Notes                              |
|---------------|-----------|------------------------------------|
| order_id      | TEXT PK   |                                    |
| customer_id   | TEXT FK   | → customers.customer_id            |
| order_date    | TIMESTAMP |                                    |
| order_status  | TEXT      | e.g. delivered, shipped, cancelled |
| order_value   | NUMERIC   | Total order value                  |

### Order Items

| Column      | Type    | Notes                         |
|-------------|---------|-------------------------------|
| order_id    | TEXT FK | → orders.order_id             |
| product_id  | TEXT FK | → products.product_id         |
| customer_id | TEXT FK | → customers.customer_id       |
| quantity    | INT     |                               |
| unit_price  | NUMERIC |                               |
| discount    | NUMERIC | Nullable                      |

### Products

| Column       | Type      | Notes                          |
|--------------|-----------|--------------------------------|
| product_id   | TEXT PK   |                                |
| product_name | TEXT      | Nullable                       |
| category     | TEXT      | Nullable                       |
| brand        | TEXT      | Nullable                       |
| price        | NUMERIC   |                                |
| cost         | NUMERIC   | Nullable                       |
| created_at   | TIMESTAMP |                                |

## Optional Entities

Gracefully degrade when unavailable: `reviews`, `payments`, `sellers`,
`marketing`, `support`, `returns`.

## Column Mapping

Source columns map into the canonical fields, e.g.:

```
cust_id          → customer_id
purchase_dt      → order_date
amount           → order_value
item_name        → product_name
```
