from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import Client, QueueResource
from ..dependencies import current_client

router = APIRouter(prefix="/clients")

@router.get("/me")
async def me(client: Client = Depends(current_client)):
    return {"client_id":client.client_id,"name":client.name,"active":client.active}

@router.get("/me/queues")
async def my_queues(client: Client = Depends(current_client), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QueueResource).where(QueueResource.client_id == client.client_id))
    return [{"name":q.name,"address":q.address,"broker_id":q.broker_id,"can_produce":q.can_produce,"can_consume":q.can_consume} for q in result.scalars()]
