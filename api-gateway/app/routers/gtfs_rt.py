import time

from fastapi import APIRouter, Request, Response
from google.transit import gtfs_realtime_pb2

from app.state import live_buses

router = APIRouter(tags=["GTFS-Realtime"])


@router.get("/gtfs-rt/vehicle-positions.pb", response_class=Response)
async def vehicle_positions(request: Request):
    """Public GTFS-RT vehicle feed; live positions disappear after the Redis TTL."""
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.header.gtfs_realtime_version = "2.0"
    feed.header.incrementality = gtfs_realtime_pb2.FeedHeader.FULL_DATASET
    feed.header.timestamp = int(time.time())

    index = 0
    async for bus in live_buses(request.app.state.redis):
        entity = feed.entity.add()
        entity.id = f"vehicle-{bus['bus_id']}"
        vehicle = entity.vehicle
        vehicle.vehicle.id = bus["bus_id"]
        vehicle.trip.route_id = bus["route_id"]
        vehicle.position.latitude = bus["latitude"]
        vehicle.position.longitude = bus["longitude"]
        vehicle.position.speed = bus["speed_mps"]
        vehicle.position.bearing = bus["heading_degrees"]
        vehicle.timestamp = bus["captured_at_unix_ms"] // 1000
        index += 1

    return Response(content=feed.SerializeToString(), media_type="application/x-protobuf", headers={"Cache-Control": "no-store", "X-GatiSync-Vehicles": str(index)})
