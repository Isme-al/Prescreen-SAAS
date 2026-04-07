from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import protocols, screening


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Clinical Prescreening Tool",
    description="Local-first medical history prescreening against protocol inclusion/exclusion criteria with automatic PHI redaction.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(protocols.router)
app.include_router(screening.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "prescreen"}
