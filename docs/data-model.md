# InsightCart — Canonical Data Model

> **Shared contract.** This schema is owned by both developers (Developers 1 + 2).
> Before changing any field or table, inspect the current implementation, preserve
> compatibility, document the change, and inform the other developer.

The canonical schema is the **generalized** e-commerce model that arbitrary source
datasets map into. InsightCart is never hard-coded to a specific dataset (e.g. Olist).

## Conventions

- Use `snake_case` for all column names.
- `*_id` columns are strings (`String(64)`) to support arbitrary source identifiers.
- Everything optional in a source dataset degrades gracefully (nullable columns).
- Core entities: rows are ingested and validated before insertion.

---

## Core Entities

### Customers (`backend/app/models/customer.py`)

| Column               | Type                     | Nullable | Constraints / Index | Notes                                  |
|----------------------|--------------------------|----------|---------------------|----------------------------------------|
| `customer_id`        | `VARCHAR(64)`            | No       | Primary Key, Index  | Unique customer transaction key        |
| `customer_unique_id` | `VARCHAR(64)`            | No       | Index               | Stable identity across multiple orders |
| `customer_city`      | `VARCHAR(128)`           | Yes      |                     | Customer city                          |
| `customer_state`     | `VARCHAR(32)`            | Yes      |                     | Customer state / province              |
| `customer_country`   | `VARCHAR(64)`            | Yes      | Default `'BR'`      | Customer country                       |
| `created_at`         | `TIMESTAMP WITH TIMEZONE`| Yes      | Default `now()`     | First-seen / registration timestamp    |

**Relationships:**
- `orders`: One-to-Many (`Order`), `cascade="all, delete, delete-orphan"`

---

### Orders (`backend/app/models/order.py`)

| Column         | Type                     | Nullable | Constraints / Index                       | Notes                              |
|----------------|--------------------------|----------|-------------------------------------------|------------------------------------|
| `order_id`     | `VARCHAR(64)`            | No       | Primary Key, Index                        | Unique order identifier            |
| `customer_id`  | `VARCHAR(64)`            | No       | Foreign Key (`customers.customer_id`), Index | Reference to customer              |
| `order_date`   | `TIMESTAMP WITH TIMEZONE`| Yes      | Index                                     | Timestamp of purchase              |
| `order_status` | `VARCHAR(32)`            | Yes      | Index                                     | e.g. delivered, shipped, canceled  |
| `order_value`  | `NUMERIC(10, 2)`         | Yes      |                                           | Total monetary value of order      |

**Relationships:**
- `customer`: Many-to-One (`Customer`)

---

### Order Items *(Developer 2 Domain)*

| Column      | Type    | Notes                         |
|-------------|---------|-------------------------------|
| order_id    | TEXT FK | → orders.order_id             |
| product_id  | TEXT FK | → products.product_id         |
| customer_id | TEXT FK | → customers.customer_id       |
| quantity    | INT     |                               |
| unit_price  | NUMERIC |                               |
| discount    | NUMERIC | Nullable                      |

---

### Products *(Developer 2 Domain)*

| Column       | Type      | Notes                          |
|--------------|-----------|--------------------------------|
| product_id   | TEXT PK   |                                |
| product_name | TEXT      | Nullable                       |
| category     | TEXT      | Nullable                       |
| brand        | TEXT      | Nullable                       |
| price        | NUMERIC   |                                |
| cost         | NUMERIC   | Nullable                       |
| created_at   | TIMESTAMP |                                |

---

## Data Validation Rules (`backend/app/services/validation/`)

The `CustomerOrderValidator` validates datasets against these data quality rules:
1. **Critical Missing Keys**: `customer_id`, `customer_unique_id`, and `order_id` cannot be empty or null (`severity: error`).
2. **Duplicate Primary Keys**: Duplicate `customer_id` or `order_id` records are flagged and deduplicated (`severity: error`).
3. **Invalid Dates**: Unparseable date strings or dates outside reasonable historical ranges (`severity: error`/`warning`).
4. **Negative Monetary Values**: `order_value < 0` is flagged and sanitized (`severity: error`).
5. **Foreign Key Integrity**: Orders referencing non-existent `customer_id` values are flagged (`severity: error`).
6. **Missing Geographic Metadata**: Missing state/city is recorded for diagnostics (`severity: warning`).

---

## Ingestion Mappings (`backend/app/services/ingestion/`)

The `CustomerOrderIngestionService` handles automatic mapping from source CSV formats:

```text
Source Column (Olist / Canonical)     → Canonical Target Column
-----------------------------------------------------------------
customer_id / customerId              → customer_id
customer_unique_id / customerUniqueId  → customer_unique_id
customer_city / customerCity          → customer_city
customer_state / customerState        → customer_state
customer_country / customerCountry    → customer_country
order_id / orderId                    → order_id
order_purchase_timestamp / order_date → order_date
order_status / status                 → order_status
order_value / payment_value / amount  → order_value
```

If separate payment records are provided, `payment_value` is aggregated per `order_id`. Customer `created_at` is automatically backfilled to the earliest order date if not explicitly set.

---

## Migrations (`backend/app/db/migrations/`)

- `0001_create_customers_and_orders`: Creates `customers` and `orders` tables with foreign keys and performance indexes.
