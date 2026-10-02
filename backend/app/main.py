from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import init_db, SessionLocal
from .models import Broker
from .config import settings
from sqlalchemy import select
from .routes import admin, clients, queues, messages, health

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with SessionLocal() as db:
        result = await db.execute(select(Broker).where(Broker.name == settings.default_broker_name))
        if not result.scalar_one_or_none():
            db.add(Broker(
                name=settings.default_broker_name,
                management_url=settings.default_broker_management_url,
                management_user=settings.artemis_admin_user,
                management_password=settings.artemis_admin_password,
                messaging_host=settings.default_broker_messaging_host,
                internal_messaging_host=settings.default_broker_internal_host,
                stomp_port=settings.default_broker_stomp_port,
            ))
            await db.commit()
    yield

app = FastAPI(title="OpenMQ Control Plane", version="0.2.0", lifespan=lifespan, docs_url="/api/docs", redoc_url="/api/redoc", openapi_url="/api/openapi.json")

origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/v1")
app.include_router(admin.router, prefix="/v1")
app.include_router(clients.router, prefix="/v1")
app.include_router(queues.router, prefix="/v1")
app.include_router(messages.router, prefix="/v1")

@app.get("/")
async def root():
    return {"service": "openmq-control-plane", "docs": "/api/docs", "health": "/v1/health"}
