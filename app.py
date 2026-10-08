"""
SMART BUS - MASTER DATABASE
Python 3.13
SQLite database - standard library only

Hierarchy:

District
    └── Town / Village
            └── Bus Stand
                    └── Stop
                            └── Route
                                    └── Route Stop
                                            └── Service
                                                    └── Fare

Additional:
Scheme
Passenger
Ticket
Ticket Passenger
Bus
Driver

Run:
    python master_database.py

Database created:
    smart_bus.db
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


# ============================================================
# CONFIGURATION
# ============================================================

DB_FILE = Path("smart_bus.db")


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_FILE)

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")

    return connection


# ============================================================
# DATABASE SCHEMA
# ============================================================

SCHEMA = """

PRAGMA foreign_keys = ON;


-- ==========================================================
-- 1. DISTRICTS
-- ==========================================================

CREATE TABLE IF NOT EXISTS districts (
    district_id INTEGER PRIMARY KEY AUTOINCREMENT,
    district_code TEXT NOT NULL UNIQUE,
    district_name TEXT NOT NULL UNIQUE,
    state_name TEXT NOT NULL DEFAULT 'Tamil Nadu',
    active INTEGER NOT NULL DEFAULT 1
);


-- ==========================================================
-- 2. LOCALITIES
-- Town / City / Municipality / Corporation / Village
-- ==========================================================

CREATE TABLE IF NOT EXISTS localities (
    locality_id INTEGER PRIMARY KEY AUTOINCREMENT,

    district_id INTEGER NOT NULL,

    locality_code TEXT NOT NULL UNIQUE,
    locality_name TEXT NOT NULL,

    locality_type TEXT NOT NULL CHECK (
        locality_type IN (
            'CITY',
            'TOWN',
            'TOWN_PANCHAYAT',
            'MUNICIPALITY',
            'MUNICIPAL_CORPORATION',
            'VILLAGE',
            'HAMLET',
            'OTHER'
        )
    ),

    pincode TEXT,

    latitude REAL,
    longitude REAL,

    active INTEGER NOT NULL DEFAULT 1,

    FOREIGN KEY (district_id)
        REFERENCES districts(district_id)
        ON DELETE RESTRICT,

    UNIQUE (district_id, locality_name)
);


-- ==========================================================
-- 3. BUS STANDS
-- ==========================================================

CREATE TABLE IF NOT EXISTS bus_stands (
    bus_stand_id INTEGER PRIMARY KEY AUTOINCREMENT,

    locality_id INTEGER NOT NULL,

    bus_stand_code TEXT NOT NULL UNIQUE,
    bus_stand_name TEXT NOT NULL,

    bus_stand_type TEXT NOT NULL CHECK (
        bus_stand_type IN (
            'CENTRAL',
            'MOFUSSIL',
            'TOWN',
            'INTERSTATE',
            'DEPOT',
            'TERMINAL',
            'VILLAGE',
            'OTHER'
        )
    ),

    address TEXT,

    latitude REAL,
    longitude REAL,

    bus_bays INTEGER DEFAULT 0,

    active INTEGER NOT NULL DEFAULT 1,

    FOREIGN KEY (locality_id)
        REFERENCES localities(locality_id)
        ON DELETE RESTRICT
);


-- ==========================================================
-- 4. STOPS
-- Every physical pickup/drop point
-- ==========================================================

CREATE TABLE IF NOT EXISTS stops (
    stop_id INTEGER PRIMARY KEY AUTOINCREMENT,

    bus_stand_id INTEGER,

    locality_id INTEGER NOT NULL,

    stop_code TEXT NOT NULL UNIQUE,
    stop_name TEXT NOT NULL,

    stop_type TEXT NOT NULL CHECK (
        stop_type IN (
            'BUS_STAND',
            'BUS_STOP',
            'JUNCTION',
            'VILLAGE_STOP',
            'HIGHWAY_STOP',
            'DEPOT',
            'OTHER'
        )
    ),

    landmark TEXT,

    latitude REAL,
    longitude REAL,

    active INTEGER NOT NULL DEFAULT 1,

    FOREIGN KEY (bus_stand_id)
        REFERENCES bus_stands(bus_stand_id)
        ON DELETE SET NULL,

    FOREIGN KEY (locality_id)
        REFERENCES localities(locality_id)
        ON DELETE RESTRICT
);


-- ==========================================================
-- 5. OPERATORS
-- MTC / TNSTC / SETC / PRIVATE / INTERSTATE
-- ==========================================================

CREATE TABLE IF NOT EXISTS operators (
    operator_id INTEGER PRIMARY KEY AUTOINCREMENT,

    operator_code TEXT NOT NULL UNIQUE,
    operator_name TEXT NOT NULL,

    operator_type TEXT NOT NULL CHECK (
        operator_type IN (
            'MTC',
            'TNSTC',
            'SETC',
            'PRIVATE',
            'KSRTC',
            'APSRTC',
            'TSRTC',
            'OTHER'
        )
    ),

    state_name TEXT,

    booking_enabled INTEGER NOT NULL DEFAULT 0,

    active INTEGER NOT NULL DEFAULT 1
);


-- ==========================================================
-- 6. BUSES
-- ==========================================================

CREATE TABLE IF NOT EXISTS buses (
    bus_id INTEGER PRIMARY KEY AUTOINCREMENT,

    bus_code TEXT NOT NULL UNIQUE,
    registration_number TEXT UNIQUE,

    operator_id INTEGER,

    route_number TEXT,

    bus_type TEXT NOT NULL DEFAULT 'ORDINARY',

    capacity INTEGER NOT NULL CHECK (capacity > 0),

    available_seats INTEGER NOT NULL DEFAULT 0,

    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (
        status IN (
            'ACTIVE',
            'RUNNING',
            'MAINTENANCE',
            'INACTIVE',
            'CANCELLED'
        )
    ),

    wheelchair_accessible INTEGER NOT NULL DEFAULT 0,

    air_conditioned INTEGER NOT NULL DEFAULT 0,

    sleeper INTEGER NOT NULL DEFAULT 0,

    seater INTEGER NOT NULL DEFAULT 1,

    FOREIGN KEY (operator_id)
        REFERENCES operators(operator_id)
        ON DELETE SET NULL
);


-- ==========================================================
-- 7. DRIVERS
-- ==========================================================

CREATE TABLE IF NOT EXISTS drivers (
    driver_id INTEGER PRIMARY KEY AUTOINCREMENT,

    driver_code TEXT NOT NULL UNIQUE,

    driver_name TEXT NOT NULL,

    phone TEXT,

    license_number TEXT UNIQUE,

    license_expiry TEXT,

    active INTEGER NOT NULL DEFAULT 1
);


-- ==========================================================
-- 8. ROUTES
-- ==========================================================

CREATE TABLE IF NOT EXISTS routes (
    route_id INTEGER PRIMARY KEY AUTOINCREMENT,

    route_code TEXT NOT NULL UNIQUE,

    route_number TEXT,

    route_name TEXT NOT NULL,

    operator_id INTEGER,

    source_stop_id INTEGER NOT NULL,

    destination_stop_id INTEGER NOT NULL,

    total_distance_km REAL,

    estimated_duration_minutes INTEGER,

    route_type TEXT NOT NULL DEFAULT 'INTERCITY' CHECK (
        route_type IN (
            'CITY',
            'SUBURBAN',
            'INTERCITY',
            'INTERSTATE',
            'RURAL',
            'EXPRESS'
        )
    ),

    active INTEGER NOT NULL DEFAULT 1,

    FOREIGN KEY (operator_id)
        REFERENCES operators(operator_id)
        ON DELETE SET NULL,

    FOREIGN KEY (source_stop_id)
        REFERENCES stops(stop_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (destination_stop_id)
        REFERENCES stops(stop_id)
        ON DELETE RESTRICT
);


-- ==========================================================
-- 9. ROUTE STOPS
-- Ordered stops belonging to a route
-- ==========================================================

CREATE TABLE IF NOT EXISTS route_stops (
    route_stop_id INTEGER PRIMARY KEY AUTOINCREMENT,

    route_id INTEGER NOT NULL,
    stop_id INTEGER NOT NULL,

    stop_sequence INTEGER NOT NULL,

    distance_from_origin_km REAL DEFAULT 0,

    arrival_offset_minutes INTEGER DEFAULT 0,
    departure_offset_minutes INTEGER DEFAULT 0,

    boarding_allowed INTEGER NOT NULL DEFAULT 1,
    dropping_allowed INTEGER NOT NULL DEFAULT 1,

    FOREIGN KEY (route_id)
        REFERENCES routes(route_id)
        ON DELETE CASCADE,

    FOREIGN KEY (stop_id)
        REFERENCES stops(stop_id)
        ON DELETE RESTRICT,

    UNIQUE (route_id, stop_sequence),
    UNIQUE (route_id, stop_id)
);


-- ==========================================================
-- 10. SERVICES / TRIPS
-- A particular bus journey on a route
-- ==========================================================

CREATE TABLE IF NOT EXISTS services (
    service_id INTEGER PRIMARY KEY AUTOINCREMENT,

    service_code TEXT NOT NULL UNIQUE,

    route_id INTEGER NOT NULL,

    bus_id INTEGER,

    driver_id INTEGER,

    service_name TEXT,

    service_class TEXT NOT NULL DEFAULT 'ORDINARY',

    departure_time TEXT NOT NULL,
    arrival_time TEXT,

    journey_date TEXT,

    operating_days TEXT,

    live_status TEXT NOT NULL DEFAULT 'SCHEDULED' CHECK (
        live_status IN (
            'SCHEDULED',
            'BOARDING',
            'RUNNING',
            'COMPLETED',
            'CANCELLED',
            'DELAYED'
        )
    ),

    total_seats INTEGER DEFAULT 0,
    available_seats INTEGER DEFAULT 0,

    FOREIGN KEY (route_id)
        REFERENCES routes(route_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (bus_id)
        REFERENCES buses(bus_id)
        ON DELETE SET NULL,

    FOREIGN KEY (driver_id)
        REFERENCES drivers(driver_id)
        ON DELETE SET NULL
);


-- ==========================================================
-- 11. FARE RULES
-- ==========================================================

CREATE TABLE IF NOT EXISTS fares (
    fare_id INTEGER PRIMARY KEY AUTOINCREMENT,

    operator_id INTEGER,

    route_id INTEGER,

    service_class TEXT NOT NULL,

    fare_type TEXT NOT NULL CHECK (
        fare_type IN (
            'STAGE',
            'PER_KM',
            'FIXED',
            'FLEXI',
            'SPECIAL'
        )
    ),

    minimum_distance_km REAL DEFAULT 0,
    maximum_distance_km REAL,

    rate_per_km REAL,
    base_fare REAL DEFAULT 0,

    fixed_fare REAL,

    minimum_fare REAL DEFAULT 0,
    maximum_fare REAL,

    peak_multiplier REAL DEFAULT 1.0,

    effective_from TEXT NOT NULL,
    effective_to TEXT,

    source_reference TEXT,

    active INTEGER NOT NULL DEFAULT 1,

    FOREIGN KEY (operator_id)
        REFERENCES operators(operator_id)
        ON DELETE SET NULL,

    FOREIGN KEY (route_id)
        REFERENCES routes(route_id)
        ON DELETE SET NULL
);


-- ==========================================================
-- 12. FARE STAGES
-- For stage-based city/town fares
-- ==========================================================

CREATE TABLE IF NOT EXISTS fare_stages (
    fare_stage_id INTEGER PRIMARY KEY AUTOINCREMENT,

    operator_id INTEGER,

    service_class TEXT NOT NULL,

    stage_number INTEGER NOT NULL,

    distance_km REAL NOT NULL,

    fare_amount REAL NOT NULL,

    effective_from TEXT NOT NULL,

    effective_to TEXT,

    source_reference TEXT,

    FOREIGN KEY (operator_id)
        REFERENCES operators(operator_id)
        ON DELETE SET NULL,

    UNIQUE (
        operator_id,
        service_class,
        stage_number,
        effective_from
    )
);


-- ==========================================================
-- 13. SCHEMES
-- ==========================================================

CREATE TABLE IF NOT EXISTS schemes (
    scheme_id INTEGER PRIMARY KEY AUTOINCREMENT,

    scheme_code TEXT NOT NULL UNIQUE,

    scheme_name TEXT NOT NULL,

    scheme_type TEXT NOT NULL CHECK (
        scheme_type IN (
            'FREE_TRAVEL',
            'PERCENT_DISCOUNT',
            'FIXED_DISCOUNT',
            'PASS',
            'CONCESSION',
            'SPECIAL'
        )
    ),

    passenger_category TEXT NOT NULL,

    discount_percent REAL DEFAULT 0,

    fixed_discount REAL DEFAULT 0,

    zero_fare INTEGER NOT NULL DEFAULT 0,

    eligibility_description TEXT,

    required_document TEXT,

    eligible_service_types TEXT,

    applicable_operator_types TEXT,

    minimum_age INTEGER,

    maximum_age INTEGER,

    effective_from TEXT,

    effective_to TEXT,

    source_reference TEXT,

    active INTEGER NOT NULL DEFAULT 1
);


-- ==========================================================
-- 14. SCHEME RULES
-- More detailed route/service/operator rules
-- ==========================================================

CREATE TABLE IF NOT EXISTS scheme_rules (
    scheme_rule_id INTEGER PRIMARY KEY AUTOINCREMENT,

    scheme_id INTEGER NOT NULL,

    operator_id INTEGER,

    route_id INTEGER,

    service_class TEXT,

    origin_locality_id INTEGER,

    destination_locality_id INTEGER,

    max_distance_km REAL,

    allowed_days TEXT,

    start_time TEXT,

    end_time TEXT,

    FOREIGN KEY (scheme_id)
        REFERENCES schemes(scheme_id)
        ON DELETE CASCADE,

    FOREIGN KEY (operator_id)
        REFERENCES operators(operator_id)
        ON DELETE SET NULL,

    FOREIGN KEY (route_id)
        REFERENCES routes(route_id)
        ON DELETE SET NULL,

    FOREIGN KEY (origin_locality_id)
        REFERENCES localities(locality_id)
        ON DELETE SET NULL,

    FOREIGN KEY (destination_locality_id)
        REFERENCES localities(locality_id)
        ON DELETE SET NULL
);


-- ==========================================================
-- 15. PASSENGERS
-- ==========================================================

CREATE TABLE IF NOT EXISTS passengers (
    passenger_id INTEGER PRIMARY KEY AUTOINCREMENT,

    passenger_code TEXT NOT NULL UNIQUE,

    full_name TEXT NOT NULL,

    age INTEGER,

    gender TEXT,

    phone TEXT,

    email TEXT,

    passenger_category TEXT NOT NULL DEFAULT 'GENERAL',

    identity_type TEXT,

    identity_number TEXT,

    scheme_id INTEGER,

    created_at TEXT NOT NULL,

    FOREIGN KEY (scheme_id)
        REFERENCES schemes(scheme_id)
        ON DELETE SET NULL
);


-- ==========================================================
-- 16. TICKETS
-- ==========================================================

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,

    pnr TEXT NOT NULL UNIQUE,

    service_id INTEGER NOT NULL,

    boarding_stop_id INTEGER NOT NULL,

    dropping_stop_id INTEGER NOT NULL,

    booking_date TEXT NOT NULL,

    travel_date TEXT NOT NULL,

    passenger_count INTEGER NOT NULL DEFAULT 1,

    base_fare REAL NOT NULL DEFAULT 0,

    discount_amount REAL NOT NULL DEFAULT 0,

    final_fare REAL NOT NULL DEFAULT 0,

    payment_status TEXT NOT NULL DEFAULT 'PENDING' CHECK (
        payment_status IN (
            'PENDING',
            'PAID',
            'FAILED',
            'REFUNDED'
        )
    ),

    ticket_status TEXT NOT NULL DEFAULT 'CONFIRMED' CHECK (
        ticket_status IN (
            'CONFIRMED',
            'CANCELLED',
            'COMPLETED',
            'NO_SHOW'
        )
    ),

    created_at TEXT NOT NULL,

    FOREIGN KEY (service_id)
        REFERENCES services(service_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (boarding_stop_id)
        REFERENCES stops(stop_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (dropping_stop_id)
        REFERENCES stops(stop_id)
        ON DELETE RESTRICT
);


-- ==========================================================
-- 17. TICKET PASSENGERS
-- ==========================================================

CREATE TABLE IF NOT EXISTS ticket_passengers (
    ticket_passenger_id INTEGER PRIMARY KEY AUTOINCREMENT,

    ticket_id INTEGER NOT NULL,

    passenger_id INTEGER NOT NULL,

    seat_number TEXT,

    passenger_fare REAL DEFAULT 0,

    scheme_discount REAL DEFAULT 0,

    FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id)
        ON DELETE CASCADE,

    FOREIGN KEY (passenger_id)
        REFERENCES passengers(passenger_id)
        ON DELETE RESTRICT
);


-- ==========================================================
-- 18. INDEXES
-- ==========================================================

CREATE INDEX IF NOT EXISTS idx_localities_district
ON localities(district_id);

CREATE INDEX IF NOT EXISTS idx_bus_stands_locality
ON bus_stands(locality_id);

CREATE INDEX IF NOT EXISTS idx_stops_locality
ON stops(locality_id);

CREATE INDEX IF NOT EXISTS idx_routes_source
ON routes(source_stop_id);

CREATE INDEX IF NOT EXISTS idx_routes_destination
ON routes(destination_stop_id);

CREATE INDEX IF NOT EXISTS idx_route_stops_route
ON route_stops(route_id);

CREATE INDEX IF NOT EXISTS idx_services_route
ON services(route_id);

CREATE INDEX IF NOT EXISTS idx_services_date
ON services(journey_date);

CREATE INDEX IF NOT EXISTS idx_fares_route
ON fares(route_id);

CREATE INDEX IF NOT EXISTS idx_schemes_category
ON schemes(passenger_category);

CREATE INDEX IF NOT EXISTS idx_tickets_pnr
ON tickets(pnr);

CREATE INDEX IF NOT EXISTS idx_tickets_travel_date
ON tickets(travel_date);


-- ==========================================================
-- 19. SEARCH VIEW
-- ==========================================================

CREATE VIEW IF NOT EXISTS route_search_view AS
SELECT
    r.route_id,
    r.route_code,
    r.route_number,
    r.route_name,

    src.stop_name AS source,
    dst.stop_name AS destination,

    r.total_distance_km,
    r.estimated_duration_minutes,

    o.operator_name,

    r.route_type,
    r.active

FROM routes r

LEFT JOIN stops src
    ON src.stop_id = r.source_stop_id

LEFT JOIN stops dst
    ON dst.stop_id = r.destination_stop_id

LEFT JOIN operators o
    ON o.operator_id = r.operator_id;


-- ==========================================================
-- 20. SERVICE SEARCH VIEW
-- ==========================================================

CREATE VIEW IF NOT EXISTS service_search_view AS
SELECT
    s.service_id,
    s.service_code,

    r.route_code,
    r.route_number,
    r.route_name,

    src.stop_name AS source,
    dst.stop_name AS destination,

    s.service_class,
    s.departure_time,
    s.arrival_time,

    s.journey_date,

    s.total_seats,
    s.available_seats,

    o.operator_name,

    s.live_status

FROM services s

JOIN routes r
    ON r.route_id = s.route_id

JOIN stops src
    ON src.stop_id = r.source_stop_id

JOIN stops dst
    ON dst.stop_id = r.destination_stop_id

LEFT JOIN operators o
    ON o.operator_id = (
        SELECT operator_id
        FROM buses
        WHERE buses.bus_id = s.bus_id
    );


"""


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database() -> None:

    with get_connection() as connection:
        connection.executescript(SCHEMA)

    print(f"Database ready: {DB_FILE.resolve()}")


# ============================================================
# 38 TAMIL NADU DISTRICTS
# ============================================================

DISTRICTS = [
    ("TN01", "Ariyalur"),
    ("TN02", "Chengalpattu"),
    ("TN03", "Chennai"),
    ("TN04", "Coimbatore"),
    ("TN05", "Cuddalore"),
    ("TN06", "Dharmapuri"),
    ("TN07", "Dindigul"),
    ("TN08", "Erode"),
    ("TN09", "Kallakurichi"),
    ("TN10", "Kancheepuram"),
    ("TN11", "Karur"),
    ("TN12", "Krishnagiri"),
    ("TN13", "Madurai"),
    ("TN14", "Mayiladuthurai"),
    ("TN15", "Nagapattinam"),
    ("TN16", "Kanniyakumari"),
    ("TN17", "Namakkal"),
    ("TN18", "Perambalur"),
    ("TN19", "Pudukkottai"),
    ("TN20", "Ramanathapuram"),
    ("TN21", "Ranipet"),
    ("TN22", "Salem"),
    ("TN23", "Sivaganga"),
    ("TN24", "Tenkasi"),
    ("TN25", "Thanjavur"),
    ("TN26", "Theni"),
    ("TN27", "Thoothukudi"),
    ("TN28", "Tiruchirappalli"),
    ("TN29", "Tirunelveli"),
    ("TN30", "Tirupathur"),
    ("TN31", "Tiruppur"),
    ("TN32", "Tiruvallur"),
    ("TN33", "Tiruvannamalai"),
    ("TN34", "The Nilgiris"),
    ("TN35", "Vellore"),
    ("TN36", "Viluppuram"),
    ("TN37", "Virudhunagar"),
]


# ============================================================
# INSERT DISTRICTS
# ============================================================

def seed_districts() -> None:

    with get_connection() as connection:

        connection.executemany(
            """
            INSERT OR IGNORE INTO districts
            (
                district_code,
                district_name
            )
            VALUES (?, ?)
            """,
            DISTRICTS
        )

    print(f"Loaded {len(DISTRICTS)} districts.")


# ============================================================
# OPERATORS
# ============================================================

OPERATORS = [
    (
        "MTC",
        "Metropolitan Transport Corporation",
        "MTC",
        "Tamil Nadu",
        1
    ),
    (
        "SETC",
        "State Express Transport Corporation",
        "SETC",
        "Tamil Nadu",
        1
    ),
    (
        "TNSTC-VPM",
        "TNSTC Villupuram",
        "TNSTC",
        "Tamil Nadu",
        1
    ),
    (
        "TNSTC-SLM",
        "TNSTC Salem",
        "TNSTC",
        "Tamil Nadu",
        1
    ),
    (
        "TNSTC-CBE",
        "TNSTC Coimbatore",
        "TNSTC",
        "Tamil Nadu",
        1
    ),
    (
        "TNSTC-MDU",
        "TNSTC Madurai",
        "TNSTC",
        "Tamil Nadu",
        1
    ),
    (
        "TNSTC-KUM",
        "TNSTC Kumbakonam",
        "TNSTC",
        "Tamil Nadu",
        1
    ),
    (
        "TNSTC-TNV",
        "TNSTC Tirunelveli",
        "TNSTC",
        "Tamil Nadu",
        1
    ),
    (
        "PRIVATE",
        "Private Bus Operator",
        "PRIVATE",
        "India",
        0
    ),
]


def seed_operators() -> None:

    with get_connection() as connection:

        connection.executemany(
            """
            INSERT OR IGNORE INTO operators
            (
                operator_code,
                operator_name,
                operator_type,
                state_name,
                booking_enabled
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            OPERATORS
        )

    print(f"Loaded {len(OPERATORS)} operators.")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_id(
    table: str,
    id_column: str,
    lookup_column: str,
    value: str
) -> Optional[int]:

    allowed_tables = {
        "districts",
        "localities",
        "bus_stands",
        "stops",
        "operators",
        "routes",
        "schemes",
        "services"
    }

    if table not in allowed_tables:
        raise ValueError("Invalid table name")

    query = f"""
        SELECT {id_column}
        FROM {table}
        WHERE {lookup_column} = ?
        LIMIT 1
    """

    with get_connection() as connection:

        row = connection.execute(
            query,
            (value,)
        ).fetchone()

    return row[0] if row else None


# ============================================================
# ADD LOCALITY
# ============================================================

def add_locality(
    district_name: str,
    locality_code: str,
    locality_name: str,
    locality_type: str,
    pincode: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> int:

    with get_connection() as connection:

        district = connection.execute(
            """
            SELECT district_id
            FROM districts
            WHERE district_name = ?
            """,
            (district_name,)
        ).fetchone()

        if district is None:
            raise ValueError(
                f"District not found: {district_name}"
            )

        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO localities
            (
                district_id,
                locality_code,
                locality_name,
                locality_type,
                pincode,
                latitude,
                longitude
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                district["district_id"],
                locality_code,
                locality_name,
                locality_type,
                pincode,
                latitude,
                longitude
            )
        )

        if cursor.lastrowid:
            return cursor.lastrowid

        row = connection.execute(
            """
            SELECT locality_id
            FROM localities
            WHERE locality_code = ?
            """,
            (locality_code,)
        ).fetchone()

        return row["locality_id"]


# ============================================================
# ADD BUS STAND
# ============================================================

def add_bus_stand(
    locality_code: str,
    bus_stand_code: str,
    bus_stand_name: str,
    bus_stand_type: str,
    address: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    bus_bays: int = 0
) -> int:

    with get_connection() as connection:

        locality = connection.execute(
            """
            SELECT locality_id
            FROM localities
            WHERE locality_code = ?
            """,
            (locality_code,)
        ).fetchone()

        if locality is None:
            raise ValueError(
                f"Locality not found: {locality_code}"
            )

        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO bus_stands
            (
                locality_id,
                bus_stand_code,
                bus_stand_name,
                bus_stand_type,
                address,
                latitude,
                longitude,
                bus_bays
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                locality["locality_id"],
                bus_stand_code,
                bus_stand_name,
                bus_stand_type,
                address,
                latitude,
                longitude,
                bus_bays
            )
        )

        if cursor.lastrowid:
            return cursor.lastrowid

        row = connection.execute(
            """
            SELECT bus_stand_id
            FROM bus_stands
            WHERE bus_stand_code = ?
            """,
            (bus_stand_code,)
        ).fetchone()

        return row["bus_stand_id"]


# ============================================================
# ADD STOP
# ============================================================

def add_stop(
    locality_code: str,
    stop_code: str,
    stop_name: str,
    stop_type: str,
    bus_stand_code: Optional[str] = None,
    landmark: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> int:

    with get_connection() as connection:

        locality = connection.execute(
            """
            SELECT locality_id
            FROM localities
            WHERE locality_code = ?
            """,
            (locality_code,)
        ).fetchone()

        if locality is None:
            raise ValueError(
                f"Locality not found: {locality_code}"
            )

        bus_stand_id = None

        if bus_stand_code:

            bus_stand = connection.execute(
                """
                SELECT bus_stand_id
                FROM bus_stands
                WHERE bus_stand_code = ?
                """,
                (bus_stand_code,)
            ).fetchone()

            if bus_stand:
                bus_stand_id = bus_stand["bus_stand_id"]

        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO stops
            (
                bus_stand_id,
                locality_id,
                stop_code,
                stop_name,
                stop_type,
                landmark,
                latitude,
                longitude
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bus_stand_id,
                locality["locality_id"],
                stop_code,
                stop_name,
                stop_type,
                landmark,
                latitude,
                longitude
            )
        )

        if cursor.lastrowid:
            return cursor.lastrowid

        row = connection.execute(
            """
            SELECT stop_id
            FROM stops
            WHERE stop_code = ?
            """,
            (stop_code,)
        ).fetchone()

        return row["stop_id"]


# ============================================================
# ADD ROUTE
# ============================================================

def add_route(
    route_code: str,
    route_number: str,
    route_name: str,
    source_stop_code: str,
    destination_stop_code: str,
    operator_code: Optional[str] = None,
    distance_km: Optional[float] = None,
    duration_minutes: Optional[int] = None,
    route_type: str = "INTERCITY"
) -> int:

    with get_connection() as connection:

        source = connection.execute(
            """
            SELECT stop_id
            FROM stops
            WHERE stop_code = ?
            """,
            (source_stop_code,)
        ).fetchone()

        destination = connection.execute(
            """
            SELECT stop_id
            FROM stops
            WHERE stop_code = ?
            """,
            (destination_stop_code,)
        ).fetchone()

        if source is None:
            raise ValueError(
                f"Source stop not found: {source_stop_code}"
            )

        if destination is None:
            raise ValueError(
                f"Destination stop not found: {destination_stop_code}"
            )

        operator_id = None

        if operator_code:

            operator = connection.execute(
                """
                SELECT operator_id
                FROM operators
                WHERE operator_code = ?
                """,
                (operator_code,)
            ).fetchone()

            if operator:
                operator_id = operator["operator_id"]

        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO routes
            (
                route_code,
                route_number,
                route_name,
                operator_id,
                source_stop_id,
                destination_stop_id,
                total_distance_km,
                estimated_duration_minutes,
                route_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                route_code,
                route_number,
                route_name,
                operator_id,
                source["stop_id"],
                destination["stop_id"],
                distance_km,
                duration_minutes,
                route_type
            )
        )

        if cursor.lastrowid:
            return cursor.lastrowid

        row = connection.execute(
            """
            SELECT route_id
            FROM routes
            WHERE route_code = ?
            """,
            (route_code,)
        ).fetchone()

        return row["route_id"]


# ============================================================
# ADD ROUTE STOP
# ============================================================

def add_route_stop(
    route_code: str,
    stop_code: str,
    sequence: int,
    distance_from_origin_km: float = 0,
    arrival_offset_minutes: int = 0,
    departure_offset_minutes: int = 0
) -> None:

    with get_connection() as connection:

        route = connection.execute(
            """
            SELECT route_id
            FROM routes
            WHERE route_code = ?
            """,
            (route_code,)
        ).fetchone()

        stop = connection.execute(
            """
            SELECT stop_id
            FROM stops
            WHERE stop_code = ?
            """,
            (stop_code,)
        ).fetchone()

        if route is None:
            raise ValueError(
                f"Route not found: {route_code}"
            )

        if stop is None:
            raise ValueError(
                f"Stop not found: {stop_code}"
            )

        connection.execute(
            """
            INSERT OR REPLACE INTO route_stops
            (
                route_id,
                stop_id,
                stop_sequence,
                distance_from_origin_km,
                arrival_offset_minutes,
                departure_offset_minutes
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                route["route_id"],
                stop["stop_id"],
                sequence,
                distance_from_origin_km,
                arrival_offset_minutes,
                departure_offset_minutes
            )
        )


# ============================================================
# ADD SCHEME
# ============================================================

def add_scheme(
    scheme_code: str,
    scheme_name: str,
    scheme_type: str,
    passenger_category: str,
    discount_percent: float = 0,
    fixed_discount: float = 0,
    zero_fare: bool = False,
    eligibility_description: Optional[str] = None,
    required_document: Optional[str] = None,
    effective_from: Optional[str] = None,
    effective_to: Optional[str] = None,
    source_reference: Optional[str] = None
) -> int:

    with get_connection() as connection:

        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO schemes
            (
                scheme_code,
                scheme_name,
                scheme_type,
                passenger_category,
                discount_percent,
                fixed_discount,
                zero_fare,
                eligibility_description,
                required_document,
                effective_from,
                effective_to,
                source_reference
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scheme_code,
                scheme_name,
                scheme_type,
                passenger_category,
                discount_percent,
                fixed_discount,
                int(zero_fare),
                eligibility_description,
                required_document,
                effective_from,
                effective_to,
                source_reference
            )
        )

        if cursor.lastrowid:
            return cursor.lastrowid

        row = connection.execute(
            """
            SELECT scheme_id
            FROM schemes
            WHERE scheme_code = ?
            """,
            (scheme_code,)
        ).fetchone()

        return row["scheme_id"]


# ============================================================
# FARE CALCULATION
# ============================================================

def calculate_fare(
    distance_km: float,
    rate_per_km: float,
    base_fare: float = 0,
    minimum_fare: float = 0,
    maximum_fare: Optional[float] = None,
    multiplier: float = 1.0
) -> float:

    fare = base_fare + (
        distance_km * rate_per_km
    )

    fare *= multiplier

    fare = max(
        fare,
        minimum_fare
    )

    if maximum_fare is not None:
        fare = min(
            fare,
            maximum_fare
        )

    return round(fare, 2)


# ============================================================
# APPLY SCHEME
# ============================================================

def apply_scheme(
    base_fare: float,
    scheme_code: Optional[str]
) -> tuple[float, float]:

    if not scheme_code:
        return base_fare, 0.0

    with get_connection() as connection:

        scheme = connection.execute(
            """
            SELECT *
            FROM schemes
            WHERE scheme_code = ?
              AND active = 1
            """,
            (scheme_code,)
        ).fetchone()

    if scheme is None:
        return base_fare, 0.0

    if scheme["zero_fare"]:
        return 0.0, base_fare

    discount = 0.0

    if scheme["discount_percent"]:
        discount += (
            base_fare *
            scheme["discount_percent"] /
            100
        )

    if scheme["fixed_discount"]:
        discount += scheme["fixed_discount"]

    discount = min(
        discount,
        base_fare
    )

    final_fare = round(
        base_fare - discount,
        2
    )

    return final_fare, round(discount, 2)


# ============================================================
# SEARCH ROUTES
# ============================================================

def search_routes(
    source: str,
    destination: str
) -> list[sqlite3.Row]:

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT *
            FROM route_search_view
            WHERE LOWER(source) LIKE LOWER(?)
              AND LOWER(destination) LIKE LOWER(?)
              AND active = 1
            ORDER BY route_name
            """,
            (
                f"%{source}%",
                f"%{destination}%"
            )
        ).fetchall()

    return rows


# ============================================================
# SEARCH SERVICES
# ============================================================

def search_services(
    source: str,
    destination: str,
    travel_date: Optional[str] = None
) -> list[sqlite3.Row]:

    query = """
        SELECT *
        FROM service_search_view
        WHERE LOWER(source) LIKE LOWER(?)
          AND LOWER(destination) LIKE LOWER(?)
          AND live_status != 'CANCELLED'
    """

    parameters = [
        f"%{source}%",
        f"%{destination}%"
    ]

    if travel_date:

        query += """
            AND (
                journey_date = ?
                OR journey_date IS NULL
            )
        """

        parameters.append(travel_date)

    query += """
        ORDER BY departure_time
    """

    with get_connection() as connection:

        return connection.execute(
            query,
            parameters
        ).fetchall()


# ============================================================
# DISPLAY ROUTES
# ============================================================

def print_routes(rows: list[sqlite3.Row]) -> None:

    if not rows:
        print("No routes found.")
        return

    print()
    print("=" * 100)
    print(
        f"{'CODE':<12}"
        f"{'ROUTE':<25}"
        f"{'FROM':<20}"
        f"{'TO':<20}"
        f"{'KM':<8}"
    )
    print("=" * 100)

    for row in rows:

        print(
            f"{row['route_code']:<12}"
            f"{row['route_name'][:24]:<25}"
            f"{row['source'][:19]:<20}"
            f"{row['destination'][:19]:<20}"
            f"{str(row['total_distance_km'] or ''):<8}"
        )

    print("=" * 100)


# ============================================================
# SEED DEMO DATA
# ============================================================

def seed_demo_data() -> None:

    # --------------------------------------------------------
    # ERODE
    # --------------------------------------------------------

    add_locality(
        "Erode",
        "ERD-CITY",
        "Erode",
        "CITY",
        "638001"
    )

    add_bus_stand(
        "ERD-CITY",
        "ERD-BS",
        "Erode Bus Stand",
        "CENTRAL",
        "Erode",
        bus_bays=20
    )

    add_stop(
        "ERD-CITY",
        "ERD-BS-STOP",
        "Erode Bus Stand",
        "BUS_STAND",
        "ERD-BS"
    )

    # --------------------------------------------------------
    # COIMBATORE
    # --------------------------------------------------------

    add_locality(
        "Coimbatore",
        "CBE-CITY",
        "Coimbatore",
        "CITY",
        "641001"
    )

    add_bus_stand(
        "CBE-CITY",
        "CBE-GANDHIPURAM",
        "Gandhipuram Bus Stand",
        "CENTRAL",
        "Gandhipuram, Coimbatore",
        bus_bays=30
    )

    add_stop(
        "CBE-CITY",
        "CBE-GAN-STOP",
        "Gandhipuram Bus Stand",
        "BUS_STAND",
        "CBE-GANDHIPURAM"
    )

    # --------------------------------------------------------
    # ROUTE R12
    # --------------------------------------------------------

    add_route(
        route_code="R12",
        route_number="R12",
        route_name="Erode - Coimbatore",
        source_stop_code="ERD-BS-STOP",
        destination_stop_code="CBE-GAN-STOP",
        operator_code="TNSTC-CBE",
        distance_km=100.0,
        duration_minutes=180,
        route_type="INTERCITY"
    )

    add_route_stop(
        "R12",
        "ERD-BS-STOP",
        1,
        0.0,
        0,
        0
    )

    add_route_stop(
        "R12",
        "CBE-GAN-STOP",
        2,
        100.0,
        180,
        180
    )

    # --------------------------------------------------------
    # SPECIAL CHALLENGE BUS
    # --------------------------------------------------------

    with get_connection() as connection:

        operator = connection.execute(
            """
            SELECT operator_id
            FROM operators
            WHERE operator_code = 'TNSTC-CBE'
            """
        ).fetchone()

        connection.execute(
            """
            INSERT OR IGNORE INTO buses
            (
                bus_code,
                registration_number,
                operator_id,
                route_number,
                bus_type,
                capacity,
                available_seats,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "BUS101",
                "TN-XX-0000",
                operator["operator_id"],
                "R12",
                "ORDINARY",
                50,
                8,
                "RUNNING"
            )
        )

    # --------------------------------------------------------
    # DRIVER
    # --------------------------------------------------------

    with get_connection() as connection:

        connection.execute(
            """
            INSERT OR IGNORE INTO drivers
            (
                driver_code,
                driver_name
            )
            VALUES (?, ?)
            """,
            (
                "DRV101",
                "Demo Driver"
            )
        )

    # --------------------------------------------------------
    # SERVICE
    # --------------------------------------------------------

    with get_connection() as connection:

        route = connection.execute(
            """
            SELECT route_id
            FROM routes
            WHERE route_code = 'R12'
            """
        ).fetchone()

        bus = connection.execute(
            """
            SELECT bus_id
            FROM buses
            WHERE bus_code = 'BUS101'
            """
        ).fetchone()

        driver = connection.execute(
            """
            SELECT driver_id
            FROM drivers
            WHERE driver_code = 'DRV101'
            """
        ).fetchone()

        connection.execute(
            """
            INSERT OR IGNORE INTO services
            (
                service_code,
                route_id,
                bus_id,
                driver_id,
                service_name,
                service_class,
                departure_time,
                arrival_time,
                journey_date,
                total_seats,
                available_seats,
                live_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "SVC-R12-001",
                route["route_id"],
                bus["bus_id"],
                driver["driver_id"],
                "Erode - Coimbatore Express",
                "EXPRESS",
                "06:00",
                "09:00",
                None,
                50,
                8,
                "SCHEDULED"
            )
        )

    # --------------------------------------------------------
    # SCHEMES
    # --------------------------------------------------------

    add_scheme(
        scheme_code="WOMAN-ZERO",
        scheme_name="Women Zero Fare Travel",
        scheme_type="FREE_TRAVEL",
        passenger_category="WOMAN",
        zero_fare=True,
        eligibility_description=(
            "Eligible women passenger subject to applicable "
            "government/operator rules."
        ),
        required_document="Aadhaar / PDS",
        source_reference="TNSTC official Zero Fare Travel"
    )

    add_scheme(
        scheme_code="GENERAL",
        scheme_name="General Passenger",
        scheme_type="CONCESSION",
        passenger_category="GENERAL",
        source_reference="Standard fare"
    )

    add_scheme(
        scheme_code="STUDENT",
        scheme_name="Student Concession",
        scheme_type="CONCESSION",
        passenger_category="STUDENT",
        discount_percent=50,
        eligibility_description=(
            "Use only where applicable to the relevant "
            "operator/service and valid student eligibility."
        ),
        required_document="Student ID / Pass",
        source_reference="Operator/Government scheme"
    )

    add_scheme(
        scheme_code="SENIOR",
        scheme_name="Senior Citizen",
        scheme_type="CONCESSION",
        passenger_category="SENIOR_CITIZEN",
        eligibility_description=(
            "Eligibility must be checked against the "
            "applicable operator/pass rules."
        ),
        required_document="Age Proof",
        source_reference="Operator/Government scheme"
    )

    print("Demo master data loaded.")


# ============================================================
# DATABASE REPORT
# ============================================================

def database_report() -> None:

    tables = [
        "districts",
        "localities",
        "bus_stands",
        "stops",
        "operators",
        "buses",
        "drivers",
        "routes",
        "route_stops",
        "services",
        "fares",
        "fare_stages",
        "schemes",
        "scheme_rules",
        "passengers",
        "tickets",
        "ticket_passengers"
    ]

    print()
    print("=" * 60)
    print("SMART BUS DATABASE REPORT")
    print("=" * 60)

    with get_connection() as connection:

        for table in tables:

            row = connection.execute(
                f"SELECT COUNT(*) AS total FROM {table}"
            ).fetchone()

            print(
                f"{table:<25} {row['total']:>8}"
            )

    print("=" * 60)


# ============================================================
# SHOW ROUTE
# ============================================================

def show_route(route_code: str) -> None:

    with get_connection() as connection:

        route = connection.execute(
            """
            SELECT
                r.route_code,
                r.route_number,
                r.route_name,
                r.total_distance_km,
                r.estimated_duration_minutes,
                o.operator_name
            FROM routes r
            LEFT JOIN operators o
                ON o.operator_id = r.operator_id
            WHERE r.route_code = ?
            """,
            (route_code,)
        ).fetchone()

        if route is None:
            print("Route not found.")
            return

        print()
        print("=" * 70)
        print(f"Route: {route['route_name']}")
        print(f"Route Code: {route['route_code']}")
        print(f"Route Number: {route['route_number']}")
        print(f"Operator: {route['operator_name']}")
        print(f"Distance: {route['total_distance_km']} km")
        print(
            f"Duration: "
            f"{route['estimated_duration_minutes']} minutes"
        )
        print("=" * 70)

        stops = connection.execute(
            """
            SELECT
                rs.stop_sequence,
                s.stop_code,
                s.stop_name,
                rs.distance_from_origin_km,
                rs.arrival_offset_minutes
            FROM route_stops rs
            JOIN stops s
                ON s.stop_id = rs.stop_id
            JOIN routes r
                ON r.route_id = rs.route_id
            WHERE r.route_code = ?
            ORDER BY rs.stop_sequence
            """,
            (route_code,)
        ).fetchall()

        for stop in stops:

            print(
                f"{stop['stop_sequence']:>3}. "
                f"{stop['stop_name']:<35} "
                f"{stop['distance_from_origin_km']:>7.1f} km"
            )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print()
    print("=" * 70)
    print("SMART BUS - MASTER DATABASE")
    print("Python 3.13 + SQLite")
    print("=" * 70)

    initialize_database()

    seed_districts()
    seed_operators()
    seed_demo_data()

    database_report()

    print()
    print("Sample route:")
    show_route("R12")

    print()
    print("Searching Erode -> Coimbatore:")
    rows = search_routes(
        "Erode",
        "Coimbatore"
    )

    print_routes(rows)

    print()
    print("Database initialization completed.")
    print(f"File: {DB_FILE.resolve()}")


if __name__ == "__main__":
    main()
