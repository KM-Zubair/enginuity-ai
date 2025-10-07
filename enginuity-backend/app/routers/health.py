from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("")
def status():
    return {"ok": True, "ts": datetime.utcnow().isoformat()}
