import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_FOLDER = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_FOLDER))

from app.graph import build_graph


JD = """Backend Engineer - Fintech startup, Bangalore.

We are looking for a backend engineer with 3+ years of experience.
You will work with Python and FastAPI, design PostgreSQL schemas, and
deploy services with Docker. You will also mentor junior developers and
work closely with the product team.
"""


print("=" * 72)
print("Feeding in the JD")
print("=" * 72)

graph = build_graph()
result = graph.invoke({"jd_text": JD})

print()
print("evidence found      :", len(result["evidence"]))
print("rounds run          :", result["round"])
print("budget used up      :", result["exhausted"])
print()
print("-" * 72)
print(result["prep_document"])
