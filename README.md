# CAT Operator Intelligence

**Closed-Loop Operator Intelligence for CAT Machinery** — a local-first, closed-loop AI
decision-support platform that fuses machine, operator, task, safety and environmental data to
identify abnormal operational behavior, estimate task outcomes, detect emerging risk, recommend the
operator's next best action, personalize training, and measure intervention outcomes.

Built for the Caterpillar / CAT Digital campus hiring hackathon (24-hour, ₹0 budget, no physical
hardware, local-first laptop execution).

> Core principle: **Observe → Understand → Predict → Prioritize → Recommend → Act → Measure → Learn**

Full product/technical specification: [CAT_Operator_Intelligence_Coding_Context.md](CAT_Operator_Intelligence_Coding_Context.md)

## Status

This project is being built phase-by-phase. See commit history for progress; each phase is tested
before merging to `main`.

## Tech Stack

- **Frontend:** React + Vite + TypeScript, Tailwind CSS, Recharts, lucide-react
- **Backend:** Python, FastAPI, Uvicorn, Pydantic, WebSockets
- **Database:** SQLite
- **Data/ML:** Pandas, NumPy, scikit-learn, Joblib
- **GenAI (optional):** Ollama + small local quantized model, with a deterministic template fallback

## Architecture

```
Machine / Simulator → Data Adapter → Context Engine → Safety/Machine/Productivity AI
    → Risk Engine → Next Best Action → Generative Explanation → Operator UI
    → Operator Action → Outcome Metrics → Feedback → Learning
```

The system is a **decision-support layer**, not a machine-control system: it never directly controls
excavator movement, hydraulics, engine, or brakes. It provides alerts, context, predictions,
recommendations and training — the human operator remains in control.

## Repository Layout

```
backend/    FastAPI app, ML models, agents, context/NBA engines, telemetry simulator, dataset generator
frontend/   React + Vite + TypeScript app (5 screens: Dashboard, Live Operation, Safety Center,
            Training Hub, Shift Intelligence)
```

## Running Locally

See `backend/README.md` and `frontend/README.md` (added as those phases land) for setup instructions.
The whole system runs offline on a laptop — no cloud dependency, no GPU required.
