from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.batch import router as batch_router
from app.api.crawl import router as crawl_router
from app.api.health import router as health_router
from app.config import FRONTEND_ORIGINS


app = FastAPI(
    title="AS Biz Dev Crawler",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


app.include_router(health_router)
app.include_router(crawl_router)
app.include_router(batch_router)
