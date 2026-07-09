from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
import logging
from sqlalchemy.exc import OperationalError
from app.core.config import settings
from app.core.database import engine, Base
from app.api import (
    auth_router,
    project_router,
    budget_router,
    materials_router,
    workers_router,
    attendance_router,
    risk_router,
    progress_router,
    documents_router,
    invoice_router,
    image_analysis_router,
    voice_router,
    chat_router,
    dashboard_router,
    reports_router,
    notifications_router,
)

logger = logging.getLogger(__name__)

# Auto-create tables (SQLite or PostgreSQL if connection is ready) with retry logic
max_retries = 10
retry_delay = 3
for attempt in range(max_retries):
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Successfully connected to the database and initialized tables.")
        break
    except OperationalError as e:
        if attempt == max_retries - 1:
            logger.error("Failed to connect to the database after maximum attempts.")
            raise e
        logger.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed. Retrying in {retry_delay} seconds...")
        time.sleep(retry_delay)

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.notification_service import BackgroundNotificationScheduler
    BackgroundNotificationScheduler.start()
    yield
    BackgroundNotificationScheduler.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS Middleware (allows communication with frontend dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth_router, prefix="/api")
app.include_router(project_router, prefix="/api")
app.include_router(budget_router, prefix="/api")
app.include_router(materials_router, prefix="/api")
app.include_router(workers_router, prefix="/api")
app.include_router(attendance_router, prefix="/api")
app.include_router(risk_router, prefix="/api")
app.include_router(progress_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(invoice_router, prefix="/api")
app.include_router(image_analysis_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")

@app.get("/api")
def read_root():
    return {"message": f"Welcome to the {settings.PROJECT_NAME} API. Access documentation at /api/docs"}

# Startup and shutdown lifecycles are managed by the lifespan context manager.
