import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth, bookings, stripe
from app.utils.stripe_setup import setup_stripe_products

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting My Hibachi API...")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Setup Stripe products and prices
    if settings.environment == "development":
        await setup_stripe_products()

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down My Hibachi API...")


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.app_name,
    description="Production-ready Stripe integration for My Hibachi",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stripe.router, prefix="/api/stripe", tags=["stripe"])

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

app.include_router(bookings.router, prefix="/api/bookings", tags=["bookings"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "My Hibachi API",
        "environment": settings.environment,
        "version": "1.0.0",
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "database": "connected",
        "stripe": "configured"
        if settings.stripe_secret_key
        else "not configured",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
    )
