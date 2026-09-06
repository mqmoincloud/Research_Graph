import io

from fastapi import FastAPI, File, UploadFile
from pypdf import PdfReader

from app.graph import build_graph

app = FastAPI()

graph = build_graph()


@app.post("/api/run")
async def run(file: UploadFile = File(...)):
    raw = await file.read()

    if (file.filename or "").lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(raw))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        text = raw.decode("utf-8", errors="ignore")

    return graph.invoke({"jd_text": text.strip()})
