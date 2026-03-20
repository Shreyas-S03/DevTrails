# AI Parametric Insurance for Gig Workers (DevTrails) 🚀

Final hackathon prototype for a parametric insurance product tailored for the gig economy. Our platform provides automated loss-of-income coverage triggered by external disruptions such as extreme weather, severe pollution, and local strikes.

---

## 🌟 Key Features

- **Automated Claims Evaluation**: Powered by **LangGraph**, the system evaluates claims through a multi-stage logic pipeline (Parametric Check -> AI Fraud Detection -> ML Risk Scoring).
- **AI Fraud Detection (Agentic)**: Utilizes **LangChain** and **Ollama** (local LLM) to analyze rider telemetry (GPS spoofing, speed patterns) and flag fraudulent claims.
- **ML Risk Engine (HGBR)**: Features an ensemble of **Random Forest** and **Histogram-based Gradient Boosting Regression** models to predict event risk and calculate dynamic weekly premiums.
- **Premium Dashboard**: A stunning, high-performance **Next.js** dashboard with **Glassmorphism** aesthetics.
- **Real-time Simulator**: Built-in test environment to simulate weather disruptions and telemetry events (like GPS spoofing).
- **Persistent Storage**: Integrated with **Supabase (PostgreSQL)** for rider profiles, policy management, and claim history.

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **AI/ML Logic**: LangGraph, LangChain, Scikit-learn
- **LLM Context**: Ollama / OpenAI
- **Task Orchestration**: Custom StateMachine built with LangGraph

### Frontend
- **Framework**: Next.js 15 (App Router)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Design System**: Custom Premium Dark Mode (Glassmorphism)

### Database & Auth
- **Provider**: Supabase (PostgreSQL)
- **Persistence**: LocalStorage (Browser-side) for simulation state caching

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Supabase Account
- Ollama (for local LLM fraud detection)

### Install Dependencies

#### 1. Backend
```bash
cd backend
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Frontend
```bash
cd frontend
npm install
```

---

## ⚙️ Configuration

Create a `.env` file in the root directory:

```env
SUPABASE_URL="https://your-project-id.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="your-secret-service-role-key"
```

---

## 🏃‍♂️ Running the Project

### Terminal 1: Python Backend
```bash
cd backend
# Ensure venv is active
uvicorn orchestrator.main:app --reload
```
 Backend API active at: `http://localhost:8000`

### Terminal 2: Next.js Frontend
```bash
cd frontend
npm run dev
```
 Dashboard active at: `http://localhost:3000`

---

## 📂 Project Structure

- `backend/`: FastAPI backend, LangGraph orchestrator, and ML Risk Engine.
  - `orchestrator/`: The core claim processing logic (nodes, graph, schemas).
  - `ml/`: Scikit-learn models and risk evaluation logic.
- `frontend/`: Next.js dashboard and simulator.
- `supabase/`: SQL schemas for table initialization.
- `AGENTS.md`: Technical documentation for AI handoff and continuity.

---

## 📝 Usage for Hackathon Demo

1. **Setup Database**: Execute `supabase/schema_hackathon.sql` in your Supabase SQL Editor.
2. **Setup Test Rider**: Use the `INSERT` snippet found in `AGENTS.md` to add `RIDER_8023`.
3. **Trigger Claims**: Use the sidebar buttons in the Dashboard to test live approval, parametric denial, and AI-detected fraud.
4. **ML Quote**: Click "Refresh Premium Quote" on the dashboard to see the HGBR model calculate a dynamic rate live.

---

## ⚖️ License
This project is built for hackathon purposes. All rights reserved by the DevTrails team.
