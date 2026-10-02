from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import stomp
import time

from ..db import get_db
from ..models import QueueResource, Broker, Client
from ..schemas import MessageRequest
from ..dependencies import current_client


router = APIRouter(prefix="/messages")


async def resolve_queue(name, client, db):
    result = await db.execute(
        select(QueueResource, Broker)
        .join(Broker, QueueResource.broker_id == Broker.id)
        .where(
            QueueResource.name == name,
            QueueResource.client_id == client.client_id,
        )
    )

    row = result.first()

    if not row:
        raise HTTPException(404, "Queue not found")

    return row


def connection(broker, client):
    conn = stomp.Connection12(
        [(broker.internal_messaging_host, broker.stomp_port)]
    )

    conn.connect(
        client.client_id,
        client.broker_password,
        wait=True,
    )

    return conn


@router.post("/{queue}/send")
async def send(
    queue: str,
    body: MessageRequest,
    client: Client = Depends(current_client),
    db: AsyncSession = Depends(get_db),
):
    q, broker = await resolve_queue(queue, client, db)

    if not q.can_produce:
        raise HTTPException(
            status_code=403,
            detail="Client cannot produce to this queue",
        )

    errors = []

    class SendListener(stomp.ConnectionListener):
        def on_error(self, frame):
            errors.append(frame.body)

    conn = connection(broker, client)
    conn.set_listener("send-listener", SendListener())

    try:
        conn.send(
            destination=q.address,
            body=body.body,
            persistent="true",
            headers={
                "destination-type": "ANYCAST",
            },
        )

        # Give Artemis a moment to return an ERROR frame.
        time.sleep(0.2)

        if errors:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Artemis rejected the message",
                    "error": errors[0],
                    "address": q.address,
                },
            )

    finally:
        conn.disconnect()

    return {
        "status": "sent",
        "queue": q.name,
        "address": q.address,
    }


@router.get("/{queue}/receive")
async def receive(
    queue: str,
    client: Client = Depends(current_client),
    db: AsyncSession = Depends(get_db),
):
    q, broker = await resolve_queue(queue, client, db)

    if not q.can_consume:
        raise HTTPException(
            status_code=403,
            detail="Client cannot consume from this queue",
        )

    messages = []
    errors = []

    class Listener(stomp.ConnectionListener):

        def on_message(self, frame):
            messages.append(
                {
                    "body": frame.body,
                    "message_id": frame.headers.get("message-id"),
                }
            )

        def on_error(self, frame):
            errors.append(frame.body)

    conn = connection(broker, client)

    subscription_id = f"openmq-{client.client_id}-{q.name}"

    conn.set_listener("receive-listener", Listener())

    try:
        conn.subscribe(
            destination=q.address,
            id=subscription_id,
            ack="client-individual",
            headers={
                "subscription-type": "ANYCAST",
            },
        )

        time.sleep(0.8)

        if errors:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Artemis rejected the subscription",
                    "error": errors[0],
                    "address": q.address,
                },
            )

        for message in messages:
            message_id = message.get("message_id")

            if message_id:
                conn.ack(
                    message_id,
                    subscription_id,
                )
                break

    finally:
        conn.disconnect()

    return {
        "messages": messages[:10],
        "address": q.address,
    }
