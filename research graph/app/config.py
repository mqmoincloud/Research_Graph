import os
import pathlib
import threading


MAX_ROUNDS = 2

LANE_NAMES = ["technical", "soft", "general"]

LANE_TO_NODE = {
    "technical": "tech_research",
    "soft": "soft_research",
    "general": "general_research",
}

EVIDENCE_PER_LANE = 6

MAX_GITHUB_REPOS = 5

# Everything in the project sits next to app/, so one anchor is enough.
PROJECT_FOLDER = pathlib.Path(__file__).resolve().parent.parent

# The sample job descriptions, and the saved graph runs made from them by
# scripts/save_demo_run.py. app/routers/demo.py serves the saved runs.
DEMO_JDS_FOLDER = PROJECT_FOLDER / "demo_jds"
DEMO_RUNS_FOLDER = PROJECT_FOLDER / "demo_runs"


def find_file(filename):
    folder = pathlib.Path(__file__).resolve().parent

    for candidate in [folder] + list(folder.parents):
        found = candidate / filename
        if found.exists():
            return found

    return None


def get_secret(name):
    value = os.environ.get(name)
    if value:
        return value

    env_file = find_file(".env")
    if env_file is None:
        return None

    for line in env_file.read_text().splitlines():
        line = line.strip()

        if line == "" or line.startswith("#") or "=" not in line:
            continue

        parts = line.split("=", 1)
        if parts[0].strip() == name:
            return parts[1].strip()

    return None


class Config:

    origin = get_secret("ORIGIN")

    secret_key = get_secret("SECRET_KEY")

    db_url = get_secret("DB_URL")

    algorithm = get_secret("ALGORITHM")

    token_minutes = int(get_secret("TOKEN_MINUTES") or "30")

    tesseract_cmd = get_secret("TESSERACT_CMD")


config = Config()

REQUIRED = ["origin", "secret_key", "db_url", "algorithm"]

missing = [name for name in REQUIRED if not getattr(config, name)]

if missing:
    keys = ", ".join(name.upper() for name in missing)
    raise RuntimeError(
        f"Missing from .env: {keys}. Copy .env.example to .env and fill it in."
    )

if config.secret_key == "replace-me-with-a-long-random-string":
    raise RuntimeError(
        "SECRET_KEY is still the .env.example placeholder. Put a real one in .env."
    )


def log(name, message):
    thread_name = threading.current_thread().name
    print("   " + name.ljust(18) + "| " + thread_name.ljust(24) + "| " + message)
