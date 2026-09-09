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

ORIGIN=http://localhost:5200     # for the CORS allow-list
SECRET_KEY=...                   # signs the JWTs, any long random string
DB_URL=sqlite:///./prepgraph.db
ALGORITHM=HS256
TOKEN_MINUTES=30                 # optional, defaults to 30
```

`.env.example` has the full list with comments. The four auth keys are
required: `app/config.py` refuses to start without them, so a typo shows up
immediately instead of as a confusing 500 on the first login. Generate a
secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Run

**Backend** - migrate, seed if the database is empty, then serve:

```bash
uv run python run.py
```

That is the same as doing it by hand:

```bash
uv run alembic upgrade head
uv run python -m scripts.seed
uv run uvicorn app.main:app --reload --reload-dir app --port 8000
```

Do not drop `--reload-dir app`. Without it uvicorn watches the whole folder -
including `.venv/` and `frontend/node_modules/`. The Vite dev server keeps
writing into `node_modules/.vite/`, uvicorn reads that as "the code changed"
and restarts. `POST /api/run` runs the whole graph inside the one request, so
a restart in the middle kills the request that is in flight - the browser just
sees the connection drop, and the minutes of research are gone.

**Frontend:**

```bash
cd frontend
npm run dev
```

The frontend opens at `http://localhost:5200` (not 5173 - `vite.config.js`
has `strictPort: 5200`). It lands on `/login`; `/signup` makes an account,
`/` is the graph page, `/profile` is your own settings, and `/users` is the
admin screen.

`vite.config.js` forwards `/api`, `/auth`, `/me`, `/admin` and `/users` to
FastAPI. A backend path missing from that list is served by Vite as the React
app instead, which arrives as HTML where JSON was expected.

After changing `frontend/.env` you have to RESTART Vite - `.env` is only read
at startup, hot-reload does not pick it up.

## Accounts

`POST /api/run` is behind a login - a graph run costs minutes of LLM and
search calls, so it is not left open.

Anyone can sign up, but signup always creates a plain `"user"`; the role is
hardcoded in the route and `UserSignup` has no role field, so nobody can make
themselves an admin by adding a line to the request body. The first admin
therefore cannot come from the API - `scripts/seed.py` writes it:

| Email | Role | Password |
|---|---|---|
| `admin@prepgraph.example.com` | admin | `password123` |
| `qaisar@prepgraph.example.com` | user | `password123` |

Demo passwords. Change them from the Profile page before anyone else can
reach the app.

**Routes**

| Route | Who |
|---|---|
| `POST /auth/signup` | anyone - always creates a `"user"` |
| `POST /auth/login` | anyone -> `{access_token, token_type}` |
| `GET /me`, `PATCH /me`, `POST /me/password` | any logged-in user |
| `GET /admin/users` | admin |
| `PATCH /users/{id}` | admin - name, email, password, role |
| `DELETE /users/{id}` | admin - soft delete, the row stays |
| `POST /api/run` | any logged-in user |
| `GET /api/demo`, `GET /api/demo/{name}` | any logged-in user - the saved sample runs |

**How the check works.** Three dependencies, each one built on the one above
it, so a route only asks for the level it needs:

```
verify_token       is this a real, unexpired JWT?
get_current_user   does it still point at a live user?   (hits the database)
require_admin      and is that user an admin?
```

`get_current_user` looks the row up on every request instead of trusting the
token's contents. A signed token keeps working until it expires, so without
that lookup a deleted user would keep getting in for the rest of the 30
minutes.

`token_version` is the same idea for passwords. The number is baked into the
token and bumped on every password change, so changing your password kills
every token issued before it - including the one on the laptop you left
logged in.

Two things an admin cannot do: demote themselves or delete themselves. That
also quietly protects the last admin - with only one left, nobody else can
reach those routes at all.

## Sample runs

Nothing stores a run. `POST /api/run` hands the result back and the browser
keeps it in memory until the page reloads - so showing the app to somebody
meant sitting through a real 1-3 minute run, with the LLM having to behave on
the day.

`demo_runs/` holds runs that were already done, one JSON per JD in
`demo_jds/`. Produce them with:

```bash
uv run python -m scripts.save_demo_run              # every JD in demo_jds/
uv run python -m scripts.save_demo_run jd_backend   # just that one
```

Those files are real graph output, not written by hand - the only difference
is when they were produced. Re-run the script after changing a JD or a node,
otherwise the demo keeps showing the old answer.

The graph page then offers them as buttons under the upload box, and
`GET /api/demo/{name}` returns the same shape `POST /api/run` does, so the
same `ResultPanel` draws both. It adds `is_demo: true`, which is what puts the
"sample run" badge on the panel - without it there is no way to tell a saved
document from one just produced.

`{name}` is checked against the files actually in `demo_runs/` before any path
is built from it. Joining the URL value onto the folder directly would make
`../../.env` a legal name, and a real file.

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
| `app/graph.py` | The state (`PrepState` - `evidence` has a reducer, lanes write at the same time), the node wiring, and the `choose_lanes` / `decide_next_step` routers |
| `app/nodes/orchestrator.py` | Reads the JD, picks lanes from the LLM's **tool calls**. The tool definitions (`@tool`) sent to the LLM live here too |
| `app/nodes/research.py` | Three lanes - tech (GitHub), soft and general (web). The GitHub and web search calls themselves are in here |
| `app/nodes/review.py` | Says which lane is still missing something |
| `app/nodes/compose.py` | The final markdown document |
| `app/llm.py` | One place to talk to the LLM - `ask_with_tools` / `ask_json` / `ask_text` |
| `app/config.py` | Secrets, the constants (`MAX_ROUNDS`, lane names), the `log` helper, and the `Config` object holding the auth settings |
| `app/pdf.py` | Text out of the upload. Text layer first, OCR only if that is empty |
| `app/main.py` | FastAPI - `POST /api/run` (login required), the CORS setup and the three error handlers that put every failure in one shape |
| `app/database.py` | The engine, `localSession`, `Base`, and `get_db` - one session per request |
| `app/models/user.py` | The one table: `users` |
| `app/schemas/user.py` | What the API accepts and returns. `UserSignup` having no `role` field is the reason signup cannot make an admin |
| `app/security.py` | Hashing, JWTs, and the `verify_token` -> `get_current_user` -> `require_admin` chain |
| `app/routers/auth.py` | Signup, login, your own profile, and the admin-only user routes |
| `migrations/` | Alembic. `env.py` takes the URL from `DB_URL`, so the migrations and the app can never point at different databases |
| `scripts/seed.py` | The starting accounts, including the admin that signup cannot create. Safe to run twice |
| `app/routers/demo.py` | Serves the saved runs in `demo_runs/` - the demo buttons on the graph page |
| `scripts/save_demo_run.py` | Runs the graph on a JD from `demo_jds/` once and saves the result |
| `demo_runs/` | Those saved results, one JSON per JD. Committed, so a fresh clone can demo straight away |
| `scripts/run_cli.py` | For running the graph straight from the terminal |
| `scripts/draw_graph.py` | Mermaid diagram of the graph |
| `run.py` | Migrate, seed if empty, serve - the one command to start the backend |

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

`pypdf` only reads a PDF's text layer. A scanned page is a picture, so there
is no such layer and pypdf comes back with nothing. `app/pdf.py` falls back to
OCR when that happens: pypdfium2 renders each page to an image, and Tesseract
reads the image.

OCR runs ONLY when the text layer looks too thin - under 100 characters per
page. It costs a few seconds a page and nearly every JD is a normal PDF, so
charging every upload for it would be waste.

Per page, not a flat total. A scan pasted into Word carries a real text layer
made of nothing but the typed headings above each image - one such file here
had 205 characters spread over 7 pages, sailed past a flat "is it empty"
check, and sent `Academic Year : 2012-2013` to the graph as the job
description. OCR on the same file returns 9111 characters. Measured across
the PDFs on hand the two groups do not overlap: scans came in at 0-29
characters a page, real text at 130 and above.

Whichever of the two is longer wins, so a false trigger costs seconds rather
than accuracy. If OCR cannot run at all, a thin text layer is discarded rather
than passed on - it was already judged unusable, and headings alone make for a
worse run than an honest 422.

It needs the optional dependency group AND Tesseract itself, which is a
separate Windows program - pip cannot install it:

```bash
uv sync --group ocr
winget install UB-Mannheim.TesseractOCR
```

**That installer does not put Tesseract on PATH**, which is the usual reason
OCR "does not work" on Windows - pytesseract raises `TesseractNotFoundError`
even though the program is sitting right there. Either add it to PATH, or
point at the exe from `.env`:

```
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

`TESSERACT_CMD` is optional. Unset, pytesseract looks on PATH as usual.

Without either of those the app still starts and normal PDFs still work. The
two OCR imports sit inside `ocr()` rather than at the top of the file, so a
missing package breaks that one function instead of the whole app. A scanned
PDF then comes back as a 422 that says so.

That 422 is the real fix here. Before it, an unreadable PDF started the graph
anyway with an empty JD, spent minutes of LLM and search calls, and handed
back a useless document without ever saying anything had gone wrong.
