CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    route_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    geometry GEOMETRY(LINESTRING, 4326)
);

CREATE TABLE stops (
    id SERIAL PRIMARY KEY,
    route_id INTEGER NOT NULL REFERENCES routes(id),
    name VARCHAR(100) NOT NULL,
    stop_order INTEGER NOT NULL,
    location GEOMETRY(POINT, 4326) NOT NULL
);

CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    vehicle_code VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'inactive'
);

CREATE TABLE trips (
    id SERIAL PRIMARY KEY,
    route_id INTEGER NOT NULL REFERENCES routes(id),
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
    status VARCHAR(20) DEFAULT 'scheduled',
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ
);

CREATE TABLE route_segments (
    id SERIAL PRIMARY KEY,
    route_id INTEGER NOT NULL REFERENCES routes(id),
    segment_code VARCHAR(50) UNIQUE NOT NULL,
    segment_order INTEGER NOT NULL,
    segment_type VARCHAR(50) NOT NULL,
    distance_km NUMERIC(8,2) NOT NULL
);

CREATE TABLE vehicle_locations (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
    trip_id INTEGER REFERENCES trips(id),
    location GEOMETRY(POINT, 4326) NOT NULL,
    speed_kmh NUMERIC,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE segment_travel_history (
    id BIGSERIAL PRIMARY KEY,
    segment_id INTEGER NOT NULL REFERENCES route_segments(id),
    vehicle_id INTEGER REFERENCES vehicles(id),
    travel_time_seconds NUMERIC(10,2) NOT NULL,
    current_speed_kmh NUMERIC(8,2),
    previous_speed_kmh NUMERIC(8,2),
    weather_severity INTEGER DEFAULT 0,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stops_location
ON stops USING GIST(location);

CREATE INDEX idx_routes_geometry
ON routes USING GIST(geometry);

CREATE INDEX idx_vehicle_locations_vehicle_time
ON vehicle_locations(vehicle_id, recorded_at DESC);

CREATE INDEX idx_route_segments_route
ON route_segments(route_id, segment_order);

CREATE INDEX idx_segment_history_segment_time
ON segment_travel_history(segment_id, recorded_at DESC);