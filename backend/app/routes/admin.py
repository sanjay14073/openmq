import secrets
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import Client, Broker
from ..schemas import ClientCreate, ClientResponse
from ..security import hash_secret, require_admin
from ..config import settings
from ..artemis import ArtemisManager

router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])

@router.post("/clients", response_model=ClientResponse)
async def create_client(body: ClientCreate, db: AsyncSession = Depends(get_db)):
    client_id = "cli_" + secrets.token_hex(6)
    secret = secrets.token_urlsafe(24)
    result = await db.execute(select(Client).where(Client.name == body.name))
    if result.scalar_one_or_none():
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail="Client name already exists")

    manager = ArtemisManager(settings.artemis_management_url, settings.artemis_admin_user, settings.artemis_admin_password)
    await manager.create_user(client_id, secret, client_id)

    client = Client(
        client_id=client_id,
        name=body.name,
        secret_hash=hash_secret(secret),
        broker_password=secret,
    )
    db.add(client)
    await db.commit()
    return ClientResponse(client_id=client_id, name=body.name, client_secret=secret, broker_username=client_id)

@router.get("/clients")
async def list_clients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Client).order_by(Client.created_at.desc()))
    return [{"client_id": c.client_id, "name": c.name, "active": c.active} for c in result.scalars()]

@router.post("/brokers/bootstrap")
async def bootstrap_broker(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Broker).where(Broker.name == settings.default_broker_name))
    broker = result.scalar_one_or_none()
    if not broker:
        broker = Broker(
            name=settings.default_broker_name,
            management_url=settings.default_broker_management_url,
            management_user=settings.artemis_admin_user,
            management_password=settings.artemis_admin_password,
            messaging_host=settings.default_broker_messaging_host,
            internal_messaging_host=settings.default_broker_internal_host,
            stomp_port=settings.default_broker_stomp_port,
        )
        db.add(broker)
        await db.commit()
    return {"broker": broker.name, "status": "ready"}
