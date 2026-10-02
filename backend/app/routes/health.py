from fastapi import APIRouter
from ..config import settings
from ..artemis import ArtemisManager
router = APIRouter()

@router.get("/health")
async def health():
    return {"status":"ok","service":"openmq-control-plane"}

@router.get("/health/broker")
async def broker_health():
    manager = ArtemisManager(settings.artemis_management_url, settings.artemis_admin_user, settings.artemis_admin_password)
    try:
        version = await manager.broker_version()
        return {"status":"ok","broker":"artemis","version":version}
    except Exception as e:
        return {"status":"degraded","error":str(e)}
