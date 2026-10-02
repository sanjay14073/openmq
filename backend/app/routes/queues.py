from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import Broker, QueueResource
from ..schemas import QueueCreate, QueueResponse
from ..dependencies import current_client
from ..models import Client
from ..artemis import ArtemisManager

router = APIRouter(prefix="/queues")

async def get_broker(db):
    result = await db.execute(select(Broker).where(Broker.active == True).order_by(Broker.id))
    broker = result.scalars().first()
    if not broker:
        raise HTTPException(503, "No active broker configured. Run POST /v1/admin/brokers/bootstrap first.")
    return broker

@router.post("", response_model=QueueResponse)
async def create_queue(
    body: QueueCreate,
    client: Client = Depends(current_client),
    db: AsyncSession = Depends(get_db)
):
    existing = await db.execute(select(QueueResource).where(
        QueueResource.name == body.name, QueueResource.client_id == client.client_id
    ))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Queue already exists for this client")

    broker = await get_broker(db)
    manager = ArtemisManager(broker.management_url, broker.management_user, broker.management_password)
    # Public queue names are tenant-scoped. Artemis gets a globally unique resource name.
    broker_queue_name = f"{client.client_id}.{body.name}"
    await manager.create_queue(broker_queue_name, broker_queue_name, body.durable)
    await manager.grant_queue_acl(broker_queue_name, client.client_id, body.can_produce, body.can_consume)

    resource = QueueResource(
        name=body.name,
        address=broker_queue_name,
        client_id=client.client_id,
        broker_id=broker.id,
        can_produce=body.can_produce,
        can_consume=body.can_consume,
        durable=body.durable
    )
    db.add(resource)
    await db.commit()

    return QueueResponse(
        name=resource.name, address=resource.address, client_id=client.client_id,
        broker=broker.name, broker_host=broker.messaging_host,
        stomp_port=broker.stomp_port, username=client.client_id,
        queue=resource.name, durable=resource.durable,
        can_produce=resource.can_produce, can_consume=resource.can_consume
    )

@router.get("")
async def list_queues(client: Client = Depends(current_client), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QueueResource, Broker).join(Broker, QueueResource.broker_id == Broker.id)
                              .where(QueueResource.client_id == client.client_id))
    return [
        {
            "name":q.name,"address":q.address,"broker":b.name,
            "broker_host":b.messaging_host,"stomp_port":b.stomp_port,
            "username":client.client_id,"can_produce":q.can_produce,"can_consume":q.can_consume
        }
        for q,b in result.all()
    ]

@router.delete("/{name}")
async def delete_queue(name: str, client: Client = Depends(current_client), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QueueResource, Broker).join(Broker, QueueResource.broker_id == Broker.id)
                              .where(QueueResource.name == name, QueueResource.client_id == client.client_id))
    row = result.first()
    if not row:
        raise HTTPException(404, "Queue not found")
    q,b = row
    manager = ArtemisManager(b.management_url, b.management_user, b.management_password)
    await manager.delete_queue(q.address)
    await db.delete(q)
    await db.commit()
    return {"deleted":name}
