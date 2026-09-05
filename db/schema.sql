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

CREATE TABLE vehicle_locations (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
    trip_id INTEGER REFERENCES trips(id),
    location GEOMETRY(POINT, 4326) NOT NULL,
    speed_kmh NUMERIC,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stops_location
ON stops USING GIST(location);

CREATE INDEX idx_routes_geometry
ON routes USING GIST(geometry);

CREATE INDEX idx_vehicle_locations_vehicle_time
ON vehicle_locations(vehicle_id, recorded_at DESC);