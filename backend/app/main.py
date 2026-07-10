"""
FastAPI application factory for Remote Device Management backend.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db, close_db
from app import redis_client
from app.api import devices, commands, enrolment, updates, auth, audit
from app.ws import agent_ws, dashboard_ws

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Backend starting up...")
    await init_db()
    await redis_client.init_redis()
    yield
    # Shutdown
    print("Backend shutting down...")
    await close_db()
    await redis_client.close_redis()

def create_app() -> FastAPI:
    app = FastAPI(
        title="Remote Device Management API",
        description="Secure cross-platform remote device management system",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(auth.router)
    app.include_router(devices.router)
    app.include_router(commands.router)
    app.include_router(enrolment.router)
    app.include_router(updates.router)
    app.include_router(audit.router)
    app.include_router(agent_ws.router)
    app.include_router(dashboard_ws.router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8443, reload=True)
