# Research Graph

Feed in a job description, LangGraph runs three research lanes in parallel, and
builds an interview preparation document.

## Setup

```bash
uv sync
```

Keep secrets in `.env` (inside the project or outside, both work):

```
NVIDIA_API_KEY=nvapi-...
GITHUB_TOKEN=github_pat_...      # optional, without it 60 requests/hour
```

## Run

**Backend:**

```bash
uv run uvicorn app.main:app --reload --reload-dir app --port 8000
```

Do not drop `--reload-dir app`. Without it uvicorn watches the whole folder -
including `.venv/` and `frontend/node_modules/`. The Vite dev server keeps
writing into `node_modules/.vite/`, uvicorn reads that as "the code changed"
and restarts, and a run in progress disappears from memory
-> `404` on `GET /api/runs/{id}`.

**Frontend:**

```bash
cd frontend
npm run dev
```

The frontend opens at `http://localhost:5200` (not 5173 - `vite.config.js`
has `strictPort: 5200`).

After changing `frontend/.env` you have to RESTART Vite - `.env` is only read
at startup, hot-reload does not pick it up.

**Only the graph, without the API:**

```bash
uv run python scripts/run_cli.py
```

**Picture of the graph (mermaid):**

```bash
uv run python scripts/draw_graph.py
```

## Files

| File | Job |
|---|---|
| `app/state.py` | The graph state. `evidence` has a reducer - lanes write at the same time |
| `app/graph.py` | Wiring the nodes together, `choose_lanes` and `decide_next_step` routers |
| `app/nodes/orchestrator.py` | Reads the JD, picks lanes from the LLM's **tool calls** |
| `app/nodes/research.py` | Three lanes - tech (GitHub), soft and general (web) |
| `app/nodes/review.py` | Says which lane is still missing something |
| `app/nodes/compose.py` | The final markdown document |
| `app/llm.py` | One place to talk to the LLM - `ask_with_tools` / `ask_json` / `ask_text` |
| `app/tool_specs.py` | The tool definitions that get sent to the LLM |
| `app/tools.py` | GitHub and web search |
| `app/pdf.py` | Text out of a PDF |
| `app/config.py` | Secrets and constants (`MAX_ROUNDS`, lane names) |
| `app/logs.py` | Terminal logs |
| `app/main.py` | FastAPI |
| `scripts/run_cli.py` | For running the graph straight from the terminal |
| `scripts/draw_graph.py` | Mermaid diagram of the graph |

## Graph

```
START -> orchestrator -> tech_research    -+
                      -> soft_research     +-> review -> compose -> END
                      -> general_research -+      |
                                                  +-> back to the lanes
                                                      that are missing things
                                                      (max 1 retry)
```

## Scanned PDFs

Not supported. `pypdf` only reads the text layer, it cannot pull text out of
an image - so a scanned PDF stops at upload with a `400`. Use a PDF with
text, or a `.txt`.
