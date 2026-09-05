-- Sample Routes
INSERT INTO routes (route_code, name, geometry)
VALUES
(
    'R1',
    'Route 1',
    ST_GeomFromText(
        'LINESTRING(85.8245 20.2961, 85.8280 20.2985, 85.8320 20.3010, 85.8360 20.3040)',
        4326
    )
),
(
    'R2',
    'Route 2',
    ST_GeomFromText(
        'LINESTRING(85.8200 20.2900, 85.8240 20.2930, 85.8280 20.2960, 85.8320 20.2990)',
        4326
    )
);

-- Sample Stops
INSERT INTO stops (route_id, name, stop_order, location)
VALUES
(1, 'Stop A', 1, ST_SetSRID(ST_Point(85.8245, 20.2961), 4326)),
(1, 'Stop B', 2, ST_SetSRID(ST_Point(85.8280, 20.2985), 4326)),
(1, 'Stop C', 3, ST_SetSRID(ST_Point(85.8320, 20.3010), 4326)),
(1, 'Stop D', 4, ST_SetSRID(ST_Point(85.8360, 20.3040), 4326)),

(2, 'Stop E', 1, ST_SetSRID(ST_Point(85.8200, 20.2900), 4326)),
(2, 'Stop F', 2, ST_SetSRID(ST_Point(85.8240, 20.2930), 4326)),
(2, 'Stop G', 3, ST_SetSRID(ST_Point(85.8280, 20.2960), 4326)),
(2, 'Stop H', 4, ST_SetSRID(ST_Point(85.8320, 20.2990), 4326));

-- Sample Vehicles
INSERT INTO vehicles (vehicle_code, status)
VALUES
('BUS-001', 'active'),
('BUS-002', 'active');

-- Sample Trips
INSERT INTO trips (route_id, vehicle_id, status, started_at)
VALUES
(1, 1, 'running', NOW()),
(2, 2, 'running', NOW());

-- Sample Live Vehicle Locations
INSERT INTO vehicle_locations
    (vehicle_id, trip_id, location, speed_kmh)
VALUES
(
    1,
    1,
    ST_SetSRID(ST_Point(85.8280, 20.2985), 4326),
    32
),
(
    2,
    2,
    ST_SetSRID(ST_Point(85.8240, 20.2930), 4326),
    28
);