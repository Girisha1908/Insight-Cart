# 🧑‍💻 Developer 1 — Kuldeep

## Customer Intelligence Guide

> Your vertical is **Customer Intelligence**. You own the customer domain end-to-end: Database → Analytics → ML → API → React UI → Tests.

---

## 📋 Table of Contents

- [Role Overview](#-role-overview)
- [Your Vertical](#-your-vertical)
- [Tech Stack](#-tech-stack)
- [How to Use This Guide](#-how-to-use-this-guide)
- [Phase 0 — Foundation (Shared)](#phase-0--foundation-shared)
- [Phase 1 — Customer + Order Ingestion](#phase-1--customer--order-ingestion)
- [Phase 2 — Customer Analytics (RFM, CLV, Cohorts)](#phase-2--customer-analytics-rfm-clv-cohorts)
- [Phase 3 — Churn ML + Customer Value](#phase-3--churn-ml--customer-value)
- [Phase 4 — Decision Intelligence](#phase-4--decision-intelligence)
- [Phase 5 — Customer React UI](#phase-5--customer-react-ui)
- [Phase 6 — API Integration](#phase-6--api-integration)
- [Phase 7 — Testing + Data Quality](#phase-7--testing--data-quality)
- [Phase 8/9 — Integration + Polish](#phase-89--integration--polish)
- [Your API Endpoints](#-your-api-endpoints)
- [Your Claude Code Prompts](#-your-claude-code-prompts)
- [Shared Contracts](#-shared-contracts)

---

## 🎯 Role Overview

You answer the **customer-side** questions of the business:

- Who are my customers?
- Which customers are valuable?
- Which are likely to leave?
- How is retention changing?
- What should we do about each customer?

You build **RFM, CLV, retention, cohorts, churn prediction, next-purchase prediction, and Customer 360** — with a human-friendly, explainable output.

---

## 🏗 Your Vertical

```
DATA (customer + order ingestion)
  ↓
DATABASE (canonical customer + order schema)
  ↓
ANALYTICS (RFM, CLV, retention, cohorts, repeat purchase, customer health)
  ↓
ML (churn, customer value, next purchase)
  ↓
API (/api/customers/*)
  ↓
REACT UI (Customer Intelligence, Segmentation, 360, Churn, Retention)
  ↓
TESTS
```

---

## 🛠 Tech Stack

| Layer | Tool |
|-------|------|
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, psycopg, Alembic |
| Data | Pandas, NumPy |
| Database | PostgreSQL |
| ML | Scikit-learn, XGBoost, Joblib |
| Frontend | React, Vite, TypeScript, Tailwind CSS, Recharts |
| Testing | Pytest, Vitest |
| Infra | Docker, Docker Compose, Git |

**Free / open-source only. No paid APIs. Everything runs locally.**

---

## 🚀 How to Use This Guide

1. Read the full project plan in `README.md` first.
2. Read `TEAM_CONTRACT.md` for the rules.
3. Work through the phases **in order** — each builds on the last.
4. For each phase, copy the **Claude Code prompt** into Claude Code (run inside the repo) and follow the step-by-step workflow.
5. Run tests at the end of each phase before moving on.

---

# Phase 0 — Foundation (Shared)

> ⚠️ **Do this first.** It is shared with Girisha. Do not start Phase 1 until this is complete.

### Step-by-step
1. Initialize the repository and confirm the folder structure from `README.md` exists.
2. Configure `docker-compose.yml` with a PostgreSQL service.
3. Start the DB: `docker compose up -d postgres`.
4. Configure `.env.example` → `.env` (DATABASE_URL, API_HOST, API_PORT, ENVIRONMENT).
5. Scaffold FastAPI: `backend/app/main.py`, `backend/app/core/config.py`, router wiring in `backend/app/api/router.py`.
6. Scaffold React + Vite + TypeScript + Tailwind in `frontend/`.
7. Configure Alembic in `backend/app/db/` and create the migrations directory.
8. Agree on the **canonical schema** (see `README.md`) and **API conventions** with Girisha.
9. Build shared React components (shell of `frontend/src/components/`) and the base API client `frontend/src/services/api.ts`.
10. Confirm the health endpoint works: `GET /api/health`.

### Claude Code prompt — Phase 0

> We are in Phase 0 of InsightCart. Scaffold the shared foundation of an e-commerce decision-intelligence project. The empty folder structure already exists in this repo. Do the following:
> 1. Configure `docker-compose.yml` with a PostgreSQL 16 service (db `insightcart`, user `insightcart`, password `insightcart`, port 5432).
> 2. Create `.env.example` with DATABASE_URL, API_HOST, API_PORT, ENVIRONMENT. Never hardcode or commit secrets.
> 3. Set up `backend/app/core/config.py` (pydantic-settings) reading env vars.
> 4. Create `backend/app/db/database.py` (SQLAlchemy engine + session) and `backend/app/db/base.py` (DeclarativeBase + imports of all models).
> 5. Configure Alembic under `backend/app/db/migrations/`.
> 6. Create the FastAPI entrypoint `backend/app/main.py` and a root API router at `backend/app/api/router.py` that includes all sub-routers (customers, products, business, opportunities, upload, ml). Add `GET /api/health`.
> 7. Scaffold the React + Vite + TypeScript + Tailwind frontend in `frontend/` with `main.tsx` and `App.tsx`, an API client in `frontend/src/services/api.ts` (base URL from env), and empty feature/page directories.
> 8. Create the shared UI component shells in `frontend/src/components/` (ui, charts, cards, tables, layout, shared).
> 9. Verify `uvicorn app.main:app --reload` starts and `/api/health` returns OK.

---

# Phase 1 — Customer + Order Ingestion

Duration: Week 1. You own customer + order ingestion and validation.

### What to build
1. **Canonical models** — `backend/app/models/customer.py`, `backend/app/models/order.py`
2. **Pydantic schemas** — `backend/app/schemas/customer.py`
3. **Ingestion service** — `backend/app/services/ingestion/` for customers + orders
4. **Validation service** — `backend/app/services/validation/`
5. **Upload API** — `backend/app/api/upload.py`
6. **Alembic migration** — `backend/app/db/migrations/`
7. **Tests** — `backend/tests/test_customers.py`

### Canonical schema (do not change without telling Girisha)

```text
Customers:
customer_id, customer_unique_id, customer_city, customer_state, customer_country, created_at

Orders:
order_id, customer_id, order_date, order_status, order_value
```

### Step-by-step
1. Put Olist `customers.csv` and `orders.csv` in `data/raw/`.
2. Build the SQLAlchemy models matching the canonical schema.
3. Write the ingestion service to load CSVs → pandas → validated rows → PostgreSQL.
4. Write validation checks: missing customer ids, duplicate orders, invalid dates, bad statuses.
5. Wire upload + health endpoints.
6. Create the Alembic migration and run `alembic upgrade head`.
7. Write and run tests in `backend/tests/test_customers.py`.
8. Document the customer/order tables in `docs/data-model.md`.

### Claude Code prompt — Phase 1

> Read `README_KULDEEP.md` and `TEAM_CONTRACT.md` first. This is InsightCart, Phase 1. Build the customer + order ingestion pipeline. Implement:
> 1. Canonical customer and order models in `backend/app/models/customer.py` and `backend/app/models/order.py` (customer_id, customer_unique_id, customer_city, customer_state, customer_country, created_at; order: order_id, customer_id, order_date, order_status, order_value). Follow the canonical schema in README.md.
> 2. Pydantic schemas in `backend/app/schemas/customer.py`.
> 3. An ingestion service in `backend/app/services/ingestion/` that reads Olist `customers.csv` + `orders.csv` from `data/raw/` with pandas and loads them into PostgreSQL.
> 4. A validation service in `backend/app/services/validation/` checking data quality (missing ids, duplicate orders, invalid dates/statuses).
> 5. Upload + health endpoints in `backend/app/api/upload.py` (POST upload, GET /api/health).
> 6. An Alembic migration in `backend/app/db/migrations/`.
> 7. Tests in `backend/tests/test_customers.py`.
> Document the tables in `docs/data-model.md`. Run pytest and confirm it passes. Do not touch Girisha's product/order-item vertical.

---

# Phase 2 — Customer Analytics (RFM, CLV, Cohorts)

Duration: Weeks 2–3.

### What to build
1. **RFM segmentation** — `backend/app/services/customers/` (Champions, Loyal Customers, Potential Loyalists, New, At Risk, Cannot Lose Them, Hibernating)
2. **CLV** — historical approach (revenue + purchase frequency + customer lifetime), transparently implemented
3. **Retention + repeat-purchase rate**
4. **Cohort analysis** — first-purchase-month cohorts
5. **Purchase frequency + customer health score**
6. **API** — `backend/app/api/customers.py`
7. **Tests** — `backend/tests/test_analytics.py`

### Step-by-step
1. Build the RFM scoring + segment mapping. Output human segment names, not raw scores.
2. Build CLV as an explainable formula.
3. Build retention tables and repeat-purchase-rate metric.
4. Build cohort analysis (rows = first-purchase month, columns = subsequent months).
5. Build a customer health score (0–100).
6. Expose endpoints: `GET /api/customers`, `/segments`, `/rfm`, `/retention`, `/cohorts`.
7. Write tests for each analytics function.
8. Confirm outputs are human-friendly ("Loyal Customer", not "RFM 422").

### Claude Code prompt — Phase 2

> Read `README_KULDEEP.md` and `TEAM_CONTRACT.md` first. InsightCart Phase 2 — implement customer analytics. Build:
> 1. RFM segmentation (Recency/Frequency/Monetary → explainable segment names like Champions, Loyal Customers, At Risk, Hibernating) in `backend/app/services/customers/` and `backend/app/services/analytics/`.
> 2. Historical CLV (revenue + purchase frequency + customer lifetime) implemented as a transparent formula.
> 3. Retention analysis + repeat-purchase-rate metric.
> 4. First-purchase-month cohort analysis.
> 5. Purchase frequency + a 0–100 customer health score.
> Expose via `backend/app/api/customers.py`: GET /api/customers, /segments, /rfm, /retention, /cohorts. Use human-friendly segment names, not raw scores. Write tests in `backend/tests/test_analytics.py` and confirm they pass.

---

# Phase 3 — Churn ML + Customer Value

Duration: Week 4.

### What to build
1. **Features** — `backend/app/services/ml/`
2. **Churn models** (Logistic Regression, Random Forest, XGBoost) — `ml/training/train_churn.py`
3. **Evaluation** (precision, recall, F1, ROC-AUC, confusion matrix) — `ml/evaluation/metrics.py`
4. **Save best model** with Joblib — `ml/models/churn/`
5. **Next-purchase prediction** — `ml/training/train_next_purchase.py`
6. **ML API** — `backend/app/api/ml.py`
7. **Customer 360 + churn endpoints** — `backend/app/api/customers.py`
8. **Tests** — `backend/tests/test_ml.py`

### Features

```text
recency_days, total_orders, total_revenue, purchase_frequency,
average_order_value, days_between_orders, discount_usage,
return_rate, category_count, customer_lifetime_days
```

### Step-by-step
1. Build the feature-engineering service.
2. Train the three churn models; compare metrics.
3. Save the best with Joblib to `ml/models/churn/`.
4. Train next-purchase prediction.
5. Expose: `GET /api/churn/summary`, `/api/model/metrics`.
6. Build Customer 360: `GET /api/customers/{id}/360`, `/churn`, `/recommendation`, `/next-purchase`.
7. Report confidence and explanations, not just a number (e.g. "High risk — 82% likelihood of churn").
8. ⚠️ **No causal claims.** Never say "a discount will reduce churn by X%" without causal data. Say "Consider a targeted retention offer."

### Claude Code prompt — Phase 3

> Read `README_KULDEEP.md` and `TEAM_CONTRACT.md` first. InsightCart Phase 3 — customer ML. Build:
> 1. A feature service in `backend/app/services/ml/` producing: recency_days, total_orders, total_revenue, purchase_frequency, average_order_value, days_between_orders, discount_usage, return_rate, category_count, customer_lifetime_days.
> 2. Churn models (Logistic Regression, Random Forest, XGBoost) trained in `ml/training/train_churn.py`.
> 3. Evaluation (precision, recall, F1, ROC-AUC, confusion matrix) in `ml/evaluation/metrics.py`; save the best model with Joblib to `ml/models/churn/`.
> 4. Next-purchase prediction in `ml/training/train_next_purchase.py`.
> 5. ML API in `backend/app/api/ml.py` (GET /api/churn/summary, /api/model/metrics).
> 6. Customer 360 + churn + recommendation endpoints in `backend/app/api/customers.py` (GET /api/customers/{id}/360, /churn, /recommendation, /next-purchase).
> Present churn as human-friendly ("High risk — 82% likelihood of churn") with a recommended action. Never make causal claims about intervention impact. Write tests in `backend/tests/test_ml.py` and confirm they pass.

---

# Phase 4 — Decision Intelligence

Duration: Week 5 (combined with UI).

Turn analytics + ML into **structured, explainable insights** for customers:

```text
Problem → Evidence → Business Impact → Recommended Action → Confidence
```

### Claude Code prompt — Phase 4

> Read `README_KULDEEP.md` and `TEAM_CONTRACT.md` first. InsightCart Phase 4 — decision intelligence for customers. Convert customer analytics (RFM, CLV, retention, cohorts, churn) into structured, explainable insights. Each insight must answer: what happened, why it matters, what evidence supports it, what the business should do, and how confident we are. Return insights in a consistent shape (id, type, severity, title, summary, evidence, business_impact, recommended_action, confidence). Do not claim causal intervention impacts without treatment data — use "consider" language. Keep technical metrics available behind a "View technical details" view. Wire the output into the customer API responses.

---

# Phase 5 — Customer React UI

Duration: Weeks 6.

### What to build
1. **Pages** — `frontend/src/pages/Customers.tsx`, `Customer360.tsx`
2. **Features** — `frontend/src/features/customers/`
3. **Service** — `frontend/src/services/customerApi.ts`
4. **Reuse shared components** from `frontend/src/components/`

### Screens
- Customer Intelligence
- Customer Segmentation
- Customer 360
- Churn Intelligence
- Customer Retention

### UX rules
- Human-friendly everywhere. "Loyal Customer" not "RFM 422".
- Charts with Recharts. Loading / error / empty states required.
- Technical metrics behind "View technical details".

### Claude Code prompt — Phase 5

> Read `README_KULDEEP.md` and `TEAM_CONTRACT.md` first. InsightCart Phase 5 — build the customer frontend with React + TypeScript + Tailwind + Recharts:
> 1. Customer Intelligence, Segmentation, Customer 360, Churn Intelligence, and Retention screens in `frontend/src/features/customers/` and `frontend/src/pages/` (Customers.tsx, Customer360.tsx).
> 2. A service layer in `frontend/src/services/customerApi.ts` that uses the shared base client `frontend/src/services/api.ts`.
> 3. Human-friendly copy: "Loyal Customer" instead of "RFM 422", "High risk — 82% churn" instead of "churn_probability 0.82". Keep technical metrics behind a "View technical details" toggle.
> 4. Use shared components (charts, cards, tables, ui) and Recharts for visualizations. Include loading, error, and empty states.

---

# Phase 6 — API Integration

Duration: Week 7.

Connect the customer UI to the customer API.

### Claude Code prompt — Phase 6

> Read `README_KULDEEP.md` first. InsightCart Phase 6 — integrate the customer React screens with the FastAPI customer endpoints. Wire `frontend/src/services/customerApi.ts` to consume `GET /api/customers`, /segments, /rfm, /retention, /cohorts, and `/api/customers/{id}/360`, /churn, /recommendation, /next-purchase. Add proper loading, error, and empty states everywhere. Confirm the dashboard data flow works end-to-end from the backend.

---

# Phase 7 — Testing + Data Quality

Duration: Week 8.

### What to test
- Customer + order ingestion and validation
- RFM, CLV, retention, cohorts
- Churn features + churn model
- Recommendation logic
- API endpoints

### Claude Code prompt — Phase 7

> Read `README_KULDEEP.md` first. InsightCart Phase 7 — harden the customer vertical with tests and data quality:
> 1. Cover ingestion, validation, RFM, CLV, retention, cohorts, churn features, churn model, recommendation logic, and the customer API endpoints with pytest in `backend/tests/`.
> 2. Add a `scripts/import_olist.py` and `scripts/seed_demo.py` path to load + seed demo data deterministically.
> 3. Ensure empty inputs and bad data are handled gracefully (no crashes, clear messages).
> 4. Confirm the full test suite passes. Frontend: add Vitest tests for the main customer pages if not present.

---

# Phase 8/9 — Integration + Polish

Duration: Week 9.

Final end-to-end verification of the customer vertical and integration with Girisha's product/business vertical.

### Claude Code prompt — Phase 8/9

> Read `README_KULDEEP.md` and `TEAM_CONTRACT.md` first. InsightCart final phase — integrate and polish the customer vertical:
> 1. Run the full end-to-end flow: start the stack, load demo data, open the customer pages, verify Customer 360, segments, cohorts, and churn render real data.
> 2. Polish UI states, responsive layout, and empty data handling.
> 3. Ensure the customer vertical works cleanly alongside Girisha's product/business vertical without breaking shared contracts.
> 4. Update docs (`docs/data-model.md`, `docs/api.md`) to match the final implementation. Confirm the whole app runs via `docker compose up --build` and a full test pass.

---

## 🔌 Your API Endpoints

```http
GET  /api/customers
GET  /api/customers/{customer_id}
GET  /api/customers/{customer_id}/360
GET  /api/customers/{customer_id}/churn
GET  /api/customers/{customer_id}/recommendation
GET  /api/customers/{customer_id}/next-purchase
GET  /api/customers/segments
GET  /api/customers/rfm
GET  /api/customers/retention
GET  /api/customers/cohorts

GET  /api/churn/summary
GET  /api/model/metrics
```

---

## 🧩 Shared Contracts

Shared with Girisha — inspect, preserve compatibility, document, and inform before changing:
- Canonical schema
- API conventions
- Docker
- Database infrastructure
- Authentication/workspaces
- Environment configuration
- Shared React components
- Common TypeScript types

---

## ✅ Definition of Done (Customer Side)

The customer vertical is done when a user can explore customers, view segments, see RFM and cohorts, view churn predictions, and see a complete Customer 360 — all in human-friendly language, without needing SQL, Python, statistics, or ML knowledge.
