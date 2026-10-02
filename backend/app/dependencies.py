from sqlalchemy import select
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .db import get_db
from .models import Client
from .security import require_client_headers, verify_secret

async def current_client(
    headers=Depends(require_client_headers),
    db: AsyncSession = Depends(get_db)
):
    client_id, secret = headers
    result = await db.execute(select(Client).where(Client.client_id == client_id, Client.active == True))
    client = result.scalar_one_or_none()
    if not client or not verify_secret(secret, client.secret_hash):
        raise HTTPException(status_code=401, detail="Invalid client credentials")
    return client
