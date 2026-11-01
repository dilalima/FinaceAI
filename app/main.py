"""FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.database.session import check_database_connection
from app.routes.auth import router as auth_router
from app.routes.finance import router as finance_router
from app.routes.dashboard import router as dashboard_router
from app.routes.reports import router as reports_router
from app.routes.planning import router as planning_router
from app.routes.assistant import router as assistant_router
from app.routes.imports import router as imports_router

settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug)
frontend_path = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_path), name="static")
app.include_router(auth_router)
app.include_router(finance_router)
app.include_router(dashboard_router)
app.include_router(reports_router)
app.include_router(planning_router)
app.include_router(assistant_router)
app.include_router(imports_router)


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    """Serve the FinanceAI web interface."""

    return FileResponse(frontend_path / "index.html")


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Report whether the application process is available."""

    return {"status": "ok", "service": settings.app_name}


@app.get("/health/database", tags=["system"])
def database_health_check() -> dict[str, str]:
    """Check connectivity to the configured database."""

    try:
        check_database_connection()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

    return {"status": "ok", "database": "connected"}
