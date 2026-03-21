# Hackathon Submission: DevTrails (Parametric Insurance for Gig Workers)

## Inspiration
The gig economy is the backbone of modern cities, but gig workers (delivery partners, ride-hailing drivers) are also the most vulnerable to things they can't control. A sudden monsoon, a severe pollution surge, or a local strike can wipe out a whole week's earnings for a family. Traditional insurance is too slow, too expensive, and often doesn't cover "loss of income" without an accident. We were inspired to build DevTrails—a parametric insurance platform that pays out automatically based on verifiable environmental data, ensuring no gig worker is left stranded by a rainy day.

## What it does
DevTrails is an AI-driven parametric insurance prototype that provides automated income protection. 
- **Parametric Triggers**: Using real-time weather and pollution APIs (simulated in our demo), it automatically evaluates claims when specific thresholds (e.g., >40mm rain) are met.
- **Agentic Fraud Detection**: It uses a LangChain-powered AI agent to analyze rider telemetry. If a rider claims they were "online" but their GPS shows they were spoofing their location or moving at impossible speeds for the weather, the AI flags it instantly.
- **Dynamic HGBR Pricing**: Our ML engine (Histogram-based Gradient Boosting Regression) calculates risk-adjusted weekly premiums in real-time, offering a fair price based on historical and local risk factors.
- **Instant Payouts**: Once a claim is "Approved" by the AI pipeline, the payout is calculated and delivered instantly to the rider's digital wallet.

## How we built it
We built a full-stack AI-first application:
- Backend Architecture: Built with FastAPI and LangGraph. We used a directed acyclic graph (DAG) to orchestrate the claim evaluation pipeline, integrating database lookups, parametric rules, and AI nodes.
- AI/ML Layer: 
    - LangChain + Ollama: Used for agentic fraud analysis of telemetry data.
    - Scikit-Learn: Implemented an ensemble of Random Forest and HGBR models for our Risk & Pricing Engine.
- Frontend Experience: A premium Next.js dashboard featuring a "Glassmorphism" design system, dark mode, and smooth micro-animations.
- Database: Supabase (PostgreSQL) handles the rider profiles and persistent claim history.
- Simulation Suite: A built-in disruption simulator allowed us to dry-run the parametric logic against various edge cases.

## Challenges we ran into
- State Management in LangGraph: Orchestrating a multi-node pipeline where each node needs to modify a shared ClaimState was a steep learning curve, but it ultimately made our backend incredibly modular and auditable.
- Model Tuning: Building a synthetic dataset for the HGBR model that accurately reflected "loss of income" risk was challenging. We had to iterate on feature engineering to ensure the premiums were realistic.
- State Persistence: Balancing the need for a "fast-loading" dashboard for the demo while keeping it synced with a real Postgres DB led us to implement a hybrid LocalStorage/Supabase approach.

## Accomplishments that we're proud of
- End-to-End Integration: We successfully connected a machine-learning regression model directly to a sleek React UI via an AI-orchestrated backend.
- The "Glassmorphism" Design: The UI feels premium, like a high-end fintech product, which elevates the user trust—a critical factor for insurance.
- Agentic Logic: Successfully moving from simple "if-else" fraud checks to a generative AI agent that "reasons" about telemetry data is a huge step forward for automated insurance.

## What we learned
We dove deep into the world of Parametric Insurance—a shift from "indemnity" (paying for damages) to "index-based" (paying for events). We also learned how to build production-grade AI workflows using LangGraph and how to resolve complex React hydration issues in modern Next.js 15 apps.

## What's next for DevTrails
- Real-time API Integration: Connecting to the OpenWeatherMap and Google Maps APIs for live, non-simulated triggers.
- Blockchain Payouts: Moving the final "Payout" node to a smart contract to make the insurance "trustless" and even more transparent.
- Multi-Zone Scaling: Training our ML risk models on specific city-level micro-zones to offer hyper-local premiums (e.g., Indiranagar vs. Whitefield).
