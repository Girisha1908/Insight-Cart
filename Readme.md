# 🛒 InsightCart

### E-Commerce Decision Intelligence Platform

> **Turn e-commerce data into decisions.**

InsightCart is a free, open-source, local-first **E-Commerce Decision Intelligence Platform** that transforms raw e-commerce data into human-friendly business insights, customer intelligence, product opportunities, risk signals, and recommended actions.

Unlike traditional analytics dashboards that simply display charts and metrics, InsightCart attempts to answer the questions that actually matter to a business:

* Who are my customers?
* Which customers are valuable?
* Which customers are likely to leave?
* What products are customers buying?
* What products are they not buying?
* Which products are frequently bought together?
* Where are the biggest cross-sell opportunities?
* Why is revenue increasing or decreasing?
* Which products or categories are underperforming?
* Which customers should we focus on?
* What should the business do next?

The core philosophy is:

```text
                    RAW E-COMMERCE DATA
                             │
                             ▼
                    DATA UNDERSTANDING
                             │
                             ▼
                         ANALYTICS
                             │
                             ▼
                       ML / AI LOGIC
                             │
                             ▼
                    PATTERN DETECTION
                             │
                             ▼
                       INSIGHT ENGINE
                             │
                             ▼
                    RECOMMENDED ACTION
```

---

# 📌 Table of Contents

* [What is InsightCart?](#-what-is-insightcart)
* [Problem](#-problem)
* [Solution](#-solution)
* [What Makes InsightCart Different?](#-what-makes-insightcart-different)
* [Core Product Features](#-core-product-features)
* [Olist Dataset](#-olist-dataset)
* [Generalized SaaS Architecture](#-generalized-saas-architecture)
* [Data Flow](#-data-flow)
* [Technology Stack](#-technology-stack)
* [System Architecture](#-system-architecture)
* [Canonical Data Model](#-canonical-data-model)
* [Project Folder Structure](#-project-folder-structure)
* [Frontend Structure](#-frontend-structure)
* [Backend Structure](#-backend-structure)
* [Machine Learning](#-machine-learning)
* [Insight Engine](#-insight-engine)
* [Customer Intelligence](#-customer-intelligence)
* [Product Intelligence](#-product-intelligence)
* [Opportunity Radar](#-opportunity-radar)
* [Data Upload Experience](#-data-upload-experience)
* [Human-Friendly UX](#-human-friendly-ux)
* [API Structure](#-api-structure)
* [Development Strategy](#-development-strategy)
* [Two-Person Team Division](#-two-person-team-division)
* [Developer 1](#-developer-1--customer-intelligence)
* [Developer 2](#-developer-2--product--business-intelligence)
* [Parallel Development](#-parallel-development)
* [Development Roadmap](#-development-roadmap)
* [Git Strategy](#-git-strategy)
* [Testing](#-testing)
* [Free / Open-Source Requirement](#-free--open-source-requirement)
* [Running Locally](#-running-locally)
* [Environment Variables](#-environment-variables)
* [Future Features](#-future-features)
* [Project Differentiation](#-project-differentiation)
* [Resume Description](#-resume-description)
* [Definition of Done](#-definition-of-done)
* [License](#-license)

---

# 🧠 What is InsightCart?

InsightCart is a general-purpose e-commerce intelligence platform.

A company should be able to upload its e-commerce dataset and receive a complete business intelligence workspace without needing to know:

* SQL
* Python
* statistics
* machine learning
* data visualization
* data engineering

The user experience should be:

```text
Upload Data
     ↓
InsightCart Understands the Data
     ↓
Map Columns
     ↓
Validate Data
     ↓
Process Data
     ↓
Generate Analytics
     ↓
Run ML Models
     ↓
Detect Risks & Opportunities
     ↓
Explain Findings
     ↓
Recommend Actions
```

---

# ❗ Problem

Most analytics systems stop at:

> "Revenue decreased by 14%."

or:

> "Customer churn probability is 82%."

That still leaves the business user asking:

> Why?

and:

> What should I do?

InsightCart is designed around a different philosophy.

Traditional BI:

```text
Data
 ↓
Metric
 ↓
Chart
 ↓
Human interpretation
```

InsightCart:

```text
Data
 ↓
Metric
 ↓
Pattern
 ↓
Explanation
 ↓
Business impact
 ↓
Recommended action
```

---

# 💡 Solution

InsightCart combines:

### Data Engineering

* CSV ingestion
* data validation
* schema detection
* column mapping
* PostgreSQL storage

### Business Analytics

* revenue
* AOV
* retention
* cohorts
* RFM
* CLV
* purchase frequency
* product performance
* product affinity

### Machine Learning

* churn prediction
* customer segmentation
* next-purchase prediction
* anomaly detection
* opportunity scoring

### Decision Intelligence

* risk detection
* cross-sell opportunities
* product gaps
* customer retention opportunities
* business health
* recommended actions

---

# 🚀 What Makes InsightCart Different?

The major differentiator is the **Decision Intelligence Layer**.

InsightCart does not want to become:

> "Another dashboard with 25 charts."

Instead:

```text
                    INSIGHTCART

                      DATA
                       │
              ┌────────┴────────┐
              ▼                 ▼
          CUSTOMERS          PRODUCTS
              │                 │
              ▼                 ▼
         BEHAVIOR           BEHAVIOR
              │                 │
              └────────┬────────┘
                       ▼
                 OPPORTUNITIES
                       │
                       ▼
                  EXPLANATIONS
                       │
                       ▼
                RECOMMENDED ACTION
```

For example:

### Traditional dashboard

```text
Repeat Purchase Rate

34.7%
```

### InsightCart

```text
⚠ Repeat purchases are declining

Repeat purchase rate:
34.7% ↓ 6.2%

What changed?
Returning customers in the Electronics
category declined significantly.

Recommended action:
Target recently inactive Electronics customers
with personalized product recommendations.
```

---

# ⭐ Core Product Features

## 1. Executive Business Overview

The home dashboard should immediately answer:

```text
How is my business doing?
What changed?
What is going wrong?
Where is the opportunity?
What should I do?
```

Metrics include:

* Revenue
* Orders
* Customers
* AOV
* Repeat purchase rate
* Retention
* Customer health
* Product health
* Opportunity count

---

# 2. Customer Intelligence

Understand customers at an individual and segment level.

### Analytics

* RFM segmentation
* Customer Lifetime Value
* retention
* cohort analysis
* repeat purchase rate
* purchase frequency
* average order value
* customer revenue
* customer lifetime
* customer health

---

# 3. Customer 360

Every customer should have a complete profile.

Example:

```text
CUSTOMER 360

Customer:
CUST-10293

Segment:
Loyal Customer

Customer Health:
82 / 100

Lifetime Value:
₹18,420

Orders:
12

Average Order:
₹1,535

Last Purchase:
43 days ago

Churn Risk:
HIGH

Top Categories:
Electronics
Accessories
```

---

# 4. Churn Intelligence

Predict customers who are likely to become inactive.

Potential features:

```text
Recency
Frequency
Monetary Value
Purchase Frequency
Average Order Value
Days Between Orders
Discount Usage
Return Rate
Category Diversity
Customer Lifetime
```

Models:

* Logistic Regression
* Random Forest
* XGBoost

Output:

```text
HIGH CHURN RISK

82% likelihood of becoming inactive

Why?

• Purchase interval is unusually high
• Customer has historically purchased frequently
• Customer has high lifetime value

Recommended action:

Prioritize this customer for retention outreach.
```

---

# 5. Customer Segmentation

Use RFM and behavioral characteristics to create segments.

Examples:

```text
Champions
Loyal Customers
Potential Loyalists
New Customers
At Risk
Cannot Lose Them
Hibernating
```

Segments should be explainable.

---

# 6. Cohort Analysis

Analyze customers based on their first purchase period.

Example:

```text
             Month 1   Month 2   Month 3   Month 4
Jan Cohort     100%      48%       32%       24%
Feb Cohort     100%      51%       35%       27%
Mar Cohort     100%      43%       29%       21%
```

The goal is to identify:

* improving cohorts
* declining cohorts
* retention problems
* acquisition quality

---

# 7. Product Intelligence

For every product:

* revenue
* units sold
* orders
* customers
* average price
* repeat purchase
* return rate where available
* reviews where available
* growth
* category performance
* affinity
* cross-sell opportunities

---

# 8. Product Gaps

One of InsightCart's key differentiators.

Instead of only asking:

> What are our best-selling products?

InsightCart asks:

> **What products should potentially be selling together, but aren't?**

Example:

```text
PRODUCT GAP

Running Shoes
      ↓
Sports Accessories

Customers buying Running Shoes:
8,421

Customers buying both:
1,102

Potential opportunity:
7,319 customers
```

The system can surface:

```text
Potential Cross-Sell Opportunity

Confidence: HIGH

Recommended action:
Test Sports Accessories recommendations
after Running Shoe purchases.
```

---

# 9. Product Affinity

Find products frequently purchased together.

Use:

* co-occurrence
* support
* confidence
* lift

Example:

```text
Wireless Headphones
        │
        ▼
Charging Cable

Customers buying headphones:
4,821

Customers buying both:
1,102

Affinity:
HIGH
```

Technical metrics can be shown under:

> View technical details

The primary UI remains human-friendly.

---

# 10. Opportunity Radar

The Opportunity Radar continuously searches for:

### Risks

* churn increasing
* retention declining
* high-value customers becoming inactive
* product sales falling
* category decline
* review deterioration
* return rate increases
* revenue anomalies

### Opportunities

* cross-sell
* upsell
* product gaps
* customer reactivation
* high-value customer retention
* category expansion
* product combinations

Example:

```text
┌──────────────────────────────────────┐
│ 🔥 CROSS-SELL OPPORTUNITY            │
│                                      │
│ Running Shoes → Sports Accessories   │
│                                      │
│ Potential customers: 7,319          │
│ Confidence: High                     │
│                                      │
│ Recommended action:                  │
│ Test post-purchase recommendations   │
└──────────────────────────────────────┘
```

---

# 11. Business Health

Generate a high-level business health score.

Potential dimensions:

```text
Revenue
Customer Health
Retention
Product Health
Growth
Opportunities
Risks
```

Example:

```text
BUSINESS HEALTH

78 / 100

Healthy

✓ Revenue growing
✓ New customer acquisition stable
⚠ Repeat purchase declining
⚠ Electronics category weakening

Top priority:
Improve Electronics customer retention.
```

The score must remain explainable.

---

# 12. "Why Did This Happen?"

InsightCart should attempt to explain major changes.

Example:

```text
Revenue ↓ 14%

Why?

1. Returning customer revenue ↓ 19%
2. Electronics revenue ↓ 23%
3. AOV ↓ 7%

Largest contributor:
Returning customers

Recommended action:
Target previously active Electronics customers.
```

---

# 13. Recommended Actions

InsightCart should translate analytics into actions.

Examples:

```text
High churn + high value
→ Priority retention outreach

Recently purchased
→ Cross-sell recommendation

Strong product affinity
→ Bundle recommendation

Low category penetration
→ Product recommendation campaign

Revenue anomaly
→ Investigate affected category

Declining repeat purchases
→ Re-engagement campaign
```

---

# ⚠️ Important: Causal Claims

InsightCart must **not** claim:

```text
"Giving this customer a 10% discount will reduce
their churn probability from 82% to 54%."
```

unless historical intervention/treatment data exists and a valid causal or uplift model has been implemented.

Without causal data, say:

```text
Recommended Action:
Consider a targeted retention offer.
```

not:

```text
Predicted impact:
Churn will decrease by 28%.
```

This distinction is important for a credible data science project.

---

# 📊 Olist Dataset

The initial demonstration dataset will be the:

**Brazilian E-Commerce Public Dataset by Olist**

The dataset contains related information around:

* customers
* orders
* order items
* products
* payments
* reviews
* sellers
* geolocation

It is an excellent real-world dataset for demonstrating InsightCart because it is relational and contains multiple business dimensions.

---

# 🔑 Olist Is Only the Demo Dataset

InsightCart must **not** be hard-coded around Olist.

The architecture must support arbitrary e-commerce datasets.

For example:

### Company A

```text
cust_id
purchase_dt
amount
item_name
```

### Company B

```text
user
transaction_date
total
sku
```

InsightCart should map both into:

```text
customer_id
order_date
order_value
product_id
```

This is achieved through the **Canonical E-Commerce Schema**.

---

# 🏗 Generalized SaaS Architecture

```text
                         COMPANY DATA
                              │
                 ┌────────────┴────────────┐
                 │                         │
                CSV                      Excel
                 │                         │
                 └────────────┬────────────┘
                              ▼
                    DATA INGESTION ENGINE
                              │
                              ▼
                    SCHEMA DETECTION
                              │
                              ▼
                     COLUMN MAPPING
                              │
                              ▼
                     DATA VALIDATION
                              │
                              ▼
                        PostgreSQL
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
       CUSTOMERS          PRODUCTS           BUSINESS
           │                  │                  │
           ▼                  ▼                  ▼
       RFM / CLV          AFFINITY            REVENUE
       RETENTION          CROSS-SELL          AOV
       COHORTS            PRODUCT GAPS        TRENDS
       CHURN              PRODUCT HEALTH      HEALTH
           │                  │                  │
           └──────────────────┼──────────────────┘
                              ▼
                      INSIGHT ENGINE
                              │
                              ▼
                    OPPORTUNITY RADAR
                              │
                              ▼
                    RECOMMENDED ACTIONS
                              │
                              ▼
                    FastAPI REST API
                              │
                              ▼
                  React + TypeScript UI
```

---

# 🔄 Data Flow

```text
Raw CSV
   ↓
Upload
   ↓
File Validation
   ↓
Schema Detection
   ↓
Column Mapping
   ↓
Data Quality Checks
   ↓
Cleaning / Transformation
   ↓
Canonical Schema
   ↓
PostgreSQL
   ↓
Analytical SQL
   ↓
Customer/Product Features
   ↓
Machine Learning
   ↓
Insight Engine
   ↓
REST API
   ↓
React UI
```

---

# 🛠 Technology Stack

Everything in the MVP is free and open-source.

## Frontend

* React
* Vite
* TypeScript
* Tailwind CSS
* Recharts

## Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* psycopg
* Alembic

## Data Processing

* Pandas
* NumPy

## Database

* PostgreSQL

## Machine Learning

* Scikit-learn
* XGBoost
* Joblib

## Testing

* Pytest
* Vitest

## Infrastructure

* Docker
* Docker Compose
* Git
* GitHub

---

# 💰 Free / Open-Source Requirement

InsightCart must be fully runnable without paid services.

### DO NOT REQUIRE

* OpenAI API
* Claude API
* Gemini API
* AWS
* Azure
* Google Cloud
* Snowflake
* Databricks
* paid BI software
* paid databases
* paid analytics APIs

The complete MVP should run locally.

---

# 🏛 System Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                    REACT FRONTEND                       │
│                                                         │
│ Dashboard │ Customers │ Products │ Opportunities       │
│                                                         │
│ Data Upload │ Business Health │ Model Performance      │
└──────────────────────────┬──────────────────────────────┘
                           │
                        REST API
                           │
┌──────────────────────────▼──────────────────────────────┐
│                     FASTAPI                             │
│                                                         │
│ Customer APIs │ Product APIs │ Business APIs            │
│ Opportunity APIs │ Upload APIs │ ML APIs                │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                 APPLICATION SERVICES                    │
│                                                         │
│ Customer Intelligence                                  │
│ Product Intelligence                                   │
│ Business Analytics                                     │
│ Opportunity Engine                                     │
│ Insight Engine                                         │
│ ML Services                                            │
│ Data Processing                                        │
└──────────────────────────┬──────────────────────────────┘
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
           PostgreSQL            ML Models
                                 Joblib/XGBoost
```

---

# 🗄 Canonical Data Model

The initial canonical schema contains:

## Customers

```text
customer_id
customer_unique_id
customer_city
customer_state
customer_country
created_at
```

## Orders

```text
order_id
customer_id
order_date
order_status
order_value
```

## Order Items

```text
order_id
product_id
customer_id
quantity
unit_price
discount
```

## Products

```text
product_id
product_name
category
brand
price
cost
created_at
```

Optional entities:

```text
reviews
payments
sellers
marketing
support
returns
```

InsightCart should gracefully degrade when optional fields are unavailable.

---

# 📁 Project Folder Structure

```text
insightcart/
│
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── docker-compose.yml
├── TEAM_CONTRACT.md
│
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   │
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       │
│       ├── components/
│       │   ├── ui/
│       │   ├── charts/
│       │   ├── cards/
│       │   ├── tables/
│       │   ├── layout/
│       │   └── shared/
│       │
│       ├── features/
│       │   ├── dashboard/
│       │   ├── customers/
│       │   ├── products/
│       │   ├── opportunities/
│       │   ├── business/
│       │   └── data/
│       │
│       ├── pages/
│       │   ├── Landing.tsx
│       │   ├── Dashboard.tsx
│       │   ├── Customers.tsx
│       │   ├── Customer360.tsx
│       │   ├── Products.tsx
│       │   ├── ProductDetail.tsx
│       │   ├── Opportunities.tsx
│       │   ├── BusinessHealth.tsx
│       │   ├── DataUpload.tsx
│       │   └── ModelPerformance.tsx
│       │
│       ├── services/
│       │   ├── api.ts
│       │   ├── customerApi.ts
│       │   ├── productApi.ts
│       │   ├── businessApi.ts
│       │   └── opportunityApi.ts
│       │
│       ├── hooks/
│       ├── types/
│       ├── utils/
│       └── lib/
│
├── backend/
│   ├── requirements.txt
│   ├── pyproject.toml
│   │
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   ├── router.py
│   │   │   ├── customers.py
│   │   │   ├── products.py
│   │   │   ├── business.py
│   │   │   ├── opportunities.py
│   │   │   ├── upload.py
│   │   │   └── ml.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   │
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   ├── base.py
│   │   │   └── migrations/
│   │   │
│   │   ├── models/
│   │   │   ├── customer.py
│   │   │   ├── order.py
│   │   │   ├── order_item.py
│   │   │   ├── product.py
│   │   │   └── opportunity.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── customer.py
│   │   │   ├── product.py
│   │   │   ├── business.py
│   │   │   └── opportunity.py
│   │   │
│   │   └── services/
│   │       ├── ingestion/
│   │       ├── validation/
│   │       ├── customers/
│   │       ├── products/
│   │       ├── analytics/
│   │       ├── ml/
│   │       ├── insights/
│   │       └── opportunities/
│   │
│   └── tests/
│       ├── test_customers.py
│       ├── test_products.py
│       ├── test_analytics.py
│       ├── test_ml.py
│       └── test_api.py
│
├── ml/
│   ├── models/
│   │   ├── churn/
│   │   └── recommendation/
│   │
│   ├── training/
│   │   ├── train_churn.py
│   │   └── train_next_purchase.py
│   │
│   └── evaluation/
│       └── metrics.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── demo/
│
├── sql/
│   ├── schema.sql
│   ├── analytics/
│   └── views/
│
├── scripts/
│   ├── import_olist.py
│   ├── seed_demo.py
│   └── reset_database.py
│
└── docs/
    ├── architecture.md
    ├── api.md
    ├── data-model.md
    └── ml.md
```

---

# 🎨 Frontend Structure

The frontend uses:

```text
React
+
TypeScript
+
Vite
+
Tailwind CSS
+
Recharts
```

Major sections:

```text
/
├── Landing
│
├── Dashboard
│
├── Customers
│   ├── Customer Intelligence
│   ├── Segmentation
│   ├── Customer 360
│   ├── Churn
│   └── Retention
│
├── Products
│   ├── Product Intelligence
│   ├── Product Detail
│   ├── Product Gaps
│   └── Product Affinity
│
├── Opportunities
│
├── Business Health
│
├── Data
│   ├── Upload
│   ├── Mapping
│   └── Quality
│
└── Model Performance
```

---

# 🐍 Backend Structure

The backend is divided by business domain rather than by technical layer alone.

```text
services/
│
├── ingestion/
│
├── validation/
│
├── customers/
│
├── products/
│
├── analytics/
│
├── ml/
│
├── insights/
│
└── opportunities/
```

This makes it easier for two developers to work independently.

---

# 🤖 Machine Learning

## Churn Prediction

Initial models:

```text
Logistic Regression
Random Forest
XGBoost
```

Features:

```text
recency_days
total_orders
total_revenue
purchase_frequency
average_order_value
days_between_orders
discount_usage
return_rate
category_count
customer_lifetime_days
```

Evaluate:

```text
Precision
Recall
F1
ROC-AUC
Confusion Matrix
```

The selected model should be saved with Joblib.

---

# 📈 Customer Lifetime Value

CLV should be implemented transparently.

Depending on available data, InsightCart can begin with a historical CLV approach:

```text
Customer Revenue
+
Purchase Frequency
+
Customer Lifetime
```

More advanced probabilistic CLV models can be added later.

---

# 🧩 Insight Engine

The Insight Engine converts analytical results into business explanations.

Each insight should have a structure similar to:

```json
{
  "id": "opp_001",
  "type": "cross_sell",
  "severity": "high",
  "title": "Strong cross-sell opportunity",
  "summary": "Running Shoe buyers rarely purchase Sports Accessories.",
  "evidence": {},
  "business_impact": {},
  "recommended_action": "Test post-purchase recommendations.",
  "confidence": "high"
}
```

---

# 🎯 Opportunity Engine

The Opportunity Engine detects:

```text
Risk
Opportunity
Anomaly
Trend
```

Every opportunity should answer:

### What happened?

### Why does it matter?

### What evidence supports it?

### What should the business do?

### How confident are we?

---

# 👥 Customer Intelligence

Customer analytics include:

```text
RFM
CLV
Retention
Cohorts
Repeat Purchase
Purchase Frequency
Customer Health
Churn
Customer Segments
Customer 360
```

---

# 📦 Product Intelligence

Product analytics include:

```text
Revenue
Units Sold
Orders
Unique Customers
Average Price
Product Growth
Category Growth
Product Health
Product Affinity
Cross-Sell
Product Gaps
```

---

# 🔎 Opportunity Radar

The Opportunity Radar is intended to be one of the most visible features in InsightCart.

Example:

```text
TODAY'S TOP OPPORTUNITIES

🔥 High-value customer retention

1,284 high-value customers are
past their normal purchase interval.

Recommended:
Launch a targeted re-engagement campaign.

────────────────────────────

📈 Cross-sell opportunity

Running Shoe customers show strong
affinity with Sports Accessories.

Potential customers:
7,319

Recommended:
Test post-purchase recommendations.

────────────────────────────

⚠ Product risk

Electronics revenue has declined 23%.

Largest contributor:
Returning customers.

Recommended:
Investigate customer retention in Electronics.
```

---

# 📤 Data Upload Experience

InsightCart should have a guided ingestion flow.

## Step 1 — Upload

Initially:

```text
CSV
```

Future:

```text
Excel
Database
API
```

---

## Step 2 — Understand Dataset

Example:

```text
✓ Orders detected
✓ Customers detected
✓ Products detected
✓ Payments detected
✓ Reviews detected

⚠ Returns data not detected
⚠ Marketing data not detected
```

---

## Step 3 — Column Mapping

Example:

```text
Your column             InsightCart field

cust_id                 → customer_id
purchase_timestamp      → order_date
amount                  → order_value
item_name               → product_name
```

---

## Step 4 — Data Quality

Example:

```text
DATA QUALITY

94%

✓ 98,421 valid orders
✓ 31,204 customers
✓ 12,402 products

⚠ 1,204 missing categories
⚠ 182 duplicate records
```

---

## Step 5 — Processing

```text
Understanding data...
Cleaning data...
Building customer features...
Building product features...
Running analytics...
Generating insights...
```

Then:

> **Your InsightCart workspace is ready.**

---

# 🧑‍💻 Human-Friendly UX

The target user is not a data scientist.

Avoid:

```text
RFM = 422
```

Prefer:

```text
Loyal Customer
```

Avoid:

```text
churn_probability = 0.82
```

Prefer:

```text
High Risk — 82% likelihood of churn
```

Avoid:

```text
lift = 3.82
```

Prefer:

```text
Customers who buy Product A are much more
likely to buy Product B.
```

Technical information can be available through:

```text
View technical details
```

---

# 🔌 API Structure

## General

```http
GET /api/health
GET /api/dashboard/overview
```

---

## Customers

```http
GET /api/customers
GET /api/customers/{customer_id}
GET /api/customers/{customer_id}/360
GET /api/customers/{customer_id}/churn
GET /api/customers/{customer_id}/recommendation
GET /api/customers/{customer_id}/next-purchase

GET /api/customers/segments
GET /api/customers/rfm
GET /api/customers/retention
GET /api/customers/cohorts
```

---

## Products

```http
GET /api/products
GET /api/products/{product_id}
GET /api/products/{product_id}/health

GET /api/products/categories
GET /api/products/affinity
GET /api/products/cross-sell
GET /api/products/gaps
```

---

## Business

```http
GET /api/business/revenue
GET /api/business/aov
GET /api/business/trends
GET /api/business/health
```

---

## Opportunities

```http
GET /api/opportunities
GET /api/opportunities/{opportunity_id}
```

---

## ML

```http
GET /api/churn/summary
GET /api/model/metrics
```

---

# 👨‍💻 Development Strategy

This project is being developed by **two people**.

The team should NOT divide work like:

```text
Person 1 = Backend
Person 2 = Frontend
```

That creates unnecessary dependencies.

Instead, use **vertical ownership**.

Each developer owns:

```text
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

for their respective business domain.

---

# 👤 Developer 1 — Customer Intelligence

Developer 1 owns:

```text
CUSTOMER DOMAIN

Data
 ↓
Database
 ↓
Analytics
 ↓
ML
 ↓
API
 ↓
React UI
 ↓
Tests
```

Responsibilities:

### Data

* customer ingestion
* customer validation
* customer schema

### Analytics

* RFM
* CLV
* retention
* cohort analysis
* repeat purchases
* purchase frequency
* customer health

### ML

* churn prediction
* customer value
* next purchase/category prediction

### API

```http
/api/customers/*
```

### Frontend

```text
Customer Intelligence
Customer Segmentation
Customer 360
Churn Intelligence
Customer Retention
```

---

# 👤 Developer 2 — Product + Business Intelligence

Developer 2 owns:

```text
PRODUCT + BUSINESS DOMAIN

Data
 ↓
Database
 ↓
Analytics
 ↓
Intelligence
 ↓
Opportunity Engine
 ↓
API
 ↓
React UI
 ↓
Tests
```

Responsibilities:

### Data

* product ingestion
* order-item ingestion
* product validation

### Analytics

* revenue
* AOV
* product performance
* category performance
* product affinity
* cross-sell
* product gaps

### Intelligence

* anomaly detection
* opportunity detection
* product health
* business health

### API

```http
/api/products/*
/api/business/*
/api/opportunities/*
```

### Frontend

```text
Executive Overview
Product Intelligence
Product Detail
Product Gaps
Opportunity Radar
Business Health
```

---

# 🤝 Shared Responsibilities

Both developers collaborate on:

```text
Canonical schema
API conventions
Docker
Database infrastructure
Authentication/workspaces
Environment configuration
Shared React components
Common TypeScript types
Documentation
```

Before changing a shared contract:

1. Inspect current implementation.
2. Preserve compatibility.
3. Document the change.
4. Inform the other developer.

Do not repeatedly rewrite shared infrastructure.

---

# ⚡ Parallel Development

The two developers should be able to work simultaneously.

Example:

```text
                    SHARED FOUNDATION
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
       DEVELOPER 1                 DEVELOPER 2
       CUSTOMER                    PRODUCT/BUSINESS
             │                           │
             ▼                           ▼
       Customer DB                  Product DB
             │                           │
             ▼                           ▼
       Customer Analytics          Product Analytics
             │                           │
             ▼                           ▼
       Churn ML                    Opportunity Engine
             │                           │
             ▼                           ▼
       Customer API                Product API
             │                           │
             ▼                           ▼
       Customer UI                 Product UI
             │                           │
             └─────────────┬─────────────┘
                           ▼
                       INTEGRATION
```

---

# 🗓 Development Roadmap

## Phase 0 — Foundation

Both developers:

* initialize repository
* configure Docker
* configure PostgreSQL
* configure FastAPI
* configure React
* configure TypeScript
* configure Tailwind
* configure Alembic
* establish canonical schema
* establish API conventions
* create TEAM_CONTRACT.md

---

# Phase 1 — Data Ingestion

### Developer 1

```text
Customer ingestion
Order ingestion
Customer validation
```

### Developer 2

```text
Product ingestion
Order-item ingestion
Product validation
```

---

# Phase 2 — Analytics

### Developer 1

```text
RFM
CLV
Retention
Cohorts
Repeat Purchase
Customer Health
```

### Developer 2

```text
Revenue
AOV
Product Analytics
Category Analytics
Affinity
Cross-Sell
Product Gaps
```

---

# Phase 3 — Machine Learning / Intelligence

### Developer 1

```text
Churn Prediction
Customer Value
Next Purchase Prediction
```

### Developer 2

```text
Anomaly Detection
Opportunity Detection
Product Health
Business Health
Cross-Sell Scoring
```

---

# Phase 4 — Decision Intelligence

Combine analytics and ML into:

```text
Problem
 ↓
Evidence
 ↓
Business Impact
 ↓
Recommended Action
 ↓
Confidence
```

---

# Phase 5 — SaaS Experience

Implement:

```text
Landing Page
Workspace
Upload Wizard
Column Mapping
Data Quality
Dashboard
Customer Intelligence
Product Intelligence
Opportunity Radar
Business Health
```

---

# Phase 6 — Advanced Intelligence

After the MVP:

```text
Ask Your Data
Explain This
Next Best Action
What-if Analysis
Automated Reports
Uplift Modeling
Multi-workspace architecture
```

---

# 📅 Suggested 9-Week Plan

| Week | Developer 1                 | Developer 2                         |
| ---- | --------------------------- | ----------------------------------- |
| 1    | Customer schema + ingestion | Product schema + ingestion          |
| 2    | RFM + customer analytics    | Product + revenue analytics         |
| 3    | Cohorts + retention         | Product affinity + cross-sell       |
| 4    | Churn ML                    | Product gaps + anomaly detection    |
| 5    | Customer 360                | Opportunity Radar + business health |
| 6    | Customer React UI           | Product/business React UI           |
| 7    | API integration             | API integration                     |
| 8    | Testing + data quality      | Testing + UI polish                 |
| 9    | Integration + intelligence  | Integration + intelligence          |

Both developers should have meaningful work throughout the project.

---

# 🌿 Git Strategy

Recommended branches:

```text
main

dev/customer-intelligence

dev/product-business-intelligence
```

Use focused commits.

Examples:

```text
feat(customer): add canonical customer ingestion

feat(customer): implement RFM segmentation

feat(customer): add churn pipeline

feat(customer-ui): add customer 360

feat(product): add product analytics

feat(product): implement affinity engine

feat(opportunity): add cross-sell detection

feat(product-ui): add product intelligence
```

Avoid huge commits containing unrelated changes.

---

# 🧪 Testing

Testing is part of the feature, not an afterthought.

## Backend

Test:

* ingestion
* validation
* RFM
* CLV
* retention
* cohorts
* churn features
* churn model
* recommendation logic
* product analytics
* affinity
* cross-sell
* opportunity engine
* API endpoints

## Frontend

Test:

* major pages
* API integration
* loading states
* error states
* empty states
* important components
* filters
* tables
* charts

---

# 🐳 Running Locally

## Prerequisites

Install:

```text
Node.js
npm
Python 3.x
Docker
Docker Compose
Git
```

---

## Clone

```bash
git clone <repository-url>
cd insightcart
```

---

## Start PostgreSQL

```bash
docker compose up -d postgres
```

---

## Backend

```bash
cd backend

python -m venv .venv
```

### Linux / macOS

```bash
source .venv/bin/activate
```

### Windows

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
alembic upgrade head
```

Start FastAPI:

```bash
uvicorn app.main:app --reload
```

---

# 💻 Frontend

```bash
cd frontend
npm install
npm run dev
```

The React application will run locally.

---

# 🐳 Full Docker Development

Eventually the entire application should be runnable through:

```bash
docker compose up --build
```

The goal is:

```text
Frontend
+
Backend
+
PostgreSQL
```

running locally.

---

# 🔐 Environment Variables

Create:

```text
.env
```

based on:

```text
.env.example
```

Example:

```env
DATABASE_URL=postgresql://insightcart:insightcart@localhost:5432/insightcart

API_HOST=0.0.0.0
API_PORT=8000

ENVIRONMENT=development
```

Never commit secrets.

---

# 🧠 Future Feature: Ask Your Data

A future version can support natural-language questions.

Example:

```text
Why did revenue fall last month?
```

Instead of requiring a paid LLM API, the first implementation should use deterministic intent mapping:

```text
User Question
      ↓
Intent Detection
      ↓
Known Analytics Function
      ↓
SQL
      ↓
Statistics / ML
      ↓
Human-Friendly Explanation
```

For example:

```text
"Which products are bought together?"

        ↓

Intent:
PRODUCT_AFFINITY

        ↓

Affinity service

        ↓

SQL

        ↓

Results

        ↓

Explanation
```

An LLM can optionally be added later.

---

# 🔮 Future Features

Potential future versions can include:

## Data Sources

```text
CSV
Excel
PostgreSQL
MySQL
REST APIs
Shopify
WooCommerce
Magento
```

---

## Advanced ML

```text
Customer Lifetime Value models
Uplift modeling
Next Best Action
Demand forecasting
Recommendation systems
Price optimization
Customer propensity
```

---

## Advanced SaaS

```text
Multiple workspaces
Role-based access
Team collaboration
Scheduled reports
Email alerts
Saved dashboards
Data connectors
```

---

# 🏆 Project Differentiation

The project should demonstrate much more than:

```text
Python
SQL
Power BI
ML
```

It demonstrates an entire data product:

```text
DATA ENGINEERING
       +
DATABASE DESIGN
       +
ANALYTICAL SQL
       +
STATISTICS
       +
MACHINE LEARNING
       +
BACKEND DEVELOPMENT
       +
FRONTEND DEVELOPMENT
       +
PRODUCT DESIGN
       +
DECISION INTELLIGENCE
```

That makes InsightCart substantially stronger as a portfolio project.

---

# 📄 Resume Description

### Short Version

> Built InsightCart, an end-to-end e-commerce decision intelligence platform using Python, PostgreSQL, FastAPI, React, and XGBoost to analyze 100K+ transactions, perform RFM/cohort analysis, predict customer churn, identify product affinity and cross-sell opportunities, and generate human-readable retention recommendations.

### Stronger Version

> Developed InsightCart, a generalized e-commerce decision intelligence SaaS that transforms raw transaction datasets into customer, product, and business insights; engineered a Python/PostgreSQL data pipeline, implemented RFM, CLV, cohort and retention analytics, trained churn prediction models using Scikit-learn/XGBoost, and built an explainable opportunity engine with a React/FastAPI interface.

---

# 🎯 Definition of Done

The MVP is complete when a user can:

```text
1. Start InsightCart locally
             ↓
2. Upload Olist data
             ↓
3. Map columns
             ↓
4. Validate the dataset
             ↓
5. See data quality
             ↓
6. See business health
             ↓
7. Explore customers
             ↓
8. Explore customer segments
             ↓
9. View RFM and cohorts
             ↓
10. View churn predictions
             ↓
11. Explore products
             ↓
12. View product affinity
             ↓
13. Discover product gaps
             ↓
14. View opportunities
             ↓
15. See recommended actions
```

The user should not need:

```text
SQL
Python
Statistics
Machine Learning
```

knowledge to understand the results.

---

# 🤝 Team Contract

The repository should contain:

```text
TEAM_CONTRACT.md
```

with:

```text
# INSIGHTCART TEAM CONTRACT

Developer 1:
Customer Intelligence

Developer 2:
Product + Business Intelligence

Neither developer may rewrite the other's vertical.

Shared:
- canonical schema
- API conventions
- Docker
- authentication
- environment variables
- common UI components

Before changing a shared contract:
- inspect current implementation
- preserve compatibility
- document the change
- communicate the change

Never commit secrets.

Never use paid APIs.

Everything must run locally.
```

---

# 🧭 Product Philosophy

InsightCart should always follow this hierarchy:

```text
                    DATA

                     ↓

                  METRIC

                     ↓

                  PATTERN

                     ↓

                 EXPLANATION

                     ↓

                OPPORTUNITY

                     ↓

                   ACTION
```

The ultimate goal is not to produce more charts.

It is to help a business answer:

> **"What should I do next?"**

---

# 🚀 Final Vision

InsightCart should eventually feel less like a BI dashboard and more like an **AI-powered business analyst that works directly from a company's data** — while keeping the core analytics explainable, reproducible, and free/open-source.

The final product experience should look conceptually like:

```text
                         INSIGHTCART
                              │
                              ▼
                     UPLOAD YOUR DATA
                              │
                              ▼
                  WE UNDERSTAND YOUR DATA
                              │
                              ▼
                    ┌─────────────────┐
                    │ BUSINESS HEALTH │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
      CUSTOMERS          PRODUCTS         OPPORTUNITIES
          │                  │                  │
          ▼                  ▼                  ▼
        Churn             Affinity           Cross-sell
        RFM               Product Gaps       Retention
        CLV               Product Health     Revenue
        Cohorts           Trends             Risks
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
                       WHAT TO DO NEXT
```

### InsightCart

> **Your e-commerce data already knows what is happening.**
>
> **InsightCart helps you understand why — and what to do about it.**

---

# 📜 License
MIT License


Choose an appropriate open-source license before public release.
