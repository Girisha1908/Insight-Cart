# INSIGHTCART TEAM CONTRACT

## Developers

**Developer 1:** Kuldeep — Customer Intelligence
**Developer 2:** Girisha — Product + Business Intelligence

---

## Vertical Ownership

Each developer owns their vertical **end-to-end**:

```
Database
  +
Analytics
  +
ML/Logic
  +
API
  +
Frontend
  +
Tests
```

Neither developer may rewrite the other's vertical.

---

## Developer 1 — Customer Intelligence

### Data
- Customer ingestion
- Customer validation
- Customer schema

### Analytics
- RFM
- CLV
- Retention
- Cohort analysis
- Repeat purchases
- Purchase frequency
- Customer health

### ML
- Churn prediction
- Customer value
- Next purchase/category prediction

### API

```
/api/customers/*
```

### Frontend
- Customer Intelligence
- Customer Segmentation
- Customer 360
- Churn Intelligence
- Customer Retention

---

## Developer 2 — Product + Business Intelligence

### Data
- Product ingestion
- Order-item ingestion
- Product validation

### Analytics
- Revenue
- AOV
- Product analytics
- Category analytics
- Affinity
- Cross-sell
- Product gaps

### Intelligence
- Anomaly detection
- Opportunity detection
- Product health
- Business health
- Cross-sell scoring

### API

```
/api/products/*
/api/business/*
/api/opportunities/*
```

### Frontend
- Executive Overview
- Product Intelligence
- Product Detail
- Product Gaps
- Opportunity Radar
- Business Health

---

## Shared Responsibilities

Both developers collaborate on:
- Canonical schema
- API conventions
- Docker
- Database infrastructure
- Authentication / workspaces
- Environment configuration
- Shared React components
- Common TypeScript types
- Documentation

---

## Rules

1. Before changing a shared contract:
   - Inspect current implementation
   - Preserve compatibility
   - Document the change
   - Inform the other developer
2. Never rewrite shared infrastructure repeatedly
3. Never commit secrets
4. Never use paid APIs
5. Everything must run locally

---

## Git Branches

```
main
dev/customer-intelligence
dev/product-business-intelligence
```

## Commit Conventions

```
feat(customer): add canonical customer ingestion
feat(customer): implement RFM segmentation
feat(customer): add churn pipeline
feat(customer-ui): add customer 360
feat(product): add product analytics
feat(product): implement affinity engine
feat(opportunity): add cross-sell detection
feat(product-ui): add product intelligence
```

Use focused commits. Avoid huge commits containing unrelated changes.

---

## Tech Stack

Everything is free and open-source. No paid services.

| Layer        | Stack                                      |
|--------------|--------------------------------------------|
| Frontend     | React, Vite, TypeScript, Tailwind CSS, Recharts |
| Backend      | Python, FastAPI, Pydantic, SQLAlchemy, psycopg, Alembic |
| Data         | Pandas, NumPy                              |
| Database     | PostgreSQL                                 |
| ML           | Scikit-learn, XGBoost, Joblib              |
| Testing      | Pytest, Vitest                             |
| Infrastructure | Docker, Docker Compose, Git, GitHub      |

---

## Definition of Done

The MVP is complete when a user can:
1. Start InsightCart locally
2. Upload Olist data
3. Map columns
4. Validate the dataset
5. See data quality
6. See business health
7. Explore customers
8. Explore customer segments
9. View RFM and cohorts
10. View churn predictions
11. Explore products
12. View product affinity
13. Discover product gaps
14. View opportunities
15. See recommended actions

The user should **not** need SQL, Python, Statistics, or Machine Learning knowledge to understand the results.

---

## 🤖 Claude Code Prompts

Each developer runs Claude Code inside the repo and pastes the prompt for their current phase. Full step-by-step guides live in `README_KULDEEP.md` and `README_GIRISHA.md`.

### Developer 1 — Kuldeep (Customer Intelligence)

**Phase 1 — Customer + Order Ingestion**

> Read `README_KULDEEP.md` first. We are in Phase 1. Build the customer and order ingestion pipeline in an InsightCart FastAPI/PostgreSQL project. Implement:
> 1. Canonical customer + order models — `backend/app/models/customer.py`, `backend/app/models/order.py` (customer_id, customer_unique_id, customer_city, customer_state, customer_country, created_at; order: order_id, customer_id, order_date, order_status, order_value). Follow the canonical schema in `README.md`.
> 2. Pydantic schemas — `backend/app/schemas/customer.py`.
> 3. Ingestion service — `backend/app/services/ingestion/` to load the Olist customers + orders CSV files from `data/raw/` into PostgreSQL.
> 4. Customer validation service — `backend/app/services/validation/` to check data quality (missing values, duplicates, bad customers, invalid dates).
> 5. Upload API endpoints under `backend/app/api/upload.py` (POST upload, GET /api/health).
> 6. Alembic migration in `backend/app/db/migrations/`.
> 7. Tests in `backend/tests/test_customers.py`.
> Document what you build in `docs/data-model.md`. Run pytest to confirm tests pass. Do not touch Girisha's product/order-item vertical.

**Phase 2 — RFM, CLV, Retention, Cohorts, Customer Health**

> Read `README_KULDEEP.md` first. Phase 2. Implement customer analytics in `backend/app/services/customers/` and `backend/app/services/analytics/`:
> 1. RFM segmentation (Recency, Frequency, Monetary → segments like Champions, Loyal Customers, At Risk, etc.)
> 2. Customer Lifetime Value (historical CLV = revenue + purchase frequency + customer lifetime)
> 3. Retention and repeat-purchase-rate analytics
> 4. Cohort analysis (first-purchase month cohorts)
> 5. Purchase frequency + customer health score
> Expose via `backend/app/api/customers.py` (GET /api/customers, /segments, /rfm, /retention, /cohorts). Explainable, human-friendly segment names. Tests in `backend/tests/test_analytics.py`.

**Phase 3 — Churn ML, Customer Value, Next Purchase**

> Read `README_KULDEEP.md` first. Phase 3. Build customer ML:
> 1. Feature building in `backend/app/services/ml/` using recency_days, total_orders, total_revenue, purchase_frequency, average_order_value, days_between_orders, discount_usage, return_rate, category_count, customer_lifetime_days.
> 2. Churn models (Logistic Regression, Random Forest, XGBoost) — train in `ml/training/train_churn.py`, evaluate (precision, recall, F1, ROC-AUC, confusion matrix) in `ml/evaluation/metrics.py`, save best with Joblib to `ml/models/churn/`.
> 3. Next-purchase prediction — `ml/training/train_next_purchase.py`.
> 4. ML API — `backend/app/api/ml.py` (GET /api/churn/summary, /api/model/metrics).
> 5. Customer 360 endpoint `backend/app/api/customers.py` (GET /api/customers/{id}/360, /churn, /recommendation, /next-purchase).
> Tests in `backend/tests/test_ml.py`.

**Phase 5 — Customer React UI**

> Read `README_KULDEEP.md` first. Phase 5. Build the customer frontend:
> 1. Customer Intelligence, Segmentation, Customer 360, Churn Intelligence, Retention screens in `frontend/src/features/customers/` and `frontend/src/pages/` (Customers.tsx, Customer360.tsx).
> 2. Human-friendly copy — prefer "Loyal Customer" over "RFM 422", "High risk 82% churn" over "churn_probability 0.82".
> 3. Service layer — `frontend/src/services/customerApi.ts` (uses shared `frontend/src/services/api.ts`).
> 4. Use shared components from `frontend/src/components/` (charts, cards, tables, ui). Recharts for charts.

### Developer 2 — Girisha (Product + Business Intelligence)

**Phase 1 — Product + Order-Item Ingestion**

> Read `README_GIRISHA.md` first. Phase 1. Build product + order-item ingestion in an InsightCart FastAPI/PostgreSQL project. Implement:
> 1. Canonical product + order_item models — `backend/app/models/product.py`, `backend/app/models/order_item.py` (product: product_id, product_name, category, brand, price, cost, created_at; order_item: order_id, product_id, customer_id, quantity, unit_price, discount). Follow the canonical schema in `README.md`.
> 2. Pydantic schemas — `backend/app/schemas/product.py`.
> 3. Ingestion service — `backend/app/services/ingestion/` to load the Olist products + order_items CSV from `data/raw/` into PostgreSQL.
> 4. Product validation — `backend/app/services/validation/` (missing categories, duplicates, invalid prices).
> 5. Upload API — `backend/app/api/upload.py`, GET /api/health.
> 6. Alembic migration in `backend/app/db/migrations/`.
> 7. Tests in `backend/tests/test_products.py`.
> Document in `docs/data-model.md`. Run pytest to confirm tests pass. Do not touch Kuldeep's customer/order vertical.

**Phase 2 — Revenue, Product Analytics, Affinity, Cross-Sell, Product Gaps**

> Read `README_GIRISHA.md` first. Phase 2. Implement product + business analytics in `backend/app/services/products/` and `backend/app/services/analytics/`:
> 1. Revenue, AOV, product performance, category performance
> 2. Product affinity (co-occurrence, support, confidence, lift)
> 3. Cross-sell detection + product gaps (what should sell together but doesn't)
> Expose via `backend/app/api/products.py` and `backend/app/api/business.py` (GET /api/products, /categories, /affinity, /cross-sell, /gaps; /api/business/revenue, /aov, /trends, /health). Tests in `backend/tests/test_analytics.py`.

**Phase 3 — Anomaly Detection, Opportunity Engine, Product/Business Health**

> Read `README_GIRISHA.md` first. Phase 3. Build intelligence:
> 1. Anomaly detection (revenue anomalies, category decline) in `backend/app/services/insights/` / `backend/app/services/opportunities/`.
> 2. Product health + Business health scores.
> 3. Cross-sell scoring.
> 4. Opportunity engine producing explainable insights (type, severity, title, summary, evidence, business_impact, recommended_action, confidence) — `backend/app/api/opportunities.py` (GET /api/opportunities, /{id}).
> 5. ML API — `backend/app/api/ml.py` (GET /api/model/metrics).
> Tests in `backend/tests/test_ml.py`.

**Phase 5 — Product/Business React UI**

> Read `README_GIRISHA.md` first. Phase 5. Build the product + business frontend:
> 1. Executive Overview (Dashboard), Product Intelligence, Product Detail, Product Gaps, Opportunity Radar, Business Health screens — `frontend/src/features/products/`, `frontend/src/features/opportunities/`, `frontend/src/features/business/`, `frontend/src/pages/` (Dashboard.tsx, Products.tsx, ProductDetail.tsx, Opportunities.tsx, BusinessHealth.tsx).
> 2. Human-friendly copy — technical metrics behind "View technical details".
> 3. Service layer — `frontend/src/services/productApi.ts`, `businessApi.ts`, `opportunityApi.ts` (use shared `frontend/src/services/api.ts`).
> 4. Use shared components from `frontend/src/components/`. Recharts for charts.

---

## Read Before Prompting

- **Phase 0 must be complete first** (repo init, Docker, PostgreSQL, FastAPI, React, TypeScript, Tailwind, Alembic, canonical schema, shared components, `frontend/src/services/api.ts`).
- Read the full plan in `README.md` before starting.
- Read the shared contracts before changing them (canonical schema, API conventions, Docker, auth, env vars, shared UI).
- Never rewrite the other developer's vertical. Coordinate shared changes with the other developer.
- Each prompt assumes the repo already has the empty file structure initialized.

