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


def log(name, message):
    thread_name = threading.current_thread().name
    print("   " + name.ljust(18) + "| " + thread_name.ljust(24) + "| " + message)
