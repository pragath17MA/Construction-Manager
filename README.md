# AI Construction Project Manager Platform (APEXBuild)

APEXBuild is an AI-powered construction management enterprise application that automates cost estimation, budgeting, project tracking, and workflow scheduling using multi-agent intelligence.

---

## 🚀 Tech Stack

- **Frontend:** React, React Router 6, Tailwind CSS, Chart.js, Axios, Lucide Icons
- **Backend:** FastAPI (Python 3.10+), SQLAlchemy ORM, SQLite/PostgreSQL, LangGraph, LangChain, ReportLab PDF Library
- **AI/LLM:** Groq API (Llama-3-70b-8192)

---

## 🛠️ Module Features

### Module 1: Authentication & Authorization
- Secure JWT-based User Registrations & Session log-ins.
- Role-based Access Control (RBAC) boundaries separating:
  - **Admin:** Full organization management privileges.
  - **Project Manager (PM):** Managed scopes over assigned project items.
  - **Site Engineer:** Read-only access to assigned projects, and progress reporting.
- Fail-safe secure token reset handler.

### Module 2: Project Management
- Project scoping (timelines, descriptions, locations).
- Dynamic member team rosters (assignments, deletions).
- Upload whitelisting for construction blueprints (PDF drawings) and progress logs (Site Images).

### Module 3: AI Cost Estimation Agent
- **Workflow Orchestration (LangGraph):** Orchestrates multi-node estimations (Validate Input $\rightarrow$ Estimate Materials $\rightarrow$ Estimate Labor $\rightarrow$ Estimate Equipment $\rightarrow$ Compute Indirects $\rightarrow$ Compute Contingency $\rightarrow$ AI Budget Optimization $\rightarrow$ Finalize Report).
- **LLM Optimizer (Groq):** Uses Groq models to analyze item lists, suggest materials grade substitutions, optimize durations, and predict cost savings in real-time.
- **Report Compiler (ReportLab):** Generates downloadable corporate budget estimate sheets as securely-streamed PDF documents.

---

## 📊 Cost Estimation Formulas

The agent enforces the following mathematical models:
1. **Total Material Cost:** $\sum (\text{Material Quantity} \times \text{Unit Price})$
2. **Labor Cost:** $\text{Worker Count} \times \text{Daily Wage Rate} \times \text{Days Duration}$
3. **Equipment Cost:** $\text{Daily Machinery Rate} \times \text{Days Rental Duration}$
4. **Indirect Cost:** $10\%$ of $(\text{Material Cost} + \text{Labor Cost} + \text{Equipment Cost})$
5. **Contingency Buffer:** $5\%$ of $(\text{Material Cost} + \text{Labor Cost} + \text{Equipment Cost} + \text{Indirect Cost})$
6. **Final Estimated Budget:** $\text{Material} + \text{Labor} + \text{Equipment} + \text{Indirect} + \text{Contingency}$

---

## ⚙️ Configuration & Groq Setup

1. Copy the environment variables to the backend local instance in `backend/app/core/config.py` or `.env` file:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   OPENWEATHER_API_KEY=your_openweather_api_key_here
   ```
2. If `GROQ_API_KEY` or `OPENWEATHER_API_KEY` are not present, the backend falls back to a sandbox evaluation mode that simulates AI analysis and returns safe defaults.

---

---

## 🛰️ Modules 6–11 API Endpoints

### AI Risk Prediction Center
- `POST /api/risk/analyze` - Triggers multi-factor risk assessment (Admin/PM).
- `GET /api/risk/project/{project_id}` - Gets active risk score and forecasts (All).
- `GET /api/risk/history/{project_id}` - Gets chronological history audits (All).
- `GET /api/reports/risk/{project_id}?format=pdf` - Streams PDF Risk Report (All).

### Progress Monitoring Center
- `POST /api/progress/update` - Site engineers log progress with optional file attachment uploads (All).
- `GET /api/progress/project/{project_id}` - Compiles timeline milestone completion ratios and logs summaries (All).
- `POST /api/milestone` - Creates or updates milestone plans and status flags (Admin/PM).
- `GET /api/milestones/{project_id}` - Lists project milestones (All).
- `GET /api/reports/progress/{project_id}?format=pdf` - Streams PDF Progress Report (All).

### AI Drawing Intelligence (RAG)
- `POST /api/documents/upload` - Uploads drawing specifications PDF and triggers background indexing (Admin/PM).
- `POST /api/documents/query` - Queries drawing library using semantic vector matches and llama-3 Q&A (All).
- `GET /api/documents/{id}` - Retrieves details and chunked text segments (All).
- `GET /api/documents/project/{project_id}` - Lists all drawing files in project (All).

### AI Invoice OCR & Audit
- `POST /api/invoice/upload` - Uploads invoice PDF/Image and schedules background OCR parsing (Admin/PM).
- `GET /api/invoice/{id}` - Fetches invoice line items and budget variance comparisons (All).
- `POST /api/invoice/analyze` - Triggers AI fraud checkers, duplicate validations, and budget variance audits (Admin/PM).
- `GET /api/invoice/report/{id}` - Downloads PDF/CSV compliance audit report sheets (All).

### AI Site Image Visual Audit (Module 10)
- `POST /api/image-analysis/analyze` - Triggers image safety gear and construction stage audit (PM/Site Engineer).
- `GET /api/image-analysis/project/{project_id}` - Retrieves list of visual audits for a project (All).
- `GET /api/image-analysis/image/{site_image_id}` - Fetches specific image analysis results (All).
- `GET /api/image-analysis/annotated-image/{analysis_id}` - Securely downloads the annotated image markup file (All).

### AI Voice Command Cockpit (Module 11)
- `POST /api/voice/command` - Accepts text query or uploaded audio clip, executing data audits (All).
- `GET /api/voice/history/{project_id}` - Lists conversational query logs for a project (All).
- `GET /api/voice/audio/{filename}` - Securely plays back response synthesized speech (All).

---

## 💻 Local Development Setup

### Backend (FastAPI)
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and source virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start FastAPI server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### Frontend (React)
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install packages:
   ```bash
   npm install
   ```
3. Boot the development dev-server:
   ```bash
   npm run dev
   ```

---

## 🧪 Running Unit Tests

Backend test suites cover registration flows, projects access boundaries, and AI budget calculations:
```bash
cd backend
venv\Scripts\pytest
```
