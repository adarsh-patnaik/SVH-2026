-- Sample Routes

INSERT INTO routes (route_code, name, geometry)
VALUES
(
    'R1',
    'Route 1',
    ST_GeomFromText(
        'LINESTRING(
            85.8245 20.2961,
            85.8280 20.2985,
            85.8320 20.3010,
            85.8360 20.3040
        )',
        4326
    )
),
(
    'R2',
    'Route 2',
    ST_GeomFromText(
        'LINESTRING(
            85.8200 20.2900,
            85.8240 20.2930,
            85.8280 20.2960,
            85.8320 20.2990
        )',
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

-- Route Segments
-- Segment metadata is aligned with the ML team's R1/R2 segment IDs.

INSERT INTO route_segments
    (route_id, segment_code, segment_order, segment_type, distance_km)
VALUES
-- Route R1
(1, 'R1_S1', 1, 'market', 0.9),
(1, 'R1_S2', 2, 'signalized_corridor', 1.4),
(1, 'R1_S3', 3, 'flyover', 2.6),
(1, 'R1_S4', 4, 'narrow_lane', 1.1),
(1, 'R1_S5', 5, 'residential', 2.2),
(1, 'R1_S6', 6, 'highway', 3.8),
(1, 'R1_S7', 7, 'school_zone', 1.8),
(1, 'R1_S8', 8, 'commercial_hub', 2.5),

-- Route R2
(2, 'R2_S1', 1, 'market', 0.8),
(2, 'R2_S2', 2, 'narrow_lane', 1.0),
(2, 'R2_S3', 3, 'signalized_corridor', 2.1),
(2, 'R2_S4', 4, 'flyover', 3.2),
(2, 'R2_S5', 5, 'residential', 1.9),
(2, 'R2_S6', 6, 'school_zone', 1.3),
(2, 'R2_S7', 7, 'residential', 1.6);

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

-- Sample Historical Segment Travel Times

INSERT INTO segment_travel_history
    (
        segment_id,
        vehicle_id,
        travel_time_seconds,
        current_speed_kmh,
        previous_speed_kmh,
        weather_severity
    )
VALUES
(1, 1, 105, 31, 29, 0),
(1, 2, 112, 29, 30, 0),
(2, 1, 170, 30, 31, 0),
(2, 2, 182, 27, 30, 1),
(3, 1, 310, 36, 35, 0),
(4, 1, 145, 25, 27, 1),
(5, 2, 220, 24, 26, 0),
(6, 2, 390, 35, 34, 0),
(7, 2, 205, 18, 20, 1),
(8, 1, 250, 30, 28, 0),

(9, 2, 95, 30, 31, 0),
(10, 2, 130, 27, 28, 0),
(11, 1, 230, 29, 30, 1),
(12, 2, 340, 34, 33, 0),
(13, 2, 175, 25, 24, 0),
(14, 1, 125, 19, 21, 1),
(15, 1, 160, 23, 22, 0);