from pydantic import BaseModel, Field

class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

class ClientResponse(BaseModel):
    client_id: str
    name: str
    client_secret: str
    broker_username: str

class ClientPublic(BaseModel):
    client_id: str
    name: str
    active: bool

class QueueCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    durable: bool = True
    can_produce: bool = True
    can_consume: bool = True

class QueueResponse(BaseModel):
    name: str
    address: str
    client_id: str
    broker: str
    broker_host: str
    stomp_port: int
    username: str
    queue: str
    durable: bool
    can_produce: bool
    can_consume: bool

class MessageRequest(BaseModel):
    body: str
