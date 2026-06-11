# InsightForge 💰

> AI-powered personal finance analyzer. Upload your bank statement, get intelligent spending insights.

**Live Demo:** https://endearing-commitment-production-44a6.up.railway.app

---

## What It Does

InsightForge lets users upload their monthly bank statement (CSV) and receive:

- **Categorized transactions** — every transaction classified by an LLM into Food, Transport, Shopping, Entertainment, Utilities, Healthcare, Income, or Other
- **Plain-English spending report** — a narrative analysis of your month: income vs expenses, top spending categories, biggest single expense, and actionable tips
- **History** — all past statements saved to your account so you can track how your spending changes month over month

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (async) |
| Database | PostgreSQL + SQLAlchemy 2.0 |
| Migrations | Alembic |
| Authentication | JWT (python-jose + bcrypt) |
| LLM | LangChain + Groq (Llama 3.3-70b) |
| Frontend | Streamlit |
| Containerization | Docker + Docker Compose |
| Deployment | Railway |

---

## Architecture

```
Streamlit Frontend
        ↓ HTTP
FastAPI Backend (Railway)
        ↓
┌───────────────────────────────────┐
│  Router → Service → Repository   │
│  (layered clean architecture)    │
└───────────────────────────────────┘
        ↓
PostgreSQL (Railway managed)
        ↓
Groq API (LLM categorization + report)
```

### Backend Layer Structure

```
app/
├── api/v1/router.py          ← HTTP layer (routes only)
├── services/
│   ├── statement_service.py  ← business logic + pipeline
│   ├── parser_service.py     ← CSV parsing
│   └── llm_service.py        ← LangChain + Groq integration
├── repositories/
│   ├── user_repo.py          ← user DB queries
│   └── statement_repo.py     ← statement/transaction/report queries
├── models/                   ← SQLAlchemy ORM models
├── schemas/                  ← Pydantic validation schemas
└── core/
    ├── config.py             ← environment config
    ├── database.py           ← async engine + session
    ├── security.py           ← JWT + bcrypt
    ├── dependencies.py       ← auth dependency
    ├── exceptions.py         ← global error handlers
    └── logging.py            ← structured logging
```

---

## API Endpoints

```
POST   /api/v1/auth/register          Register a new user
POST   /api/v1/auth/login             Login, receive JWT token
GET    /api/v1/users/me               Get current user profile

POST   /api/v1/statements/upload      Upload CSV, triggers full analysis
GET    /api/v1/statements             List all past statements
GET    /api/v1/statements/{id}        Get statement + transactions + report
```

---

## The Processing Pipeline

```
Upload CSV
    ↓
Parse transactions (handles multiple bank formats)
    ↓
Save Statement + Transactions to DB
    ↓
LLM categorizes all transactions in one batched API call
    ↓
Update transaction categories in DB
    ↓
LLM generates plain-English spending report
    ↓
Save Report to DB
    ↓
Return statement ID → user fetches full detail
```

---

## Running Locally

**Prerequisites:** Docker Desktop

```bash
# Clone the repo
git clone https://github.com/lakshya0010/insightforge.git
cd insightforge

# Set up environment variables
cp .env.example .env
# Fill in SECRET_KEY and GROQ_API_KEY in .env

# Start everything
docker compose up --build
```

App runs at `http://localhost:8000` (API) and `http://localhost:8501` (UI)

**Environment variables needed:**
```
SECRET_KEY=your-secret-key
GROQ_API_KEY=your-groq-api-key
```

Get a free Groq API key at https://console.groq.com

---

## CSV Format

InsightForge accepts standard bank statement CSVs. Required columns (flexible naming):

| Column | Accepted Names |
|---|---|
| Date | Date, Transaction Date, Txn Date |
| Description | Description, Narration, Particulars |
| Debit | Debit, Withdrawal, DR |
| Credit | Credit, Deposit, CR |

Example:
```
Date,Description,Debit,Credit,Balance
01/04/2026,ZOMATO ORDER,450.00,,15550.00
03/04/2026,SALARY CREDIT,,50000.00,65550.00
05/04/2026,UBER RIDE,230.00,,65320.00
```

---

## Design Decisions

**Why async SQLAlchemy?** FastAPI is async-first. Using a sync DB driver blocks the event loop and destroys concurrency. Every DB call is non-blocking.

**Why the Repository pattern?** Separates SQL from business logic. Services are testable without a real database — swap the real repo for a fake one in tests.

**Why LangChain over direct SDK?** Provider-agnostic. Switching from Groq to Anthropic or OpenAI requires changing one import and one model name — nothing else.

**Why batched LLM calls for categorization?** One API call for all transactions instead of N calls. Faster, cheaper, fewer rate limit issues.

---

## Roadmap (v2)

- [ ] PDF bank statement support (pdfplumber)
- [ ] Excel (.xlsx) support
- [ ] Spending goals with progress tracking
- [ ] Month-over-month comparison charts
- [ ] Email report delivery

---

## Author

**Lakshya Sharma** — B.Tech Mathematics & Computing, DTU (2024–2028)

[LinkedIn](https://www.linkedin.com/in/lakshya-sharma-551583312/) · [GitHub](https://github.com/lakshya0010)