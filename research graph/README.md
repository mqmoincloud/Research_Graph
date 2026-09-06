# Research Graph

Job description daalo, LangGraph teen research lanes parallel chalata hai, aur
ek interview preparation document banata hai.

## Setup

```bash
uv sync
```

Secrets `.env` mein rakho (project ke andar ya bahar, dono chalega):

```
NVIDIA_API_KEY=nvapi-...
GITHUB_TOKEN=github_pat_...      # optional, na ho to 60 request/ghanta
```

## Chalao

**Backend:**

```bash
uv run uvicorn app.main:app --reload --reload-dir app --port 8000
```

`--reload-dir app` chhodna mat. Uske bina uvicorn poore folder ko watch karta
hai - `.venv/` aur `frontend/node_modules/` samet. Vite dev server
`node_modules/.vite/` mein lagataar likhta rehta hai, uvicorn usko "code badla"
samajh kar restart kar deta hai, aur chalta hua run memory se gayab ho jaata
hai -> `GET /api/runs/{id}` par 404.

**Frontend:**

```bash
cd frontend
npm run dev
```

Frontend `http://localhost:5200` par khulta hai (5173 par nahi - `vite.config.js`
mein `strictPort: 5200` hai).

`frontend/.env` badalne ke baad Vite ko RESTART karna padta hai - `.env` sirf
start hote waqt padhi jaati hai, hot-reload usse nahi uthata.

**Sirf graph, bina API ke:**

```bash
uv run python scripts/run_cli.py
```

**Graph ki tasveer (mermaid):**

```bash
uv run python scripts/draw_graph.py
```

## Files

| File | Kaam |
|---|---|
| `app/state.py` | Graph ki state. `evidence` par reducer hai - lanes ek saath likhti hain |
| `app/graph.py` | Nodes ko jodna, `choose_lanes` aur `decide_next_step` router |
| `app/nodes/orchestrator.py` | JD padhta hai, LLM ke **tool calls** se lanes chunta hai |
| `app/nodes/research.py` | Teen lanes - tech (GitHub), soft aur general (web) |
| `app/nodes/review.py` | Kis lane mein kami hai, ye batata hai |
| `app/nodes/compose.py` | Aakhri markdown document |
| `app/llm.py` | LLM se baat karne ki ek jagah - `ask_with_tools` / `ask_json` / `ask_text` |
| `app/tool_specs.py` | Tools ki definitions, jo LLM ko bheji jaati hain |
| `app/tools.py` | GitHub aur web search |
| `app/pdf.py` | PDF se text |
| `app/config.py` | Secrets aur constants (`MAX_ROUNDS`, lane names) |
| `app/logs.py` | Terminal logs |
| `app/main.py` | FastAPI |
| `scripts/run_cli.py` | Graph ko seedha terminal se chalane ke liye |
| `scripts/draw_graph.py` | Graph ka mermaid diagram |

## Graph

```
START -> orchestrator -> tech_research    -+
                      -> soft_research     +-> review -> compose -> END
                      -> general_research -+      |
                                                  +-> wapas un lanes par
                                                      jinme kami hai
                                                      (max 1 retry)
```

## Scan kiye hue PDF

Support nahi hai. `pypdf` sirf text layer padhta hai, image se text nahi
nikaal sakta - toh scan kiya hua PDF upload par `400` ke saath ruk jaata
hai. Text wala PDF ya `.txt` use karo.
