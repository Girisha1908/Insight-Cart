# 🧑‍💻 Developer 2 — Girisha

## Product + Business Intelligence Guide

> Your vertical is **Product + Business Intelligence**. You own the product & business domain end-to-end: Database → Analytics → Intelligence → Opportunity Engine → API → React UI → Tests.

---

## 📋 Table of Contents

- [Role Overview](#-role-overview)
- [Your Vertical](#-your-vertical)
- [Tech Stack](#-tech-stack)
- [How to Use This Guide](#-how-to-use-this-guide)
- [Phase 0 — Foundation (Shared)](#phase-0--foundation-shared)
- [Phase 1 — Product + Order-Item Ingestion](#phase-1--product--order-item-ingestion)
- [Phase 2 — Revenue, Product Analytics, Affinity, Cross-Sell, Gaps](#phase-2--revenue-product-analytics-affinity-cross-sell-gaps)
- [Phase 3 — Anomaly Detection + Opportunity Engine + Health](#phase-3--anomaly-detection--opportunity-engine--health)
- [Phase 4 — Decision Intelligence](#phase-4--decision-intelligence)
- [Phase 5 — Product/Business React UI](#phase-5--productbusiness-react-ui)
- [Phase 6 — API Integration](#phase-6--api-integration)
- [Phase 7 — Testing + UI Polish](#phase-7--testing--ui-polish)
- [Phase 8/9 — Integration + Polish](#phase-89--integration--polish)
- [Your API Endpoints](#-your-api-endpoints)
- [Your Claude Code Prompts](#-your-claude-code-prompts)
- [Shared Contracts](#-shared-contracts)

---

## 🎯 Role Overview

You answer the **product & business-side** questions of the business:

- What products are customers buying?
- What products are they not buying?
- What sells together?
- Where are the cross-sell/gap opportunities?
- Why is revenue changing?
- How healthy is the business?

You build **revenue analytics, product performance, affinity, cross-sell, product gaps, anomaly detection, the Opportunity Radar, and Business Health** — with human-friendly, explainable output.

---

## 🏗 Your Vertical

```
DATA (product + order-item ingestion)
  ↓
DATABASE (canonical product + order_item schema)
  ↓
ANALYTICS (revenue, AOV, product/category performance, affinity, cross-sell, gaps)
  ↓
INTELLIGENCE (anomaly detection, product health, business health, cross-sell scoring)
  ↓
OPPORTUNITY ENGINE (risk + opportunity + anomaly + trend)
  ↓
API (/api/products/*, /api/business/*, /api/opportunities/*)
  ↓
REACT UI (Executive Overview, Product Intelligence, Product Gaps, Opportunity Radar, Business Health)
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

> ⚠️ **Do this first.** It is shared with Kuldeep. Do not start Phase 1 until this is complete.

### Step-by-step
1. Initialize the repository and confirm the folder structure from `README.md` exists.
2. Configure `docker-compose.yml` with a PostgreSQL service.
3. Start the DB: `docker compose up -d postgres`.
4. Configure `.env.example` → `.env` (DATABASE_URL, API_HOST, API_PORT, ENVIRONMENT).
5. Scaffold FastAPI: `backend/app/main.py`, `backend/app/core/config.py`, router wiring in `backend/app/api/router.py`.
6. Scaffold React + Vite + TypeScript + Tailwind in `frontend/`.
7. Configure Alembic in `backend/app/db/` and create the migrations directory.
8. Agree on the **canonical schema** (see `README.md`) and **API conventions** with Kuldeep.
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

# Phase 1 — Product + Order-Item Ingestion

Duration: Week 1. You own product + order-item ingestion and validation.

### What to build
1. **Canonical models** — `backend/app/models/product.py`, `backend/app/models/order_item.py`
2. **Pydantic schemas** — `backend/app/schemas/product.py`
3. **Ingestion service** — `backend/app/services/ingestion/` for products + order_items
4. **Validation service** — `backend/app/services/validation/`
5. **Upload API** — `backend/app/api/upload.py`
6. **Alembic migration** — `backend/app/db/migrations/`
7. **Tests** — `backend/tests/test_products.py`

### Canonical schema (do not change without telling Kuldeep)

```text
Products:
product_id, product_name, category, brand, price, cost, created_at

Order Items:
order_id, product_id, customer_id, quantity, unit_price, discount
```

### Step-by-step
1. Put Olist `products.csv` and `order_items.csv` in `data/raw/`.
2. Build the SQLAlchemy models matching the canonical schema.
3. Write the ingestion service to load CSVs → pandas → validated rows → PostgreSQL.
4. Write validation checks: missing categories, duplicate products, invalid prices, missing ids.
5. Wire upload + health endpoints.
6. Create the Alembic migration and run `alembic upgrade head`.
7. Write and run tests in `backend/tests/test_products.py`.
8. Document the product/order_item tables in `docs/data-model.md`.

### Claude Code prompt — Phase 1

> Read `README_GIRISHA.md` and `TEAM_CONTRACT.md` first. This is InsightCart, Phase 1. Build the product + order-item ingestion pipeline. Implement:
> 1. Canonical product and order_item models in `backend/app/models/product.py` and `backend/app/models/order_item.py` (product: product_id, product_name, category, brand, price, cost, created_at; order_item: order_id, product_id, customer_id, quantity, unit_price, discount). Follow the canonical schema in README.md.
> 2. Pydantic schemas in `backend/app/schemas/product.py`.
> 3. An ingestion service in `backend/app/services/ingestion/` that reads Olist `products.csv` + `order_items.csv` from `data/raw/` with pandas and loads them into PostgreSQL.
> 4. A validation service in `backend/app/services/validation/` checking data quality (missing categories, duplicate products, invalid prices, missing ids).
> 5. Upload + health endpoints in `backend/app/api/upload.py` (POST upload, GET /api/health).
> 6. An Alembic migration in `backend/app/db/migrations/`.
> 7. Tests in `backend/tests/test_products.py`.
> Document the tables in `docs/data-model.md`. Run pytest and confirm it passes. Do not touch Kuldeep's customer/order vertical.

---

# Phase 2 — Revenue, Product Analytics, Affinity, Cross-Sell, Gaps

Duration: Weeks 2–3.

### What to build
1. **Revenue + AOV analytics** — `backend/app/services/analytics/`
2. **Product & category performance** — `backend/app/services/products/`
3. **Product affinity** (co-occurrence, support, confidence, lift) — `backend/app/services/products/`
4. **Cross-sell detection** — `backend/app/services/products/`
5. **Product gaps** (what should sell together but doesn't) — `backend/app/services/products/`
6. **API** — `backend/app/api/products.py`, `backend/app/api/business.py`
7. **Tests** — `backend/tests/test_analytics.py`

### Step-by-step
1. Build revenue, AOV, trend, and product/category performance analytics.
2. Build affinity using co-occurrence, support, confidence, and lift.
3. Build cross-sell detection and product-gap scoring.
4. Expose endpoints: `GET /api/products`, `/categories`, `/affinity`, `/cross-sell`, `/gaps`; `GET /api/business/revenue`, `/aov`, `/trends`, `/health`.
5. Write tests for each analytics function.
6. Keep the primary output human-friendly; put raw metrics (lift, support) behind "View technical details".

### Claude Code prompt — Phase 2

> Read `README_GIRISHA.md` and `TEAM_CONTRACT.md` first. InsightCart Phase 2 — implement product + business analytics. Build:
> 1. Revenue, AOV, trend, and product/category performance analytics in `backend/app/services/products/` and `backend/app/services/analytics/`.
> 2. Product affinity using co-occurrence, support, confidence, and lift.
> 3. Cross-sell detection and product-gap scoring (products that should be selling together but aren't).
> Expose via `backend/app/api/products.py` (GET /api/products, /categories, /affinity, /cross-sell, /gaps) and `backend/app/api/business.py` (GET /api/business/revenue, /aov, /trends, /health). Keep raw technical metrics available only behind a "View technical details" view. Write tests in `backend/tests/test_analytics.py` and confirm they pass.

---

# Phase 3 — Anomaly Detection + Opportunity Engine + Health

Duration: Week 4.

### What to build
1. **Anomaly detection** (revenue anomalies, category decline, review deterioration, return-rate increases) — `backend/app/services/insights/`
2. **Product health + Business health scores**
3. **Cross-sell scoring** — `backend/app/services/opportunities/`
4. **Opportunity Engine** — produces explainable insights (type, severity, title, summary, evidence, business_impact, recommended_action, confidence)
5. **API** — `backend/app/api/opportunities.py`, `backend/app/api/ml.py`
6. **Tests** — `backend/tests/test_ml.py`

### Opportunity categories
- **Risks:** churn rising, retention falling, high-value customers inactive, product sales falling, category decline, review deterioration, return-rate increase, revenue anomalies
- **Opportunities:** cross-sell, upsell, product gaps, customer reactivation, high-value retention, category expansion, product combinations

### Step-by-step
1. Build anomaly detection over revenue/product/category trends.
2. Build product health and business health (dimensions: revenue, customer health, retention, product health, growth, opportunities, risks).
3. Build the Opportunity Engine that returns structured, explainable insights.
4. Expose: `GET /api/opportunities`, `/api/opportunities/{id}`; `GET /api/model/metrics`.
5. ⚠️ **No causal claims.** Use "consider" language, never "this will increase revenue by X%".

### Claude Code prompt — Phase 3

> Read `README_GIRISHA.md` and `TEAM_CONTRACT.md` first. InsightCart Phase 3 — build product/business intelligence. Build:
> 1. Anomaly detection (revenue anomalies, category decline) in `backend/app/services/insights/`.
> 2. Product health + a Business health score (dimensions: revenue, customer health, retention, product health, growth, opportunities, risks).
> 3. Cross-sell scoring in `backend/app/services/opportunities/`.
> 4. An Opportunity Engine returning structured, explainable insights: {id, type, severity, title, summary, evidence, business_impact, recommended_action, confidence}. Types include risks (churn rising, retention falling, product sales falling, category decline, revenue anomalies) and opportunities (cross-sell, upsell, product gaps, category expansion).
> Expose via `backend/app/api/opportunities.py` (GET /api/opportunities, /{id}) and `backend/app/api/ml.py` (GET /api/model/metrics). Keep the output human-friendly with full explanations. Never make causal intervention claims — use "consider" language. Write tests in `backend/tests/test_ml.py` and confirm they pass.

---

# Phase 4 — Decision Intelligence

Duration: Week 5 (combined with UI).

Turn analytics + intelligence into **structured, explainable insights** for products and business:

```text
Problem → Evidence → Business Impact → Recommended Action → Confidence
```

### Claude Code prompt — Phase 4

> Read `README_GIRISHA.md` and `TEAM_CONTRACT.md` first. InsightCart Phase 4 — decision intelligence for product & business. Convert product analytics and opportunity detection into structured, explainable insights. Each insight must answer: what happened, why it matters, what evidence supports it, what the business should do, and how confident we are. Return insights in a consistent shape (id, type, severity, title, summary, evidence, business_impact, recommended_action, confidence). Do not claim causal intervention impacts without treatment data — use "consider" language. Keep technical metrics available behind a "View technical details" view. Wire the output into the product/business/opportunity API responses.

---

# Phase 5 — Product/Business React UI

Duration: Week 6.

### What to build
1. **Pages** — `frontend/src/pages/Dashboard.tsx`, `Products.tsx`, `ProductDetail.tsx`, `Opportunities.tsx`, `BusinessHealth.tsx`
2. **Features** — `frontend/src/features/products/`, `frontend/src/features/opportunities/`, `frontend/src/features/business/`
3. **Services** — `frontend/src/services/productApi.ts`, `businessApi.ts`, `opportunityApi.ts`
4. **Reuse shared components** from `frontend/src/components/`

### Screens
- Executive Overview (Dashboard / Business Health)
- Product Intelligence
- Product Detail
- Product Gaps
- Opportunity Radar
- Business Health

### UX rules
- Human-friendly everywhere. "Customers who buy A are more likely to buy B" not "lift = 3.82".
- The **Opportunity Radar** is highly visible on the dashboard.
- Charts with Recharts. Loading / error / empty states required.
- Technical metrics behind "View technical details".

### Claude Code prompt — Phase 5

> Read `README_GIRISHA.md` and `TEAM_CONTRACT.md` first. InsightCart Phase 5 — build the product + business frontend with React + TypeScript + Tailwind + Recharts:
> 1. Executive Overview (Dashboard), Product Intelligence, Product Detail, Product Gaps, Opportunity Radar, and Business Health screens in `frontend/src/features/products/`, `frontend/src/features/opportunities/`, `frontend/src/features/business/`, and `frontend/src/pages/` (Dashboard.tsx, Products.tsx, ProductDetail.tsx, Opportunities.tsx, BusinessHealth.tsx).
> 2. Service layers in `frontend/src/services/productApi.ts`, `businessApi.ts`, and `opportunityApi.ts` that use the shared base client `frontend/src/services/api.ts`.
> 3. Human-friendly copy: "Customers who buy Product A are much more likely to buy Product B" instead of "lift = 3.82". Keep technical metrics behind a "View technical details" toggle.
> 4. Make the Opportunity Radar highly visible. Use shared components (charts, cards, tables, ui) and Recharts. Include loading, error, and empty states.

---

# Phase 6 — API Integration

Duration: Week 7.

Connect the product/business UI to the product/business API.

### Claude Code prompt — Phase 6

> Read `README_GIRISHA.md` first. InsightCart Phase 6 — integrate the product/business React screens with the FastAPI product, business, and opportunity endpoints. Wire `frontend/src/services/productApi.ts`, `businessApi.ts`, and `opportunityApi.ts` to consume `GET /api/products`, /categories, /affinity, /cross-sell, /gaps, `/api/business/revenue`, /aov, /trends, /health, and `/api/opportunities`. Add proper loading, error, and empty states everywhere. Confirm the dashboard (Executive Overview + Opportunity Radar + Business Health) data flow works end-to-end from the backend.

---

# Phase 7 — Testing + UI Polish

Duration: Week 8.

### What to test
- Product + order-item ingestion and validation
- Product analytics, affinity, cross-sell, product gaps
- Opportunity engine
- API endpoints

### Claude Code prompt — Phase 7

> Read `README_GIRISHA.md` first. InsightCart Phase 7 — harden the product/business vertical with tests and UI polish:
> 1. Cover ingestion, validation, product analytics, affinity, cross-sell, product gaps, the opportunity engine, and the product/business/opportunity API endpoints with pytest in `backend/tests/`.
> 2. Add a `scripts/seed_demo.py` path to load + seed demo data deterministically.
> 3. Polish the product/business UI: responsive layout, empty states, and loading states.
> 4. Confirm the full test suite passes. Frontend: add Vitest tests for the main product/business pages if not present.

---

# Phase 8/9 — Integration + Polish

Duration: Week 9.

Final end-to-end verification of the product/business vertical and integration with Kuldeep's customer vertical.

### Claude Code prompt — Phase 8/9

> Read `README_GIRISHA.md` and `TEAM_CONTRACT.md` first. InsightCart final phase — integrate and polish the product/business vertical:
> 1. Run the full end-to-end flow: start the stack, load demo data, open the dashboard, verify Executive Overview, Product Intelligence, Product Gaps, Opportunity Radar, and Business Health render real data.
> 2. Polish UI states, responsive layout, and empty data handling.
> 3. Ensure the product/business vertical works cleanly alongside Kuldeep's customer vertical without breaking shared contracts.
> 4. Update docs (`docs/data-model.md`, `docs/api.md`) to match the final implementation. Confirm the whole app runs via `docker compose up --build` and a full test pass.

---

## 🔌 Your API Endpoints

```http
GET  /api/products
GET  /api/products/{product_id}
GET  /api/products/{product_id}/health
GET  /api/products/categories
GET  /api/products/affinity
GET  /api/products/cross-sell
GET  /api/products/gaps

GET  /api/business/revenue
GET  /api/business/aov
GET  /api/business/trends
GET  /api/business/health

GET  /api/opportunities
GET  /api/opportunities/{opportunity_id}

GET  /api/model/metrics
```

---

## 🧩 Shared Contracts

Shared with Kuldeep — inspect, preserve compatibility, document, and inform before changing:
- Canonical schema
- API conventions
- Docker
- Database infrastructure
- Authentication/workspaces
- Environment configuration
- Shared React components
- Common TypeScript types

---

## ✅ Definition of Done (Product/Business Side)

The product/business vertical is done when a user can view the Executive Overview, explore products, see product affinity, discover product gaps, view the Opportunity Radar, and see Business Health — all in human-friendly language with clear recommended actions, without needing SQL, Python, statistics, or ML knowledge.
