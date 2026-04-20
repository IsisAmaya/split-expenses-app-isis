"""Punto de entrada de la API REST."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .config import settings
from .database import engine
from .routes.expenses import router as expenses_router
from .routes.groups import router as groups_router
from .schemas import HealthResponse

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- CORS: permitir que el frontend se comunique con la API ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Registrar routers ---
app.include_router(groups_router)
app.include_router(expenses_router)


# --- Health check ---
@app.get("/health", response_model=HealthResponse, tags=["system"])
def health_check():
    """Verifica el estado de la aplicación y la conexión a DB."""
    db_status = "healthy"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:  # pylint: disable=broad-exception-caught
        db_status = "unhealthy"

    return HealthResponse(
        status="ok" if db_status == "healthy" else "degraded",
        database=db_status,
        environment=settings.app_env,
        version=settings.app_version,
    )
