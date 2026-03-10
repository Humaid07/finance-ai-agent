# Finance AI Agent Platform

A production-grade Finance Analytics and AI Assistant platform built on Microsoft Azure.

## Architecture Overview

```
finance-ai-agent/
├── frontend/          # React + TypeScript + Vite + Tailwind
├── backend/           # Python Azure Functions v2 + SQLAlchemy
├── infra/             # Azure Bicep infrastructure as code
├── scripts/           # DB schema creation + seed data
└── docker-compose.yml # Local PostgreSQL + Azurite
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, Recharts |
| Backend | Python 3.11, Azure Functions v2, SQLAlchemy 2.0 |
| Database | Azure Database for PostgreSQL (Flexible Server) |
| AI | Azure OpenAI (GPT-4o) with tool-based agent architecture |
| Infrastructure | Azure Bicep, Azure Functions, Key Vault, App Insights |

---

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker Desktop
- Azure Functions Core Tools v4: `npm i -g azure-functions-core-tools@4`
- Azure CLI (for cloud deployment)

---

### Step 1 — Start Local Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL on port 5432
- Azurite (Azure Storage emulator) on ports 10000-10002

---

### Step 2 — Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy settings
cp local.settings.json.example local.settings.json

# Edit local.settings.json with your DB credentials (defaults work with docker-compose)
```

---

### Step 3 — Create Schema & Seed Data

```bash
# From project root (with .venv active)
cd backend
python ../scripts/create_schema.py
python ../scripts/seed_data.py
```

---

### Step 4 — Start Backend

```bash
cd backend
func start
```

Backend runs at: `http://localhost:7071/api`

Available endpoints:
- `GET  /api/health`
- `GET  /api/hierarchy/tree`
- `GET  /api/reports/trial-balance`
- `GET  /api/reports/pnl`
- `GET  /api/reports/dashboard`
- `GET  /api/transactions/journal-lines`
- `GET  /api/transactions/journal-entries`
- `POST /api/ai/chat`

---

### Step 5 — Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy env
cp .env.example .env

# Start dev server
npm run dev
```

Frontend runs at: `http://localhost:3000`

---

## AI Assistant

The AI assistant uses a **tool-based architecture** — it never invents financial numbers.

### Flow
```
User Question
  → LLM interprets intent
  → LLM calls finance tool (get_trial_balance, get_pnl, etc.)
  → Tool queries PostgreSQL
  → LLM explains result in natural language
  → Evidence panel shows raw data
```

### Without Azure OpenAI
If `AZURE_OPENAI_ENDPOINT` is not set, the system uses a **deterministic keyword-based fallback** that still routes queries to the correct finance tools.

### With Azure OpenAI
Set these in `local.settings.json`:
```json
"AZURE_OPENAI_ENDPOINT": "https://your-resource.openai.azure.com/",
"AZURE_OPENAI_API_KEY": "your-key",
"AZURE_OPENAI_DEPLOYMENT": "gpt-4o"
```

---

## Azure Deployment

See [`infra/README.md`](infra/README.md) for full deployment instructions.

Quick start:
```bash
# Deploy infrastructure
cd infra/bicep
az deployment group create \
  --resource-group finance-ai-rg \
  --template-file main.bicep \
  --parameters environmentName=dev dbAdminPassword=<SecurePass!>

# Deploy function app
cd backend
func azure functionapp publish <function-app-name>

# Build and deploy frontend to Azure Static Web Apps
cd frontend
npm run build
# Deploy dist/ to Azure Static Web Apps via portal or CLI
```

---

## GL Hierarchy Model

```
Company (ACME Corp)
  └── Entity (ACME United States)
        └── Ledger (Actual Ledger)
              └── Account Group (Assets / Revenue / Expenses...)
                    └── GL Account (Cash, Salary Expense...)

Dimensions:
  ├── Cost Center  (Operations, Sales, Admin)
  ├── Profit Center (Product Revenue, Services)
  ├── Project      (Project Alpha)
  ├── Region       (North America)
  ├── Vendor       (AWS, Corporate Travel)
  └── Customer     (BigCorp, TechCo)
```

---

## Sample Data

After running the seed script you will have:
- 1 Company, 1 Entity, 1 Ledger
- 5 Account Groups (Assets, Liabilities, Equity, Revenue, Expenses)
- 16 GL Accounts
- 18 Journal Entries across Jan-Mar 2026
- ~36 Journal Lines with full dimension tagging

---

## Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/dashboard` | KPI cards + revenue charts |
| GL Hierarchy | `/hierarchy` | Interactive account tree |
| Reports | `/reports` | Trial balance + P&L |
| Transactions | `/transactions` | Journal lines + entries with pagination |
| AI Chat | `/ai-chat` | Finance AI assistant with evidence |

---

## Project Structure — Key Files

```
backend/
├── function_app.py                     # All Azure Function HTTP routes
├── shared_code/
│   ├── config.py                       # Environment config
│   ├── database.py                     # SQLAlchemy session management
│   ├── models/
│   │   ├── hierarchy.py                # Company → GL Account models
│   │   └── transactions.py             # JournalEntry + JournalLine models
│   ├── services/
│   │   ├── finance_service.py          # Trial balance, P&L, dashboard logic
│   │   └── ai_agent_service.py         # Tool-based AI agent orchestration
│   ├── llm_provider/
│   │   ├── base.py                     # Abstract LLM interface
│   │   ├── azure_openai.py             # Azure OpenAI implementation
│   │   └── fallback.py                 # Deterministic fallback
│   └── prompt_templates/
│       └── finance_agent.py            # System prompt + prompt builders
```
