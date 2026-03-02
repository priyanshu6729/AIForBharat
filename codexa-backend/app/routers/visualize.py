import time
from fastapi import APIRouter, Depends

from app.core.cache import LRUCache
from app.deps import get_current_user
from app.schemas.visualize import VisualizeRequest, VisualizeResponse
from app.services.s3_client import put_json
from app.services.visualizer import build_graph

router = APIRouter()
_cache = LRUCache(max_size=128)


@router.post("/api/visualize", response_model=VisualizeResponse)
def visualize(payload: VisualizeRequest, user=Depends(get_current_user)):
    cache_key = f"graph:{hash(str(payload.ast))}"
    cached = _cache.get(cache_key)
    if cached:
        return VisualizeResponse(s3_url=cached["s3_url"], graph=cached["graph"])

    graph = build_graph(payload.ast)
    prefix = f"visualizations/{payload.session_id}" if payload.session_id else "visualizations"
    key = f"{prefix}/{int(time.time())}.json"
    s3_url = put_json(key, graph)
    result = {"s3_url": s3_url, "graph": graph}
    _cache.set(cache_key, result)
    return VisualizeResponse(s3_url=s3_url, graph=graph)
