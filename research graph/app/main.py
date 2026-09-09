import logging

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import config
from app.graph import build_graph
from app.models import User
from app.pdf import MIN_TEXT, extract_text
from app.routers import auth_router, demo_router
from app.security import get_current_user

logger = logging.getLogger("uvicorn.error")

app = FastAPI()

graph = build_graph()

@app.exception_handler(StarletteHTTPException)
def http_error(request: Request, exc: StarletteHTTPException):

    logger.warning(
        "%s %s -> %s %s", request.method, request.url.path, exc.status_code, exc.detail
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {
            "status": exc.status_code,
            "message": exc.detail,
            "fields": {},
        }},
    )


@app.exception_handler(RequestValidationError)
def validation_error(request: Request, exc: RequestValidationError):
    # Pydantic reports the whole path to the bad value; only the last part is
    # the field name the form knows about.
    fields = {}
    for err in exc.errors():
        name = err["loc"][-1]
        fields[name] = err["msg"]

    logger.warning("%s %s -> 422 %s", request.method, request.url.path, fields)

    return JSONResponse(
        status_code=422,
        content={"error": {
            "status": 422,
            "message": "Validation failed",
            "fields": fields,
        }},
    )


@app.exception_handler(Exception)
def unexpected_error(request: Request, exc: Exception):
    # The real traceback goes to the terminal, never to the browser.
    logger.error(
        "Unhandled error: %s %s", request.method, request.url.path, exc_info=exc
    )

    return JSONResponse(
        status_code=500,
        content={"error": {
            "status": 500,
            "message": "Something went wrong.",
            "fields": {},
        }},
    )


app.include_router(auth_router)
app.include_router(demo_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/run")
async def run(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
   
    raw = await file.read()

    text = extract_text(raw, file.filename)

    if len(text) < MIN_TEXT:
        raise HTTPException(
            status_code=422,
            detail="Could not read any text from that file. A scanned PDF "
                   "needs OCR, and OCR could not read this one either - try "
                   "a PDF with a real text layer, or a .txt.",
        )

    print(text)

    return graph.invoke({"jd_text": text})
