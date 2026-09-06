import pathlib
import sys

PROJECT_FOLDER = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_FOLDER))

from app.graph import build_graph


print(build_graph().get_graph().draw_mermaid())
