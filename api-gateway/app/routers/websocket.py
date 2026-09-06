import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["live updates"])


@router.websocket("/ws/buses")
async def bus_updates(websocket: WebSocket):
    await websocket.accept()
    pubsub = websocket.app.state.redis.pubsub()
    await pubsub.subscribe("bus-updates")
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                await websocket.send_json(json.loads(message["data"]))
            await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe("bus-updates")
        await pubsub.aclose()
