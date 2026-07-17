from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import STATIC_DIR, SQL_DIR
from api.files import router as files_router
from api.tables import router as tables_router

app = FastAPI(title="SQL Dump Explorer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(files_router)
app.include_router(tables_router)


@app.get("/", response_class=FileResponse)
async def home():
    return STATIC_DIR / "index.html"


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
