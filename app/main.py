from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import FileResponse, Response
from starlette.staticfiles import StaticFiles

from app.api.crawl import router as crawl_router
from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.results import router as results_router
from app.config import FRONTEND_ORIGINS
from app.jobs.manager import manager
from app.paths import frontend_dir
from app.storage.db import create_all_tables


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_all_tables()
    yield
    await manager.shutdown()


app = FastAPI(
    title="AS Biz Dev Web Intelligence",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(crawl_router)
app.include_router(jobs_router)
app.include_router(results_router)


class SpaStaticFiles(StaticFiles):
    """Serve the exported Next.js site, falling back to index.html so a
    browser refresh on a client-side route still resolves. Real assets
    (anything with a file extension) keep their normal 404."""

    async def get_response(self, path: str, scope):
        response = None
        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != 404:
                raise

        if (response is None or response.status_code == 404) and "." not in path.rsplit(
            "/", 1
        )[-1]:
            return FileResponse(Path(self.directory) / "index.html")

        if response is None:
            raise StarletteHTTPException(status_code=404)
        return response


_web = frontend_dir()
if (_web / "index.html").exists():
    app.mount("/", SpaStaticFiles(directory=_web, html=True), name="web")
else:  # pragma: no cover - frontend not built (dev / test)
    @app.get("/")
    async def _no_frontend() -> Response:
        return Response(
            "Frontend not built. Run `npm run build` in web/ and copy web/out "
            "to the bundle, or use the Next.js dev server.",
            media_type="text/plain",
        )
