
import json

from fastapi import APIRouter, Depends, HTTPException

from app.config import DEMO_RUNS_FOLDER
from app.models import User
from app.security import get_current_user

demo_router = APIRouter(prefix="/api/demo")


def saved_names():
    """The <name> part of every demo_runs/<name>.json, sorted."""
    if not DEMO_RUNS_FOLDER.exists():
        return []

    names = []
    for path in DEMO_RUNS_FOLDER.glob("*.json"):
        names.append(path.stem)

    return sorted(names)


def read_saved(name):
    # Never build the path from the URL directly. "../../.env" is a legal
    # {name}, and DEMO_RUNS_FOLDER / "../../.env" is a real file - that is the
    # path traversal bug. Checking the name against the list of files we
    # actually have means an unknown name is a 404 long before any path is
    # built from it.
    if name not in saved_names():
        raise HTTPException(status_code=404, detail="No saved run by that name")

    path = DEMO_RUNS_FOLDER / (name + ".json")

    return json.loads(path.read_text(encoding="utf-8"))


@demo_router.get("")
def list_demos(current_user: User = Depends(get_current_user)):
    """Just enough to draw the buttons - the documents themselves stay behind."""
    demos = []

    for name in saved_names():
        saved = read_saved(name)
        demos.append({
            "name": name,
            "label": saved.get("label", name),
            "saved_at": saved.get("saved_at"),
        })

    return demos


@demo_router.get("/{name}")
def get_demo(name: str, current_user: User = Depends(get_current_user)):
    saved = read_saved(name)

    # Same shape POST /api/run returns, plus the two "this was not live" fields
    # the result panel needs for its badge.
    result = dict(saved["result"])
    result["is_demo"] = True
    result["saved_at"] = saved.get("saved_at")

    return result
