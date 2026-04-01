import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api import auth, companies, investors, investments, jobs, applications

settings = get_settings()

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        {"debug": 10, "info": 20, "warning": 30, "error": 40}.get(settings.log_level, 20)
    ),
)

app = FastAPI(
    title="StartupInfo API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "local" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = settings.api_v1_prefix

app.include_router(auth.router,         prefix=PREFIX)
app.include_router(companies.router,    prefix=PREFIX)
app.include_router(investors.router,    prefix=PREFIX)
app.include_router(investments.router,  prefix=PREFIX)
app.include_router(jobs.router,         prefix=PREFIX)
app.include_router(applications.router, prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
