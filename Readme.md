# InsightCart

InsightCart is an e-commerce analytics, predictive modeling, and conversational data querying platform. It was built as an end-to-end data science and analytics project to turn raw e-commerce transaction data into customer intelligence, churn predictions, and an ambiguity-aware natural language query interface.

Traditional dashboards display static metrics without explaining customer behavior, while standard text-to-SQL tools guess when business questions have multiple interpretations. InsightCart pairs statistical customer segmentation and machine learning with a query engine that asks clarifying questions before running SQL.

---

## What the System Does

### 1. Customer Analytics and Segmentation
* **RFM Segmentation**: Calculates Recency, Frequency, and Monetary quintiles (1–5) and maps customers into behavioral segments including *Champions*, *Loyal Customers*, *Potential Loyalists*, *At Risk*, *Cannot Lose Them*, and *Hibernating*.
* **Customer Lifetime Value (CLV)**: Computes historical customer lifetime value with mean, median, and top 10% benchmark thresholds.
* **Retention and Cohorts**: Computes repeat purchase rates, 30/60/90/180/365-day retention decay curves, and monthly acquisition cohort retention matrices.
* **Customer Health Score**: Calculates a composite 0–100 score based on recency decay, order frequency, monetary contribution, and purchasing consistency, grouping accounts into Healthy, At-Risk, and Critical.
* **Customer 360 View**: Aggregates a single customer's order history, RFM classification, predicted churn risk, and health score into a single profile.

### 2. Machine Learning Pipelines
* **Feature Engineering**: Derives 10 behavioral features per customer from order history, including purchase frequency, average order value, order cancellation rates, and product diversity.
* **Target Leakage Prevention**:
  * Excludes `recency_days` from churn model features because recency deterministically encodes the churn threshold (inactivity > 90 days), preventing artificially inflated evaluation scores.
  * Excludes `days_between_orders` and lifetime ratio features from next-purchase interval training to avoid mathematical leakage into the regression target.
* **Churn Classification**:
  * Trains and evaluates Logistic Regression, Random Forest, and XGBoost classifiers.
  * Tracks Accuracy, Precision, Recall, F1-score, and ROC-AUC.
  * Automatically selects and serializes the best-performing model to `ml/models/churn/` via Joblib.
  * Provides on-demand training and batch prediction endpoints.
* **Next Purchase Interval Prediction**:
  * Uses a statistical inter-purchase baseline for customers with sparse order histories.
  * Trains a Gradient Boosted Regressor when sufficient repeat purchase history exists.

### 3. Ask Your Data (Text-to-SQL with Clarification)
Most text-to-SQL systems make silent assumptions when questions are ambiguous. For example, "Who is our best customer?" can mean highest total spend, highest order count, or highest visit frequency.

* **Clarification Engine**: Detects underspecified terms against a semantic business glossary and pauses execution to ask the user what they mean before generating SQL.
* **Dual Execution Modes**:
  * **Offline Planner (Default)**: Uses a deterministic rule-based semantic parser. Runs locally with zero API keys, no network calls, and zero external costs.
  * **LLM Mode (Optional)**: Uses Groq or Google Gemini free-tier models with structured JSON outputs validated against Pydantic schemas.
* **SQL Guard**: Enforces read-only execution by rejecting write operations (`INSERT`, `UPDATE`, `DELETE`, `DROP`), multiple statements, comments, and dangerous PostgreSQL functions.
* **Evaluation Benchmark**: Evaluated on 30 test cases (14 ambiguous, 16 clear):
  * Baseline (direct guessing): 70% overall accuracy (36% on ambiguous questions).
  * Clarification engine: 100% accuracy on ambiguous questions with 0 false clarifications on clear questions.

### 4. Data Pipeline and Storage
* **Validation and Ingestion**: Validates raw customer and order CSV datasets, handles missing attributes, normalizes timestamps, and tracks batch ingestion statistics.
* **Relational Schema**: Stores transactions across `customers`, `orders`, `order_items`, `products`, and `payments` tables in PostgreSQL, with a separate `ask_demo` schema for sandboxed query execution.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **Backend & API** | Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Uvicorn |
| **Database** | PostgreSQL 16 (psycopg3 driver) |
| **Data Processing & ML** | Pandas, NumPy, Scikit-learn, XGBoost, Joblib |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS |
| **Evaluation & Tests** | Pytest, HTTPX |
| **Infrastructure** | Docker, Docker Compose |

---

## Project Structure

```text
InsightCart/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI route handlers (customers, ml, ask, upload)
│   │   ├── core/            # App configuration and settings
│   │   ├── db/              # SQLAlchemy session and engine management
│   │   ├── models/          # SQLAlchemy database models (Customer, Order)
│   │   ├── schemas/         # Pydantic request/response validation models
│   │   └── services/
│   │       ├── analytics/   # Customer analytics orchestration
│   │       ├── ask/         # Text-to-SQL engine, glossary, planner, and SQL guard
│   │       ├── customers/   # RFM, CLV, retention, cohorts, and health scoring
│   │       ├── ingestion/   # CSV parsing and batch database ingestion
│   │       ├── ml/          # Feature engineering pipelines
│   │       └── validation/  # Data schema validators
│   ├── requirements.txt     # Python backend dependencies
│   └── tests/               # Pytest suite for API, analytics, ML, and Ask
├── frontend/
│   ├── src/
│   │   ├── pages/           # React pages (Landing, Ask Your Data workspace)
│   │   ├── services/        # API client and Ask service bindings
│   │   ├── App.tsx          # Router configuration
│   │   └── main.tsx         # Frontend entrypoint
│   └── package.json         # Frontend dependencies and Vite scripts
├── ml/
│   ├── evaluation/          # Ask evaluation cases and model metrics
│   ├── models/              # Serialized model artifacts and metadata
│   └── training/            # Churn and next-purchase training pipelines
├── scripts/
│   ├── eval_ask.py          # Benchmark runner for text-to-SQL accuracy
│   └── seed_ask_demo.py     # Deterministic demo dataset generator
├── sql/
│   └── ask/
│       └── schema.sql       # DDL schema for the text-to-SQL sandbox
├── docker-compose.yml       # Local PostgreSQL container definition
└── .env.example             # Template for local environment variables
```

---

## Local Setup

### Prerequisites
* Python 3.11+
* Node.js 18+ and npm
* Docker (for local PostgreSQL)

### 1. Database Setup
Start the PostgreSQL container:

```bash
docker compose up -d
```

Or start a standalone container:

```powershell
docker run -d --name insightcart-postgres -e POSTGRES_USER=insightcart -e POSTGRES_PASSWORD=insightcart -e POSTGRES_DB=insightcart -p 5432:5432 postgres:16
```

### 2. Backend Setup
Navigate to the backend directory, create a virtual environment, and install dependencies:

```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

Create your `.env` file in the project root:

```bash
cp ../.env.example ../.env
```

Default connection string in `.env`:
```text
DATABASE_URL=postgresql+psycopg://insightcart:insightcart@localhost:5432/insightcart
```

### 3. Seed Demo Data
Seed the `ask_demo` schema with reproducible e-commerce scenarios:

```bash
python ../scripts/seed_ask_demo.py
```

### 4. Start the Backend API
From the `backend/` directory:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The interactive API documentation is available at `http://localhost:8000/docs`.

### 5. Frontend Setup
In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` to access the application.

---

## Running Evaluations and Tests

### Backend Unit and Integration Tests
From the `backend/` directory:

```bash
pytest tests
```

### Text-to-SQL Benchmark Evaluation
Run the automated benchmark comparing direct query generation against the clarification engine across 30 test cases:

```bash
# Offline deterministic planner (free, no API key required):
python scripts/eval_ask.py

# Optional: Run against Groq or Gemini (requires GROQ_API_KEY or GEMINI_API_KEY in .env):
python scripts/eval_ask.py --provider groq
python scripts/eval_ask.py --provider gemini
```

---

## API Reference

### Health and Data Ingestion
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System liveness probe |
| `POST` | `/api/data/upload` | Upload customer or order CSV files |
| `POST` | `/api/data/upload/bundle` | Upload combined customer, order, and payment CSVs |
| `GET` | `/api/data/summary` | Summary of ingested rows, revenue, and date ranges |

### Customer Analytics
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/customers` | Paginated customer list |
| `GET` | `/api/customers/rfm` | RFM segment overview and distribution counts |
| `GET` | `/api/customers/segments` | Segment breakdown with customer counts and average spend |
| `GET` | `/api/customers/retention` | Repeat purchase rate and retention decay curve |
| `GET` | `/api/customers/cohorts` | Monthly acquisition cohort retention matrix |
| `GET` | `/api/customers/health` | Distribution of customer health scores |
| `GET` | `/api/customers/{customer_id}` | Customer 360 profile view |
| `GET` | `/api/customers/{customer_id}/churn` | Churn prediction for a specific customer |
| `GET` | `/api/customers/{customer_id}/next-purchase` | Predicted next-purchase interval and date |

### Machine Learning
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/ml/churn/summary` | Churn risk distribution across all customers |
| `GET` | `/api/ml/model/metrics` | Evaluation metrics for trained churn and next-purchase models |
| `POST` | `/api/ml/train` | Retrains models on current database records and saves artifacts |

### Ask Your Data
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/ask` | Natural language query endpoint. Returns either a clarification request or executable SQL with result rows |

---

## License
MIT License. See [LICENSE](LICENSE) for details.
