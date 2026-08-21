from fastapi import FastAPI

from app.api.batch import router as batch_router
from app.api.crawl import router as crawl_router
from app.api.health import router as health_router


app = FastAPI(
    title="AS Biz Dev Crawler",
    version="0.1.0",
)


app.include_router(health_router)
app.include_router(crawl_router)
app.include_router(batch_router)
