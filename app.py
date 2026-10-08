# ============================================================
# SMART BUS
# BUS ROUTE AND PASSENGER MANAGEMENT SYSTEM
# Tamil Nadu Government Bus Management System
#
# Python 3.13
# Streamlit
#
# Run:
# streamlit run app.py
# ============================================================

import streamlit as st
import sqlite3
import pandas as pd
import json
import hashlib
import random
import string
from datetime import datetime, date
from pathlib import Path

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="SMART BUS - Bus Route and Passenger Management System",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CONSTANTS
# ============================================================

DB_FILE = "smart_bus.db"

TNSTC_CORPORATIONS = [
    "MTC",
    "SETC",
    "TNSTC Villupuram",
    "TNSTC Salem",
    "TNSTC Coimbatore",
    "TNSTC Madurai",
    "TNSTC Kumbakonam",
    "TNSTC Tirunelveli"
]

BUS_TYPES = [
    "Ordinary",
    "Express",
    "Super Deluxe",
    "Ultra Deluxe",
    "Semi Deluxe",
    "Semi Luxury",
    "Luxury",
    "Classic",
    "Low Floor",
    "Semi Low Floor",
    "AC",
    "AC Seater",
    "AC Sleeper",
    "AC Seater Cum Sleeper",
    "Non AC Sleeper",
    "Non AC Seater Cum Sleeper",
    "Volvo AC",
    "Volvo Multi Axle AC Semi Sleeper",
    "Town Bus",
    "Ghat Service",
    "Night Service",
    "Interstate Service"
]

BUS_STATUS = [
    "Running",
    "Scheduled",
    "Stopped",
    "Under Maintenance",
    "Cancelled",
    "Spare"
]

# Historical official TNSTC tariff rules.
# These are NOT silently presented as live route fares.
# Exact route/service fare should be entered from the official
# booking/service result when available.
OFFICIAL_FARE_RULES = {
    "Ordinary": {
        "rate": 0.58,
        "minimum": 7.00,
        "source": "TNSTC published fare table"
    },
    "Express": {
        "rate": 0.75,
        "minimum": 10.00,
        "source": "TNSTC published fare table"
    },
    "Semi Luxury": {
        "rate": 0.85,
        "minimum": 9.00,
        "source": "TNSTC published fare table"
    },
    "Super Deluxe": {
        "rate": 0.85,
        "minimum": 15.00,
        "source": "TNSTC published fare table"
    },
    "Ultra Deluxe": {
        "rate": 1.00,
        "minimum": 15.00,
        "source": "TNSTC published fare table"
    },
    "AC": {
        "rate": 1.09,
        "minimum": 10.00,
        "source": "TNSTC published fare table"
    },
    "Classic": {
        "rate": 1.15,
        "minimum": 15.00,
        "source": "TNSTC published SETC fare table"
    },
    "AC Sleeper": {
        "rate": 1.80,
        "minimum": 20.00,
        "source": "TNSTC published SETC fare table"
    },
    "Non AC Sleeper": {
        "rate": 1.35,
        "minimum": 15.00,
        "source": "TNSTC published SETC fare table"
    },
    "AC Seater Cum Sleeper": {
        "rate": 1.30,
        "minimum": 20.00,
        "source": "TNSTC published SETC fare table"
    },
    "Non AC Seater Cum Sleeper": {
        "rate": 1.35,
        "minimum": 15.00,
        "source": "TNSTC published SETC fare table"
    }
}

OFFICIAL_TNSTC_URL = "https://www.tnstc.in/OTRSOnline/"
OFFICIAL_BUS_SEARCH_URL = "https://www.tnstc.in/booking/"
OFFICIAL_KNOW_BUS_URL = "https://www.tnstc.in/OTRSOnline/preKnowYourConductor.do"

# ============================================================
# DATABASE
# ============================================================

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def create_database():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS buses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bus_id TEXT UNIQUE NOT NULL,
            registration_no TEXT,
            corporation TEXT,
            bus_type TEXT,
            route_no TEXT,
            driver TEXT,
            capacity INTEGER,
            available_seats INTEGER,
            status TEXT,
            source TEXT,
            verified INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_no TEXT UNIQUE NOT NULL,
            source_place TEXT NOT NULL,
            destination TEXT NOT NULL,
            stops TEXT,
            distance_km REAL,
            corporation TEXT,
            verified INTEGER DEFAULT 0,
            source TEXT,
            updated_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_id TEXT UNIQUE NOT NULL,
            route_no TEXT,
            bus_id TEXT,
            bus_type TEXT,
            departure TEXT,
            arrival TEXT,
            distance_km REAL,
            fare REAL,
            fare_status TEXT,
            source TEXT,
            verified INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS passengers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pnr TEXT UNIQUE NOT NULL,
            passenger_name TEXT,
            age INTEGER,
            gender TEXT,
            phone TEXT,
            source_place TEXT,
            destination TEXT,
            route_no TEXT,
            bus_id TEXT,
            service_type TEXT,
            seats TEXT,
            seat_count INTEGER,
            fare REAL,
            booking_status TEXT,
            booked_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS fare_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_no TEXT,
            source_place TEXT,
            destination TEXT,
            bus_type TEXT,
            distance_km REAL,
            fare REAL,
            fare_status TEXT,
            source TEXT,
            verified_date TEXT
        )
    """)

    conn.commit()
    conn.close()


create_database()

# ============================================================
# DATABASE HELPERS
# ============================================================

def db_execute(query, params=()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    result = cur.lastrowid
    conn.close()
    return result


def db_query(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def db_scalar(query, params=()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    result = cur.fetchone()
    conn.close()

    if result:
        return result[0]

    return None


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def generate_pnr():
    while True:
        pnr = "TN" + "".join(
            random.choices(string.digits, k=8)
        )

        exists = db_scalar(
            "SELECT COUNT(*) FROM passengers WHERE pnr=?",
            (pnr,)
        )

        if not exists:
            return pnr


def generate_service_id():
    return "SRV" + "".join(
        random.choices(string.digits, k=7)
    )


def generate_bus_id():
    while True:
        bus_id = "BUS" + "".join(
            random.choices(string.digits, k=3)
        )

        exists = db_scalar(
            "SELECT COUNT(*) FROM buses WHERE bus_id=?",
            (bus_id,)
        )

        if not exists:
            return bus_id


def calculate_hash(text):
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()[:16].upper()


def normalize_place(value):
    return " ".join(
        str(value).strip().upper().split()
    )


def get_route(source, destination):
    source = normalize_place(source)
    destination = normalize_place(destination)

    return db_query(
        """
        SELECT *
        FROM routes
        WHERE UPPER(source_place)=?
        AND UPPER(destination)=?
        """,
        (source, destination)
    )


def get_route_by_number(route_no):
    return db_query(
        """
        SELECT *
        FROM routes
        WHERE UPPER(route_no)=?
        """,
        (str(route_no).strip().upper(),)
    )


# ============================================================
# FARE ENGINE
# ============================================================

def get_exact_fare(
    route_no,
    source,
    destination,
    bus_type
):
    source = normalize_place(source)
    destination = normalize_place(destination)

    df = db_query(
        """
        SELECT *
        FROM fare_master
        WHERE
            (
                UPPER(route_no)=?
                OR route_no IS NULL
                OR route_no=''
            )
            AND UPPER(source_place)=?
            AND UPPER(destination)=?
            AND UPPER(bus_type)=?
            AND fare_status='VERIFIED'
        ORDER BY id DESC
        LIMIT 1
        """,
        (
            str(route_no).strip().upper(),
            source,
            destination,
            str(bus_type).strip().upper()
        )
    )

    if not df.empty:
        return {
            "fare": float(df.iloc[0]["fare"]),
            "distance": float(df.iloc[0]["distance_km"]),
            "status": "VERIFIED",
            "source": df.iloc[0]["source"]
        }

    return None


def calculate_estimated_fare(
    distance_km,
    bus_type
):
    rule = OFFICIAL_FARE_RULES.get(
        bus_type,
        OFFICIAL_FARE_RULES["Ordinary"]
    )

    distance_km = max(
        0,
        float(distance_km)
    )

    calculated = distance_km * rule["rate"]

    fare = max(
        calculated,
        rule["minimum"]
    )

    return round(fare, 2)


def calculate_fare(
    route_no,
    source,
    destination,
    bus_type,
    distance_km
):
    exact = get_exact_fare(
        route_no,
        source,
        destination,
        bus_type
    )

    if exact:
        return exact

    fare = calculate_estimated_fare(
        distance_km,
        bus_type
    )

    return {
        "fare": fare,
        "distance": float(distance_km),
        "status": "ESTIMATED",
        "source": "Published TNSTC tariff rule"
    }


# ============================================================
# SEED DATA
# ============================================================

def seed_demo_data():

    count = db_scalar(
        "SELECT COUNT(*) FROM buses"
    )

    if count == 0:

        demo_buses = [
            (
                "BUS101",
                "TN 33 N 0101",
                "TNSTC Coimbatore",
                "Express",
                "R12",
                "Government Driver",
                50,
                50,
                "Running",
                "Project Master",
                0
            ),
            (
                "BUS102",
                "TN 38 N 0102",
                "TNSTC Salem",
                "Ordinary",
                "R21",
                "Government Driver",
                52,
                52,
                "Scheduled",
                "Project Master",
                0
            ),
            (
                "BUS103",
                "TN 57 N 0103",
                "TNSTC Madurai",
                "Super Deluxe",
                "R31",
                "Government Driver",
                48,
                48,
                "Running",
                "Project Master",
                0
            ),
            (
                "BUS104",
                "TN 72 N 0104",
                "TNSTC Tirunelveli",
                "Ultra Deluxe",
                "R41",
                "Government Driver",
                48,
                48,
                "Running",
                "Project Master",
                0
            ),
            (
                "BUS105",
                "TN 01 N 0105",
                "MTC",
                "Town Bus",
                "M1",
                "Government Driver",
                50,
                50,
                "Running",
                "Project Master",
                0
            ),
            (
                "BUS106",
                "TN 01 N 0106",
                "SETC",
                "Volvo Multi Axle AC Semi Sleeper",
                "S1",
                "Government Driver",
                40,
                40,
                "Scheduled",
                "Project Master",
                0
            )
        ]

        for row in demo_buses:
            db_execute(
                """
                INSERT INTO buses
                (
                    bus_id,
                    registration_no,
                    corporation,
                    bus_type,
                    route_no,
                    driver,
                    capacity,
                    available_seats,
                    status,
                    source,
                    verified
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                row
            )


seed_demo_data()

# ============================================================
# SESSION STATE
# ============================================================

if "selected_bus" not in st.session_state:
    st.session_state.selected_bus = None

if "selected_route" not in st.session_state:
    st.session_state.selected_route = None


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.main-header {
    background: linear-gradient(
        135deg,
        #0b1f3a,
        #173f68
    );
    padding: 28px;
    border-radius: 14px;
    margin-bottom: 20px;
    border: 1px solid #d4af37;
}

.main-title {
    font-size: 32px;
    font-weight: 800;
    color: white;
}

.main-subtitle {
    color: #dbeafe;
    font-size: 15px;
    margin-top: 5px;
}

.card {
    background: #ffffff;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #dbe3ec;
    box-shadow: 0 3px 10px rgba(0,0,0,0.06);
}

.metric-card {
    background: #f8fafc;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    text-align: center;
}

.metric-number {
    font-size: 28px;
    font-weight: 800;
    color: #123b63;
}

.metric-label {
    color: #64748b;
    font-size: 13px;
}

.verified {
    color: #15803d;
    font-weight: 700;
}

.estimated {
    color: #b45309;
    font-weight: 700;
}

.status-running {
    color: #15803d;
    font-weight: 800;
}

.status-maintenance {
    color: #b45309;
    font-weight: 800;
}

.status-stopped {
    color: #dc2626;
    font-weight: 800;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="main-header">
    <div class="main-title">
        🚌 SMART BUS
    </div>
    <div class="main-subtitle">
        BUS ROUTE AND PASSENGER MANAGEMENT SYSTEM
    </div>
    <div style="color:#facc15;margin-top:8px;font-size:13px;">
        Tamil Nadu Government Bus Management Portal
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🚌 SMART BUS")

    menu = st.radio(
        "MAIN MENU",
        [
            "Dashboard",
            "Bus Management",
            "Route Management",
            "Service Management",
            "Passenger Management",
            "Fare Calculator",
            "Bus Status Report",
            "Government Bus Types",
            "Fare Master",
            "Official Sources"
        ]
    )

    st.divider()

    st.caption(
        "Tamil Nadu State Transport Corporations"
    )

    for corporation in TNSTC_CORPORATIONS:
        st.write("•", corporation)

    st.divider()

    st.caption(
        "SMART BUS Management System"
    )


# ============================================================
# DASHBOARD
# ============================================================

if menu == "Dashboard":

    buses = db_query(
        "SELECT * FROM buses"
    )

    routes = db_query(
        "SELECT * FROM routes"
    )

    services = db_query(
        "SELECT * FROM services"
    )

    passengers = db_query(
        "SELECT * FROM passengers"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-number">{len(buses)}</div>
                <div class="metric-label">BUSES</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-number">{len(routes)}</div>
                <div class="metric-label">ROUTES</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-number">{len(services)}</div>
                <div class="metric-label">SERVICES</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-number">{len(passengers)}</div>
                <div class="metric-label">PASSENGERS</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    st.subheader("🚌 Current Bus Status")

    if not buses.empty:

        status_counts = (
            buses["status"]
            .value_counts()
            .reset_index()
        )

        status_counts.columns = [
            "Status",
            "Buses"
        ]

        st.dataframe(
            status_counts,
            use_container_width=True,
            hide_index=True
        )

    st.subheader("🏢 Corporation Fleet")

    if not buses.empty:

        corporation_counts = (
            buses["corporation"]
            .value_counts()
            .reset_index()
        )

        corporation_counts.columns = [
            "Corporation",
            "Buses"
        ]

        st.dataframe(
            corporation_counts,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# BUS MANAGEMENT
# ============================================================

elif menu == "Bus Management":

    st.header("🚌 Bus Management")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Add Bus",
            "View / Search Bus",
            "Update Bus",
            "Delete Bus"
        ]
    )

    # --------------------------------------------------------
    # ADD BUS
    # --------------------------------------------------------

    with tab1:

        st.subheader("➕ Add New Government Bus")

        with st.form("add_bus_form"):

            c1, c2 = st.columns(2)

            with c1:
                bus_id = st.text_input(
                    "Bus ID",
                    value=generate_bus_id()
                )

                registration = st.text_input(
                    "Registration Number"
                )

                corporation = st.selectbox(
                    "Corporation",
                    TNSTC_CORPORATIONS
                )

                bus_type = st.selectbox(
                    "Bus Type",
                    BUS_TYPES
                )

                route_no = st.text_input(
                    "Route Number"
                )

            with c2:

                driver = st.text_input(
                    "Driver"
                )

                capacity = st.number_input(
                    "Capacity",
                    min_value=1,
                    max_value=200,
                    value=50
                )

                available = st.number_input(
                    "Available Seats",
                    min_value=0,
                    max_value=200,
                    value=50
                )

                status = st.selectbox(
                    "Status",
                    BUS_STATUS
                )

                verified = st.checkbox(
                    "Verified Government Data"
                )

            submitted = st.form_submit_button(
                "➕ ADD BUS",
                use_container_width=True
            )

        if submitted:

            if not bus_id.strip():
                st.error("Bus ID is required.")

            elif available > capacity:
                st.error(
                    "Available seats cannot exceed capacity."
                )

            else:

                try:

                    db_execute(
                        """
                        INSERT INTO buses
                        (
                            bus_id,
                            registration_no,
                            corporation,
                            bus_type,
                            route_no,
                            driver,
                            capacity,
                            available_seats,
                            status,
                            source,
                            verified,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            bus_id.strip().upper(),
                            registration.strip().upper(),
                            corporation,
                            bus_type,
                            route_no.strip().upper(),
                            driver,
                            int(capacity),
                            int(available),
                            status,
                            "SMART BUS Admin",
                            int(verified),
                            datetime.now().isoformat()
                        )
                    )

                    st.success(
                        f"Bus {bus_id.upper()} added successfully."
                    )

                except sqlite3.IntegrityError:
                    st.error(
                        "Bus ID already exists."
                    )

    # --------------------------------------------------------
    # VIEW / SEARCH
    # --------------------------------------------------------

    with tab2:

        search = st.text_input(
            "🔎 Search Bus",
            placeholder="Bus ID / Registration / Route / Driver"
        )

        buses = db_query(
            "SELECT * FROM buses ORDER BY bus_id"
        )

        if search.strip():

            keyword = f"%{search.strip().upper()}%"

            buses = db_query(
                """
                SELECT *
                FROM buses
                WHERE
                    UPPER(bus_id) LIKE ?
                    OR UPPER(registration_no) LIKE ?
                    OR UPPER(route_no) LIKE ?
                    OR UPPER(driver) LIKE ?
                    OR UPPER(corporation) LIKE ?
                ORDER BY bus_id
                """,
                (
                    keyword,
                    keyword,
                    keyword,
                    keyword,
                    keyword
                )
            )

        if buses.empty:
            st.info("No buses found.")

        else:

            display = buses.copy()

            display["Verified"] = display[
                "verified"
            ].map(
                lambda x: "YES" if x else "NO"
            )

            display = display[
                [
                    "bus_id",
                    "registration_no",
                    "corporation",
                    "bus_type",
                    "route_no",
                    "driver",
                    "capacity",
                    "available_seats",
                    "status",
                    "Verified"
                ]
            ]

            display.columns = [
                "Bus ID",
                "Registration",
                "Corporation",
                "Bus Type",
                "Route",
                "Driver",
                "Capacity",
                "Available Seats",
                "Status",
                "Verified"
            ]

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True
            )

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    with tab3:

        buses = db_query(
            "SELECT bus_id FROM buses ORDER BY bus_id"
        )

        if buses.empty:

            st.info("No buses available.")

        else:

            selected = st.selectbox(
                "Select Bus",
                buses["bus_id"].tolist()
            )

            current = db_query(
                "SELECT * FROM buses WHERE bus_id=?",
                (selected,)
            )

            if not current.empty:

                row = current.iloc[0]

                with st.form("update_bus_form"):

                    c1, c2 = st.columns(2)

                    with c1:

                        registration = st.text_input(
                            "Registration Number",
                            value=str(
                                row["registration_no"] or ""
                            )
                        )

                        corporation = st.selectbox(
                            "Corporation",
                            TNSTC_CORPORATIONS,
                            index=(
                                TNSTC_CORPORATIONS.index(
                                    row["corporation"]
                                )
                                if row["corporation"]
                                in TNSTC_CORPORATIONS
                                else 0
                            )
                        )

                        bus_type = st.selectbox(
                            "Bus Type",
                            BUS_TYPES,
                            index=(
                                BUS_TYPES.index(
                                    row["bus_type"]
                                )
                                if row["bus_type"]
                                in BUS_TYPES
                                else 0
                            )
                        )

                        route_no = st.text_input(
                            "Route Number",
                            value=str(
                                row["route_no"] or ""
                            )
                        )

                    with c2:

                        driver = st.text_input(
                            "Driver",
                            value=str(
                                row["driver"] or ""
                            )
                        )

                        capacity = st.number_input(
                            "Capacity",
                            min_value=1,
                            max_value=200,
                            value=int(
                                row["capacity"]
                            )
                        )

                        available = st.number_input(
                            "Available Seats",
                            min_value=0,
                            max_value=200,
                            value=int(
                                row["available_seats"]
                            )
                        )

                        status = st.selectbox(
                            "Status",
                            BUS_STATUS,
                            index=(
                                BUS_STATUS.index(
                                    row["status"]
                                )
                                if row["status"]
                                in BUS_STATUS
                                else 0
                            )
                        )

                    update = st.form_submit_button(
                        "💾 UPDATE BUS",
                        use_container_width=True
                    )

                if update:

                    if available > capacity:
                        st.error(
                            "Available seats cannot exceed capacity."
                        )
                    else:

                        db_execute(
                            """
                            UPDATE buses
                            SET
                                registration_no=?,
                                corporation=?,
                                bus_type=?,
                                route_no=?,
                                driver=?,
                                capacity=?,
                                available_seats=?,
                                status=?
                            WHERE bus_id=?
                            """,
                            (
                                registration.strip().upper(),
                                corporation,
                                bus_type,
                                route_no.strip().upper(),
                                driver,
                                int(capacity),
                                int(available),
                                status,
                                selected
                            )
                        )

                        st.success(
                            "Bus updated successfully."
                        )

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    with tab4:

        buses = db_query(
            "SELECT bus_id FROM buses ORDER BY bus_id"
        )

        if buses.empty:

            st.info("No buses available.")

        else:

            selected_delete = st.selectbox(
                "Select Bus to Delete",
                buses["bus_id"].tolist(),
                key="delete_bus"
            )

            confirm = st.checkbox(
                "I confirm that I want to delete this bus."
            )

            if st.button(
                "🗑️ DELETE BUS",
                type="primary"
            ):

                if not confirm:

                    st.warning(
                        "Please confirm deletion."
                    )

                else:

                    db_execute(
                        "DELETE FROM buses WHERE bus_id=?",
                        (selected_delete,)
                    )

                    st.success(
                        f"{selected_delete} deleted."
                    )


# ============================================================
# ROUTE MANAGEMENT
# ============================================================

elif menu == "Route Management":

    st.header("🛣️ Route Management")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Add Route",
            "Search Route",
            "Update Route",
            "Delete Route"
        ]
    )

    with tab1:

        st.subheader("➕ Add Route")

        with st.form("route_add"):

            c1, c2 = st.columns(2)

            with c1:

                route_no = st.text_input(
                    "Route Number"
                )

                source = st.text_input(
                    "Source"
                )

                destination = st.text_input(
                    "Destination"
                )

                corporation = st.selectbox(
                    "Corporation",
                    TNSTC_CORPORATIONS
                )

            with c2:

                stops = st.text_area(
                    "Stops",
                    placeholder=(
                        "Stop 1, Stop 2, Stop 3..."
                    )
                )

                distance = st.number_input(
                    "Verified Road Distance (KM)",
                    min_value=0.0,
                    max_value=2000.0,
                    value=0.0,
                    step=1.0
                )

                verified = st.checkbox(
                    "Distance verified from official route/service data"
                )

                source_reference = st.text_input(
                    "Distance Source / Reference"
                )

            save_route = st.form_submit_button(
                "➕ ADD ROUTE",
                use_container_width=True
            )

        if save_route:

            if not route_no.strip():
                st.error("Route number is required.")

            elif not source.strip():
                st.error("Source is required.")

            elif not destination.strip():
                st.error("Destination is required.")

            elif distance <= 0:
                st.error(
                    "Enter the verified road distance."
                )

            else:

                try:

                    db_execute(
                        """
                        INSERT INTO routes
                        (
                            route_no,
                            source_place,
                            destination,
                            stops,
                            distance_km,
                            corporation,
                            verified,
                            source,
                            updated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            route_no.strip().upper(),
                            source.strip().title(),
                            destination.strip().title(),
                            stops.strip(),
                            distance,
                            corporation,
                            int(verified),
                            source_reference.strip(),
                            datetime.now().isoformat()
                        )
                    )

                    st.success(
                        "Route added successfully."
                    )

                except sqlite3.IntegrityError:

                    st.error(
                        "Route number already exists."
                    )

    with tab2:

        st.subheader("🔎 Search Route")

        c1, c2 = st.columns(2)

        with c1:
            source_search = st.text_input(
                "From"
            )

        with c2:
            destination_search = st.text_input(
                "To"
            )

        route_search = st.text_input(
            "Route Number / Stop Search"
        )

        routes = db_query(
            "SELECT * FROM routes ORDER BY route_no"
        )

        if source_search.strip():

            routes = routes[
                routes["source_place"]
                .str.contains(
                    source_search,
                    case=False,
                    na=False
                )
            ]

        if destination_search.strip():

            routes = routes[
                routes["destination"]
                .str.contains(
                    destination_search,
                    case=False,
                    na=False
                )
            ]

        if route_search.strip():

            routes = routes[
                routes["route_no"]
                .str.contains(
                    route_search,
                    case=False,
                    na=False
                )
                |
                routes["stops"]
                .str.contains(
                    route_search,
                    case=False,
                    na=False
                )
            ]

        if routes.empty:

            st.info(
                "No route data found. Add verified route data first."
            )

        else:

            result = routes.copy()

            result["Distance Status"] = result[
                "verified"
            ].map(
                lambda x:
                "VERIFIED"
                if x
                else "NOT VERIFIED"
            )

            result = result[
                [
                    "route_no",
                    "source_place",
                    "destination",
                    "stops",
                    "distance_km",
                    "corporation",
                    "Distance Status"
                ]
            ]

            result.columns = [
                "Route",
                "Source",
                "Destination",
                "Stops",
                "Distance KM",
                "Corporation",
                "Distance Status"
            ]

            st.dataframe(
                result,
                use_container_width=True,
                hide_index=True
            )

    with tab3:

        routes = db_query(
            "SELECT route_no FROM routes ORDER BY route_no"
        )

        if routes.empty:

            st.info(
                "No routes available."
            )

        else:

            selected_route = st.selectbox(
                "Select Route",
                routes["route_no"].tolist()
            )

            current = db_query(
                "SELECT * FROM routes WHERE route_no=?",
                (selected_route,)
            )

            if not current.empty:

                row = current.iloc[0]

                with st.form("route_update"):

                    source = st.text_input(
                        "Source",
                        value=row["source_place"]
                    )

                    destination = st.text_input(
                        "Destination",
                        value=row["destination"]
                    )

                    stops = st.text_area(
                        "Stops",
                        value=row["stops"] or ""
                    )

                    distance = st.number_input(
                        "Distance KM",
                        min_value=0.0,
                        value=float(
                            row["distance_km"]
                        )
                    )

                    corporation = st.selectbox(
                        "Corporation",
                        TNSTC_CORPORATIONS,
                        index=(
                            TNSTC_CORPORATIONS.index(
                                row["corporation"]
                            )
                            if row["corporation"]
                            in TNSTC_CORPORATIONS
                            else 0
                        )
                    )

                    verified = st.checkbox(
                        "Distance Verified",
                        value=bool(row["verified"])
                    )

                    source_reference = st.text_input(
                        "Source / Reference",
                        value=row["source"] or ""
                    )

                    update_route = st.form_submit_button(
                        "💾 UPDATE ROUTE",
                        use_container_width=True
                    )

                if update_route:

                    db_execute(
                        """
                        UPDATE routes
                        SET
                            source_place=?,
                            destination=?,
                            stops=?,
                            distance_km=?,
                            corporation=?,
                            verified=?,
                            source=?,
                            updated_at=?
                        WHERE route_no=?
                        """,
                        (
                            source.strip().title(),
                            destination.strip().title(),
                            stops.strip(),
                            distance,
                            corporation,
                            int(verified),
                            source_reference.strip(),
                            datetime.now().isoformat(),
                            selected_route
                        )
                    )

                    st.success(
                        "Route updated successfully."
                    )

    with tab4:

        routes = db_query(
            "SELECT route_no FROM routes ORDER BY route_no"
        )

        if routes.empty:

            st.info(
                "No routes available."
            )

        else:

            selected = st.selectbox(
                "Select Route to Delete",
                routes["route_no"].tolist(),
                key="route_delete"
            )

            confirm = st.checkbox(
                "Confirm route deletion"
            )

            if st.button(
                "🗑️ DELETE ROUTE"
            ):

                if confirm:

                    db_execute(
                        "DELETE FROM routes WHERE route_no=?",
                        (selected,)
                    )

                    st.success(
                        "Route deleted."
                    )

                else:

                    st.warning(
                        "Please confirm deletion."
                    )


# ============================================================
# SERVICE MANAGEMENT
# ============================================================

elif menu == "Service Management":

    st.header("🚍 Bus Service Management")

    tab1, tab2 = st.tabs(
        [
            "Add Service",
            "View Services"
        ]
    )

    with tab1:

        routes = db_query(
            "SELECT route_no FROM routes ORDER BY route_no"
        )

        buses = db_query(
            "SELECT bus_id FROM buses ORDER BY bus_id"
        )

        if routes.empty:

            st.warning(
                "Add a route before creating a service."
            )

        else:

            with st.form("service_form"):

                service_id = st.text_input(
                    "Service ID",
                    value=generate_service_id()
                )

                c1, c2 = st.columns(2)

                with c1:

                    route_no = st.selectbox(
                        "Route",
                        routes["route_no"].tolist()
                    )

                    bus_id = st.selectbox(
                        "Bus",
                        buses["bus_id"].tolist()
                        if not buses.empty
                        else ["No bus"]
                    )

                    bus_type = st.selectbox(
                        "Bus Type",
                        BUS_TYPES
                    )

                    departure = st.time_input(
                        "Departure Time"
                    )

                with c2:

                    arrival = st.time_input(
                        "Arrival Time"
                    )

                    route_data = db_query(
                        """
                        SELECT distance_km
                        FROM routes
                        WHERE route_no=?
                        """,
                        (route_no,)
                    )

                    default_distance = (
                        float(
                            route_data.iloc[0]["distance_km"]
                        )
                        if not route_data.empty
                        else 0.0
                    )

                    distance = st.number_input(
                        "Verified Distance KM",
                        min_value=0.0,
                        value=default_distance
                    )

                    fare = st.number_input(
                        "Official Service Fare ₹",
                        min_value=0.0,
                        value=0.0,
                        step=1.0
                    )

                    fare_status = st.selectbox(
                        "Fare Status",
                        [
                            "VERIFIED",
                            "ESTIMATED"
                        ]
                    )

                    source_reference = st.text_input(
                        "Fare Source / Reference"
                    )

                save_service = st.form_submit_button(
                    "➕ ADD SERVICE",
                    use_container_width=True
                )

            if save_service:

                db_execute(
                    """
                    INSERT INTO services
                    (
                        service_id,
                        route_no,
                        bus_id,
                        bus_type,
                        departure,
                        arrival,
                        distance_km,
                        fare,
                        fare_status,
                        source,
                        verified
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        service_id.strip().upper(),
                        route_no,
                        bus_id,
                        bus_type,
                        departure.strftime("%H:%M"),
                        arrival.strftime("%H:%M"),
                        distance,
                        fare,
                        fare_status,
                        source_reference,
                        int(fare_status == "VERIFIED")
                    )
                )

                st.success(
                    "Service added successfully."
                )

    with tab2:

        services = db_query(
            "SELECT * FROM services ORDER BY route_no, departure"
        )

        if services.empty:

            st.info(
                "No services available."
            )

        else:

            st.dataframe(
                services,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# PASSENGER MANAGEMENT
# ============================================================

elif menu == "Passenger Management":

    st.header("👤 Passenger Management")

    tab1, tab2, tab3 = st.tabs(
        [
            "Book Ticket",
            "Passenger Details",
            "Cancel Ticket"
        ]
    )

    # --------------------------------------------------------
    # BOOK
    # --------------------------------------------------------

    with tab1:

        buses = db_query(
            "SELECT * FROM buses ORDER BY bus_id"
        )

        routes = db_query(
            "SELECT * FROM routes ORDER BY route_no"
        )

        with st.form("booking_form"):

            st.subheader(
                "🎫 Online Bus Ticket Booking"
            )

            c1, c2 = st.columns(2)

            with c1:

                passenger_name = st.text_input(
                    "Passenger Name"
                )

                age = st.number_input(
                    "Age",
                    min_value=1,
                    max_value=120,
                    value=25
                )

                gender = st.selectbox(
                    "Gender",
                    [
                        "Male",
                        "Female",
                        "Other"
                    ]
                )

                phone = st.text_input(
                    "Phone Number"
                )

                source = st.text_input(
                    "From"
                )

                destination = st.text_input(
                    "To"
                )

            with c2:

                route_no = st.text_input(
                    "Route Number"
                )

                service_type = st.selectbox(
                    "Service Type",
                    BUS_TYPES
                )

                bus_id = st.selectbox(
                    "Bus",
                    buses["bus_id"].tolist()
                    if not buses.empty
                    else ["No bus"]
                )

                seats_text = st.text_input(
                    "Seat Numbers",
                    placeholder="A1,A2"
                )

                seat_count = st.number_input(
                    "Number of Seats",
                    min_value=1,
                    max_value=10,
                    value=1
                )

            booking = st.form_submit_button(
                "🎫 BOOK TICKET",
                use_container_width=True
            )

        if booking:

            if not passenger_name.strip():
                st.error(
                    "Passenger name is required."
                )

            elif not source.strip():
                st.error(
                    "Source is required."
                )

            elif not destination.strip():
                st.error(
                    "Destination is required."
                )

            else:

                route_data = get_route(
                    source,
                    destination
                )

                if not route_data.empty:

                    distance = float(
                        route_data.iloc[0]["distance_km"]
                    )

                else:

                    distance = 0.0

                if distance <= 0:

                    st.warning(
                        "No verified route distance exists "
                        "for this From/To pair. "
                        "Enter the route in Route Management first."
                    )

                else:

                    fare_info = calculate_fare(
                        route_no,
                        source,
                        destination,
                        service_type,
                        distance
                    )

                    pnr = generate_pnr()

                    total_fare = (
                        fare_info["fare"]
                        * int(seat_count)
                    )

                    db_execute(
                        """
                        INSERT INTO passengers
                        (
                            pnr,
                            passenger_name,
                            age,
                            gender,
                            phone,
                            source_place,
                            destination,
                            route_no,
                            bus_id,
                            service_type,
                            seats,
                            seat_count,
                            fare,
                            booking_status,
                            booked_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            pnr,
                            passenger_name.strip(),
                            int(age),
                            gender,
                            phone.strip(),
                            source.strip().title(),
                            destination.strip().title(),
                            route_no.strip().upper(),
                            bus_id,
                            service_type,
                            seats_text.strip(),
                            int(seat_count),
                            total_fare,
                            "CONFIRMED",
                            datetime.now().isoformat()
                        )
                    )

                    # Update available seats
                    db_execute(
                        """
                        UPDATE buses
                        SET available_seats =
                            MAX(
                                0,
                                available_seats - ?
                            )
                        WHERE bus_id=?
                        """,
                        (
                            int(seat_count),
                            bus_id
                        )
                    )

                    st.success(
                        f"Ticket booked successfully. PNR: {pnr}"
                    )

                    st.info(
                        f"""
                        **PNR:** {pnr}

                        **Passenger:** {passenger_name}

                        **Route:** {source.title()} → {destination.title()}

                        **Distance:** {distance:.1f} KM

                        **Fare / Seat:** ₹{fare_info['fare']:.2f}

                        **Total Fare:** ₹{total_fare:.2f}

                        **Fare Status:** {fare_info['status']}
                        """
                    )

    # --------------------------------------------------------
    # PASSENGER DETAILS
    # --------------------------------------------------------

    with tab2:

        passengers = db_query(
            """
            SELECT *
            FROM passengers
            ORDER BY id DESC
            """
        )

        if passengers.empty:

            st.info(
                "No passenger records."
            )

        else:

            search_pnr = st.text_input(
                "Search by PNR / Passenger Name"
            )

            if search_pnr.strip():

                keyword = (
                    f"%{search_pnr.strip()}%"
                )

                passengers = db_query(
                    """
                    SELECT *
                    FROM passengers
                    WHERE
                        pnr LIKE ?
                        OR passenger_name LIKE ?
                    ORDER BY id DESC
                    """,
                    (
                        keyword,
                        keyword
                    )
                )

            st.dataframe(
                passengers,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "📥 Download Passenger Data",
                data=passengers.to_csv(
                    index=False
                ),
                file_name="smart_bus_passengers.csv",
                mime="text/csv"
            )

    # --------------------------------------------------------
    # CANCEL
    # --------------------------------------------------------

    with tab3:

        pnr = st.text_input(
            "Enter PNR to Cancel"
        )

        if st.button(
            "❌ CANCEL TICKET"
        ):

            ticket = db_query(
                """
                SELECT *
                FROM passengers
                WHERE pnr=?
                """,
                (pnr.strip().upper(),)
            )

            if ticket.empty:

                st.error(
                    "PNR not found."
                )

            elif ticket.iloc[0][
                "booking_status"
            ] == "CANCELLED":

                st.warning(
                    "This ticket is already cancelled."
                )

            else:

                row = ticket.iloc[0]

                db_execute(
                    """
                    UPDATE passengers
                    SET booking_status='CANCELLED'
                    WHERE pnr=?
                    """,
                    (pnr.strip().upper(),)
                )

                db_execute(
                    """
                    UPDATE buses
                    SET available_seats =
                        available_seats + ?
                    WHERE bus_id=?
                    """,
                    (
                        int(row["seat_count"]),
                        row["bus_id"]
                    )
                )

                st.success(
                    f"Ticket {pnr.upper()} cancelled successfully."
                )


# ============================================================
# FARE CALCULATOR
# ============================================================

elif menu == "Fare Calculator":

    st.header("💰 Government Bus Fare Calculator")

    st.info(
        "Exact route fares should come from a verified service/fare "
        "record. If an exact verified fare is not available, the "
        "system uses the published tariff rule and clearly marks "
        "the result as ESTIMATED."
    )

    c1, c2 = st.columns(2)

    with c1:

        route_no = st.text_input(
            "Route Number"
        )

        source = st.text_input(
            "From"
        )

        destination = st.text_input(
            "To"
        )

        bus_type = st.selectbox(
            "Bus / Service Type",
            BUS_TYPES
        )

    with c2:

        route_data = get_route(
            source,
            destination
        ) if source and destination else pd.DataFrame()

        if not route_data.empty:

            distance = float(
                route_data.iloc[0]["distance_km"]
            )

            if route_data.iloc[0]["verified"]:

                st.success(
                    f"Verified route distance: {distance:.1f} KM"
                )

            else:

                st.warning(
                    "Route distance is not verified."
                )

        else:

            distance = st.number_input(
                "Distance KM",
                min_value=0.0,
                max_value=2000.0,
                value=0.0
            )

    if st.button(
        "🧮 CALCULATE FARE",
        use_container_width=True
    ):

        if distance <= 0:

            st.error(
                "A valid verified route distance is required."
            )

        else:

            result = calculate_fare(
                route_no,
                source,
                destination,
                bus_type,
                distance
            )

            st.markdown(
                f"""
                <div class="card">

                <h2>₹ {result['fare']:.2f}</h2>

                <p>
                <b>From:</b> {source.title()}
                </p>

                <p>
                <b>To:</b> {destination.title()}
                </p>

                <p>
                <b>Distance:</b> {result['distance']:.1f} KM
                </p>

                <p>
                <b>Service:</b> {bus_type}
                </p>

                <p>
                <b>Status:</b> {result['status']}
                </p>

                <p>
                <b>Source:</b> {result['source']}
                </p>

                </div>
                """,
                unsafe_allow_html=True
            )

    st.divider()

    st.subheader(
        "📊 Published Tariff Rules"
    )

    fare_table = []

    for name, rule in OFFICIAL_FARE_RULES.items():

        fare_table.append(
            {
                "Service Type": name,
                "Rate ₹ / KM": rule["rate"],
                "Minimum Fare ₹": rule["minimum"],
                "Status": "Published Rule"
            }
        )

    st.dataframe(
        pd.DataFrame(fare_table),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# BUS STATUS REPORT
# ============================================================

elif menu == "Bus Status Report":

    st.header("📋 Bus Status Report")

    buses = db_query(
        "SELECT * FROM buses ORDER BY bus_id"
    )

    if buses.empty:

        st.info(
            "No bus records available."
        )

    else:

        for _, bus in buses.iterrows():

            available = int(
                bus["available_seats"]
            )

            capacity = int(
                bus["capacity"]
            )

            passengers = max(
                0,
                capacity - available
            )

            load_percentage = (
                passengers / capacity * 100
                if capacity > 0
                else 0
            )

            st.markdown(
                f"""
                <div class="card">

                <h3>🚌 {bus['bus_id']}</h3>

                <b>Route:</b> {bus['route_no']}
                &nbsp;&nbsp;&nbsp;

                <b>Corporation:</b> {bus['corporation']}

                <br><br>

                <b>Registration:</b>
                {bus['registration_no']}

                &nbsp;&nbsp;&nbsp;

                <b>Bus Type:</b>
                {bus['bus_type']}

                <br><br>

                <b>Capacity:</b>
                {capacity}

                &nbsp;&nbsp;&nbsp;

                <b>Passengers:</b>
                {passengers}

                &nbsp;&nbsp;&nbsp;

                <b>Available Seats:</b>
                {available}

                <br><br>

                <b>Status:</b>
                {bus['status']}

                <br><br>

                <b>Passenger Load:</b>
                {load_percentage:.1f}%

                </div>
                """,
                unsafe_allow_html=True
            )

            st.progress(
                min(
                    load_percentage / 100,
                    1.0
                )
            )


# ============================================================
# GOVERNMENT BUS TYPES
# ============================================================

elif menu == "Government Bus Types":

    st.header(
        "🚌 Tamil Nadu Government Bus Types"
    )

    st.write(
        "The system supports the major government-transport "
        "service categories used by Tamil Nadu State Transport "
        "Corporations."
    )

    type_rows = []

    for bus_type in BUS_TYPES:

        if bus_type in [
            "Ordinary",
            "Express",
            "Town Bus"
        ]:
            category = "Regular / Town"

        elif "Sleeper" in bus_type:
            category = "Sleeper"

        elif "AC" in bus_type or "Volvo" in bus_type:
            category = "Air Conditioned"

        elif bus_type in [
            "Super Deluxe",
            "Ultra Deluxe",
            "Semi Deluxe",
            "Semi Luxury",
            "Luxury",
            "Classic"
        ]:
            category = "Long Distance"

        elif bus_type == "Ghat Service":
            category = "Hill / Ghat"

        else:
            category = "Other"

        type_rows.append(
            {
                "Bus Type": bus_type,
                "Category": category
            }
        )

    st.dataframe(
        pd.DataFrame(type_rows),
        use_container_width=True,
        hide_index=True
    )

    st.subheader(
        "Government Transport Corporations"
    )

    st.dataframe(
        pd.DataFrame(
            {
                "Corporation": TNSTC_CORPORATIONS
            }
        ),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# FARE MASTER
# ============================================================

elif menu == "Fare Master":

    st.header(
        "📚 Verified Fare Master"
    )

    st.info(
        "Use this section to enter the exact fare shown by "
        "the official TNSTC service/booking result. "
        "Only records marked VERIFIED are used as exact fares."
    )

    tab1, tab2 = st.tabs(
        [
            "Add Verified Fare",
            "View Fare Master"
        ]
    )

    with tab1:

        with st.form("fare_master_form"):

            c1, c2 = st.columns(2)

            with c1:

                route_no = st.text_input(
                    "Route Number"
                )

                source = st.text_input(
                    "From"
                )

                destination = st.text_input(
                    "To"
                )

                bus_type = st.selectbox(
                    "Bus Type",
                    BUS_TYPES
                )

            with c2:

                distance = st.number_input(
                    "Official Total KM",
                    min_value=0.0,
                    max_value=2000.0,
                    value=0.0
                )

                fare = st.number_input(
                    "Exact Fare ₹",
                    min_value=0.0,
                    max_value=10000.0,
                    value=0.0
                )

                source_reference = st.text_input(
                    "Official Source / Trip Result"
                )

                verified_date = st.date_input(
                    "Verified Date",
                    value=date.today()
                )

            save_fare = st.form_submit_button(
                "💾 SAVE VERIFIED FARE",
                use_container_width=True
            )

        if save_fare:

            if (
                not source.strip()
                or not destination.strip()
                or distance <= 0
                or fare <= 0
            ):

                st.error(
                    "Enter source, destination, distance and fare."
                )

            else:

                db_execute(
                    """
                    INSERT INTO fare_master
                    (
                        route_no,
                        source_place,
                        destination,
                        bus_type,
                        distance_km,
                        fare,
                        fare_status,
                        source,
                        verified_date
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'VERIFIED', ?, ?)
                    """,
                    (
                        route_no.strip().upper(),
                        source.strip().title(),
                        destination.strip().title(),
                        bus_type,
                        distance,
                        fare,
                        source_reference.strip(),
                        verified_date.isoformat()
                    )
                )

                st.success(
                    "Verified fare saved."
                )

    with tab2:

        fares = db_query(
            """
            SELECT *
            FROM fare_master
            ORDER BY source_place, destination
            """
        )

        if fares.empty:

            st.info(
                "No verified fares have been added yet."
            )

        else:

            st.dataframe(
                fares,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "📥 Download Fare Master",
                data=fares.to_csv(
                    index=False
                ),
                file_name="smart_bus_verified_fares.csv",
                mime="text/csv"
            )


# ============================================================
# OFFICIAL SOURCES
# ============================================================

elif menu == "Official Sources":

    st.header(
        "🌐 Official Government Sources"
    )

    st.markdown(
        f"""
        ### TNSTC Official Online Reservation

        {OFFICIAL_TNSTC_URL}

        ### TNSTC Bus Search

        {OFFICIAL_BUS_SEARCH_URL}

        ### TNSTC Know Your Bus

        {OFFICIAL_KNOW_BUS_URL}
        """
    )

    st.divider()

    st.subheader(
        "Important Data Rule"
    )

    st.write(
        """
        Exact distance and fare are stored separately from
        estimated tariff calculations.

        A route becomes VERIFIED only after entering the
        official route/service information.

        A fare becomes VERIFIED only when the exact fare for
        that route and service is entered.

        The application does not invent a distance or call an
        estimated fare an official fare.
        """
    )

    st.subheader(
        "Supported Government Corporations"
    )

    for corporation in TNSTC_CORPORATIONS:
        st.write(
            f"• {corporation}"
        )

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "SMART BUS – Bus Route and Passenger Management System"
)

st.caption(
    "Tamil Nadu Government Bus Management Project"
)
