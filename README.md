# AI Job Hunting Assistant

An agentic web application that helps candidates align their resume and interview narrative with a specific job description (JD). It ingests a resume (PDF or pasted text), job metadata, and the target JD, then produces structured match analysis, resume bullet refinements, a consolidated final resume draft, and themed interview preparation.

---

## Table of contents

1. [Objective](#1-objective)  
2. [Target customers](#2-target-customers)  
3. [Key capabilities and use cases](#3-key-capabilities-and-use-cases)  
4. [How to use](#4-how-to-use)  
5. [Technical architecture — agentic system](#5-technical-architecture--agentic-system)  
6. [Installation and runtime](#6-installation-and-runtime)  
7. [API and operations](#7-api-and-operations)  
8. [Deployment](#8-deployment)  
9. [Configuration reference](#9-configuration-reference)  
10. [Privacy, security, and data](#10-privacy-security-and-data)  
11. [Troubleshooting](#11-troubleshooting)  
12. [Project structure](#12-project-structure)  
13. [License](#13-license)  
14. [Contributing](#14-contributing)

---

## 1. Objective

Reduce friction between a candidate’s resume and a concrete job posting by:

- **Diagnosing fit** against the JD (strengths, gaps, and role expectations).  
- **Improving resume bullets** with JD-aware suggestions and a guided accept / edit / reject workflow.  
- **Accelerating interview prep** with behavioral, project deep-dive, and business-domain themes grounded in the same JD and finalized resume context.

The product is optimized for **one job at a time**: each run is scoped to a single JD and produces a coherent set of artifacts for that application.

---

## 2. Target customers

| Segment | Typical need |
|--------|----------------|
| **Active job seekers** | Tailor resume and talking points quickly per application. |
| **Career switchers** | Map transferable skills to unfamiliar JD language and expectations. |
| **Students and early-career hires** | Turn internships and academic work into JD-aligned resume language. |
| **Experienced professionals** | Refresh narrative for a specific level (e.g. staff, lead, manager) or domain. |

The UI supports **English and Chinese** for interface copy and workflow messages; structured LLM outputs follow the user-selected language where the pipeline is configured to do so.

---

## 3. Key capabilities and use cases

### Core workflow

1. **Input** — Job title, company, region (optional), JD text, and resume (PDF upload or paste).  
2. **Validation** — Ensures minimum resume completeness before expensive LLM steps.  
3. **JD analysis & match** — Structured role understanding, fit framing, and dashboard views (e.g. scenarios, profile, match).  
4. **Resume optimization** — Bullet-level suggestions tied to the JD; user confirms choices to build a **final resume** draft.  
5. **Interview preparation** — After resume confirmation, generates themed prep: behavioral (including story frameworks), project deep-dive, and business-domain questions, plus a short preparation summary.

### Representative use cases

- **High-volume applications** — Re-run the workflow per JD; compare match tabs and carry forward only the final resume you accept.  
- **Final interview stage** — Use interview tabs to rehearse stories and domain questions aligned to the same JD and resume version.  
- **Bilingual teams** — Switch UI language on the input screen; dashboard language stays consistent for a given run once analysis has started.

---

## 4. How to use

### Development mode (recommended for contributors)

1. Start the **backend** (port `8000`).  
2. Start the **frontend dev server** (typically Vite on port `5173` or as configured).  
3. Open the app URL, choose **English** or **中文**, fill the form, and submit.  
4. On the **loading** screen, progress updates stream (with polling fallback if the live connection drops).  
5. On the **dashboard**, explore tabs: work scenarios, candidate / role profile, match analysis, resume optimization, then **confirm** resume modifications to trigger **final resume** generation and **interview prep**.

### Production-style single port

Build the frontend and serve it from the FastAPI app so a single process can expose the UI and API (see [Installation and runtime](#6-installation-and-runtime)).

For concise local commands, see **`START_SERVICES.md`** in this repository.

---

## 5. Technical architecture — agentic system

### Orchestration

- **API layer**: `workflow_api.py` (FastAPI) — workflow lifecycle, progress endpoints, resume and interview sub-routes, static / SPA hosting when `frontend/dist` exists.  
- **Client**: React 18, TypeScript, Vite, Tailwind CSS, Zustand; health check and **SSE** progress with **automatic polling fallback** for resilience.

### Specialized agents (documented pipeline)

The core path is a **four-step sequential** workflow on the server, plus **interview generation** after the user finalizes resume edits.

| Agent | Responsibility |
|-------|------------------|
| **Agent 1** | **Input validation** — Blocks incomplete resumes before downstream cost. |
| **Agent 2** | **JD analysis & match** — Structured understanding of the role, fit, and candidate-facing insights (configurable fast path for latency). |
| **Agent 4** | **Resume optimization** — JD- and analysis-grounded bullet suggestions and structured resume output for the UI and export flow. |
| **Agent 5** | **Interview preparation** — Runs **asynchronously** after the user finalizes resume choices; consumes JD plus prior analysis and resume-optimization context for themed prep. |

Prompts and compressed prompt modules live in `agent_prompts.py` and `*_prompt_compressed.py` where used. The stack calls an **OpenAI-compatible chat completions** endpoint (see configuration) with JSON-mode style responses where enabled.

### Data flow (conceptual)

```text
User inputs → Agent 1 → Agent 2 → Agent 4 → Dashboard
                                            ↓
                          User confirms bullets → Final resume
                                            ↓
                                    Agent 5 (async) → Interview tab
```

---

## 6. Installation and runtime

### Prerequisites

- **Python** 3.10+ recommended (3.8+ may work depending on dependencies).  
- **Node.js** 18+ and npm (for frontend development and builds).  
- A valid **API key** for the configured LLM gateway (see below).

### Clone

```bash
git clone https://github.com/MikeFan1433/ai-job-hunting-assistant.git
cd ai-job-hunting-assistant
```

### Backend

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a **`.env`** file in the project root (never commit it). Minimum:

```env
AI_BUILDER_TOKEN=your-api-key-here
```

Optional base URL (default shown):

```env
AI_BUILDER_BASE_URL=https://space.ai-builders.com/backend
```

Start the API:

```bash
python3 -m uvicorn workflow_api:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (development)

```bash
cd frontend
npm install
npm run dev
```

Point the frontend at the backend URL if required by your `frontend` environment (often `http://localhost:8000` for API calls).

### Production build (UI served by FastAPI)

```bash
./build.sh
python3 -m uvicorn workflow_api:app --host 0.0.0.0 --port 8000
```

Then open `http://localhost:8000`.

---

## 7. API and operations

| Resource | Description |
|----------|-------------|
| **OpenAPI / Swagger** | `http://localhost:8000/docs` |
| **Health** | `GET /api/v1/health` |

Use these to verify the server before running through the UI.

---

## 8. Deployment

- **Docker**: `Dockerfile` and `docker-compose.yml` are provided for containerized runs.  
- **Shell helpers**: `deploy.sh`, `update_and_deploy.sh`, and `build.sh` support common packaging flows.

Tune model names and timeouts via environment variables (see [Configuration reference](#9-configuration-reference)) to match your provider’s latency and quotas.

---

## 9. Configuration reference

Primary variables are read in `config.py`. Commonly adjusted:

| Variable | Purpose |
|----------|---------|
| `AI_BUILDER_TOKEN` | Primary API key (aliases such as `STUDENT_PORTAL_API_KEY` are also supported). |
| `AI_BUILDER_BASE_URL` | OpenAI-compatible gateway base URL. |
| `LLM_MODEL_JSON` / `LLM_MODEL` | Default chat model for structured agents. |
| `AGENT2_FAST_MODE` | Faster JD analysis path when set to `1` (default in repo). |
| `AGENT2_FAST_MODEL`, `AGENT4_FAST_MODEL`, `AGENT5_FAST_MODEL` | Per-agent fast models where applicable. |
| `AGENT5_DISABLED` | Set to `1` to skip interview generation features. |
| `AGENT5_SKIP_IN_WORKFLOW` | Default `1`: skip Agent 5 during initial workflow; runs once after user confirms resume via Interview Prep. |
| `DISABLE_JSON_MODE` | Set to `1` if the provider does not support `response_format` JSON mode. |

See inline comments in `config.py` for the full list and provider notes.

---

## 10. Privacy, security, and data

- **Secrets**: Keep `.env` out of version control; rotate keys if exposed.  
- **Resume and JD content** are processed by the configured LLM provider according to that provider’s policies.  
- **Local artifacts**: Uploaded and generated files may be written under `data/` (see `.gitignore` for ignored patterns). Operate on machines and accounts you trust.

---

## 11. Troubleshooting

| Symptom | Things to check |
|--------|-------------------|
| Stuck on loading | Confirm backend on port **8000**; open **Network** tab; `GET /api/v1/health` should return healthy JSON. |
| SSE disconnects | The client falls back to **polling**; persistent failure usually means the API process stopped or CORS / URL mismatch. |
| Validation errors | Agent 1 requires substantive resume sections (e.g. experience, education); expand pasted text or use a fuller PDF. |
| Timeouts / empty JSON from models | Try fast models via env vars in `config.py`; increase timeouts only if your provider allows. |

---

## 12. Project structure

```text
.
├── workflow_api.py          # FastAPI app and routes
├── agent1.py, agent2.py, agent4.py, agent5.py   # documented pipeline steps
├── agent_prompts.py, *\_prompt_compressed.py   # prompts (as used by agents)
├── config.py                # Environment and model configuration
├── resume_optimization_service.py, resume_export.py
├── frontend/                # React + Vite SPA
├── static/                  # Legacy static assets if used
├── data/                    # Local runtime data (partially gitignored)
├── build.sh, deploy.sh, Dockerfile, docker-compose.yml
├── requirements.txt
├── START_SERVICES.md        # Quick local command reference
└── README.md
```

---

## 13. License

MIT License — see the repository license file if present, or include a `LICENSE` file for distribution.

---

## 14. Contributing

Issues and pull requests are welcome. When changing agent contracts or JSON schemas, update both **backend parsers** and **frontend types** so the dashboard stays in sync.

**Repository:** [github.com/MikeFan1433/ai-job-hunting-assistant](https://github.com/MikeFan1433/ai-job-hunting-assistant)
