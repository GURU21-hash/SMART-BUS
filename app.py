import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

# ---------------------------------------------------------
# PAGE SETUP & OMIO-STYLE THEME INJECTION
# ---------------------------------------------------------
st.set_page_config(
    page_title="SMART BUS | Intercity Travel",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #111827;
}

/* Base Container */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

/* Header Banner */
.hero-header {
    background: linear-gradient(135deg, #102A43 0%, #0B1D3A 100%);
    border-radius: 16px;
    padding: 32px 36px;
    color: #ffffff;
    margin-bottom: 24px;
    box-shadow: 0 10px 25px -5px rgba(11, 29, 58, 0.15);
}
.hero-title {
    font-size: 30px;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin: 0;
    color: #FFFFFF;
}
.hero-subtitle {
    font-size: 14px;
    color: #9FB3C8;
    margin-top: 6px;
    margin-bottom: 0;
}

/* Omio Ticket Card */
.ticket-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 16px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    transition: all 0.2s ease-in-out;
}
.ticket-card:hover {
    border-color: #CBD5E1;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.06);
}
.operator-badge {
    background: #F1F5F9;
    color: #334155;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
}
.amenity-chip {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    color: #64748B;
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 20px;
    font-weight: 500;
}
.price-tag {
    font-size: 24px;
    font-weight: 800;
    color: #0F172A;
}

/* Timeline Indicators */
.timeline-text {
    font-size: 18px;
    font-weight: 700;
    color: #0F172A;
}
.timeline-sub {
    font-size: 12px;
    color: #64748B;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DATABASE ENGINE
# ---------------------------------------------------------
DB = "smart_bus.db"
ADMIN_PASSWORD = os.environ.get("SMART_BUS_ADMIN_PASSWORD", "admin123")

CORPORATIONS = [
    "MTC", "SETC", "TNSTC Villupuram", "TNSTC Salem",
    "TNSTC Coimbatore", "TNSTC Madurai", "TNSTC Kumbakonam",
    "TNSTC Tirunelveli"
]
BUS_TYPES = ["Ordinary", "Express", "Super Deluxe", "Ultra Deluxe",
             "AC", "AC Sleeper", "Volvo", "Low Floor", "Semi Low Floor"]
STATUSES = ["Running", "Scheduled", "Maintenance", "Breakdown", "Inactive"]

def db():
    return sqlite3.connect(DB, check_same_thread=False)

def setup():
    c = db()
    c.execute("""CREATE TABLE IF NOT EXISTS buses(
        bus_id TEXT PRIMARY KEY, reg_no TEXT UNIQUE, corporation TEXT,
        route_no TEXT, route TEXT, driver TEXT, bus_type TEXT,
        capacity INTEGER, available_seats INTEGER, status TEXT,
        depot TEXT, updated_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS routes(
        route_no TEXT PRIMARY KEY, source TEXT, destination TEXT,
        stops TEXT, distance_km REAL, active INTEGER DEFAULT 1)""")
    c.execute("""CREATE TABLE IF NOT EXISTS passengers(
        pnr TEXT PRIMARY KEY, name TEXT, phone TEXT, bus_id TEXT,
        route_no TEXT, source TEXT, destination TEXT, seats INTEGER,
        fare REAL, status TEXT, booked_at TEXT)""")
    c.commit()
    c.close()

def query(sql, params=()):
    c = db()
    out = pd.read_sql_query(sql, c, params=params)
    c.close()
    return out

def run(sql, params=()):
    c = db()
    c.execute(sql, params)
    c.commit()
    c.close()

def seed():
    if not query("SELECT * FROM buses LIMIT 1").empty:
        return
    rows = [
        ("BUS101","TN33N0101","TNSTC Coimbatore","R12","Erode - Coimbatore","Government Driver","Express",50,42,"Running","Erode"),
        ("BUS102","TN38N0102","TNSTC Salem","R21","Salem - Erode","Government Driver","Ordinary",52,48,"Scheduled","Salem"),
        ("BUS103","TN57N0103","TNSTC Madurai","R31","Madurai - Trichy","Government Driver","Super Deluxe",48,22,"Running","Madurai"),
        ("BUS104","TN72N0104","TNSTC Tirunelveli","R41","Tirunelveli - Madurai","Government Driver","Ultra Deluxe",48,31,"Running","Tirunelveli"),
        ("BUS105","TN01N0105","MTC","M1","Chennai City Service","Government Driver","Ordinary",50,15,"Running","Chennai"),
        ("BUS106","TN01N0106","SETC","S1","Chennai - Coimbatore","Government Driver","Volvo",40,18,"Scheduled","Chennai"),
    ]
    c = db()
    c.executemany(
        "INSERT INTO buses VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        [x + (datetime.now().strftime("%Y-%m-%d %H:%M"),) for x in rows]
    )
    routes = [
        ("R12","Erode","Coimbatore","Erode, Perundurai, Avinashi, Coimbatore",100),
        ("R21","Salem","Erode","Salem, Sankari, Bhavani, Erode",65),
        ("R31","Madurai","Trichy","Madurai, Melur, Dindigul, Manapparai, Trichy",140),
        ("R41","Tirunelveli","Madurai","Tirunelveli, Kovilpatti, Virudhunagar, Madurai",160),
        ("M1","Chennai","Chennai","Central, Egmore, T Nagar, Guindy",25),
        ("S1","Chennai","Coimbatore","Chennai, Salem, Erode, Tiruppur, Coimbatore",500),
    ]
    c.executemany("INSERT INTO routes VALUES(?,?,?,?,?,1)", routes)
    c.commit()
    c.close()

setup()
seed()

# ---------------------------------------------------------
# TOP BANNER
# ---------------------------------------------------------
st.markdown("""
<div class="hero-header">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h1 class="hero-title">smartbus</h1>
            <p class="hero-subtitle">Intercity Bus Reservation & Real-Time Fleet Network</p>
        </div>
        <div style="text-align:right;">
            <span style="background:rgba(255,255,255,0.15); padding:6px 14px; border-radius:20px; font-size:12px; font-weight:600;">
                🟢 All TN Corridors Operational
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# SIDEBAR NAVIGATION & AUTHENTICATION
# ---------------------------------------------------------
if "admin" not in st.session_state:
    st.session_state.admin = False

st.sidebar.markdown("### 🧭 Portal Navigation")
view_mode = st.sidebar.radio(
    "Choose View",
    ["Traveler Portal", "Fleet & Dispatch Ops", "System Analytics"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
with st.sidebar.expander("🔐 Depot / Admin Portal"):
    if not st.session_state.admin:
        password = st.text_input("Enter Passkey", type="password")
        if st.button("Unlock Admin Access", use_container_width=True):
            if password == ADMIN_PASSWORD:
                st.session_state.admin = True
                st.toast("Admin clearance authorized", icon="✅")
                st.rerun()
            else:
                st.error("Invalid credentials")
    else:
        st.success("Admin Active")
        if st.button("Logout", use_container_width=True):
            st.session_state.admin = False
            st.rerun()

admin = st.session_state.admin

# =========================================================
# 1. TRAVELER PORTAL (OMIO SEARCH & BOOKING EXPERIENCE)
# =========================================================
if view_mode == "Traveler Portal":
    # SEARCH BAR CONTAINER
    with st.container():
        st.markdown("#### Where do you want to travel?")
        routes_df = query("SELECT DISTINCT source, destination FROM routes WHERE active=1")
        sources = sorted(list(set(routes_df["source"].tolist()))) if not routes_df.empty else ["Chennai", "Coimbatore"]
        destinations = sorted(list(set(routes_df["destination"].tolist()))) if not routes_df.empty else ["Coimbatore", "Salem"]

        col1, col2, col3, col4 = st.columns([1.2, 1.2, 1, 0.8])
        with col1:
            from_city = st.selectbox("From", sources, index=0)
        with col2:
            to_city = st.selectbox("To", destinations, index=min(1, len(destinations)-1))
        with col3:
            journey_date = st.date_input("Travel Date")
        with col4:
            st.write("")
            st.write("")
            search_pressed = st.button("Search Buses", type="primary", use_container_width=True)

    st.markdown("---")

    booking_tab, track_tab = st.tabs(["⚡ Available Departures", "🎫 Manage / Print Ticket"])

    with booking_tab:
        # Query matching buses
        buses_query = query("""
            SELECT b.*, r.distance_km, r.stops 
            FROM buses b
            LEFT JOIN routes r ON b.route_no = r.route_no
            WHERE b.status != 'Inactive'
        """)

        # Filter by city or route match
        filtered_buses = buses_query[
            buses_query['route'].str.contains(from_city, case=False, na=False) |
            buses_query['route'].str.contains(to_city, case=False, na=False)
        ] if not buses_query.empty else pd.DataFrame()

        if filtered_buses.empty:
            st.info(f"No direct departures found between **{from_city}** and **{to_city}**. Showing all running express buses below:")
            filtered_buses = buses_query.head(4)

        # Render Tickets with Omio-style layouts
        for idx, bus in filtered_buses.iterrows():
            seats_left = int(bus['available_seats'])
            distance = float(bus['distance_km']) if pd.notnull(bus['distance_km']) else 120.0
            fare_est = max(120.0, round(distance * 1.45, 0))

            card_col, action_col = st.columns([3, 1])
            with card_col:
                st.markdown(f"""
                <div class="ticket-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                        <span class="operator-badge">{bus['corporation']}</span>
                        <span style="font-size:12px; color:{'#16A34A' if seats_left > 10 else '#DC2626'}; font-weight:700;">
                            ● {seats_left} seats remaining
                        </span>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div class="timeline-text">20:30</div>
                            <div class="timeline-sub">{from_city}</div>
                        </div>
                        <div style="text-align:center; flex:1; padding:0 24px;">
                            <div style="font-size:11px; color:#94A3B8; font-weight:600;">{round(distance/45, 1)} hrs</div>
                            <div style="height:2px; background:#CBD5E1; position:relative; margin:6px 0;">
                                <div style="width:6px; height:6px; background:#475569; border-radius:50%; position:absolute; top:-2px; left:0;"></div>
                                <div style="width:6px; height:6px; background:#475569; border-radius:50%; position:absolute; top:-2px; right:0;"></div>
                            </div>
                            <div style="font-size:11px; color:#64748B;">Direct • {bus['bus_type']}</div>
                        </div>
                        <div style="text-align:right;">
                            <div class="timeline-text">04:15</div>
                            <div class="timeline-sub">{to_city}</div>
                        </div>
                    </div>
                    <div style="margin-top:16px; display:flex; gap:8px;">
                        <span class="amenity-chip">⚡ Live GPS</span>
                        <span class="amenity-chip">🔌 Charging Ports</span>
                        <span class="amenity-chip">❄️ {bus['bus_type']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with action_col:
                st.markdown(f"""
                <div style="padding-top:20px; text-align:center;">
                    <div style="font-size:11px; color:#64748B; font-weight:600;">FARE / PASSENGER</div>
                    <div class="price-tag">₹{int(fare_est)}</div>
                </div>
                """, unsafe_allow_html=True)

                with st.popover(f"Select Seats", use_container_width=True):
                    st.write(f"**Reserve on {bus['reg_no']}**")
                    passenger_name = st.text_input("Full Name", key=f"name_{bus['bus_id']}")
                    passenger_phone = st.text_input("Mobile Number", key=f"phone_{bus['bus_id']}")
                    seat_count = st.number_input("Passengers", 1, min(seats_left, 6), 1, key=f"seat_{bus['bus_id']}")

                    total_price = seat_count * fare_est
                    st.markdown(f"**Total Payable:** ₹{total_price:,.2f}")

                    if st.button("Confirm Booking", key=f"btn_{bus['bus_id']}", type="primary", use_container_width=True):
                        if not passenger_name or not passenger_phone:
                            st.error("Please supply contact details")
                        else:
                            pnr = "SB" + datetime.now().strftime("%y%m%d%H%M%S")[-8:]
                            run("""INSERT INTO passengers VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                                (pnr, passenger_name, passenger_phone, bus['bus_id'],
                                 str(bus['route_no']), from_city, to_city,
                                 int(seat_count), float(total_price), "Booked",
                                 datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            run("UPDATE buses SET available_seats=available_seats-? WHERE bus_id=?",
                                (int(seat_count), bus['bus_id']))
                            st.balloons()
                            st.success(f"Confirmed! PNR: {pnr}")
                            st.rerun()

    with track_tab:
        st.subheader("Your Journey Itinerary")
        ticket_pnr = st.text_input("Enter 10-Digit PNR Code", placeholder="e.g. SB2610081234").strip()
        if ticket_pnr:
            pnr_record = query("SELECT * FROM passengers WHERE pnr=?", (ticket_pnr,))
            if not pnr_record.empty:
                t = pnr_record.iloc[0]
                st.markdown(f"""
                <div class="ticket-card" style="border-left:5px solid #16A34A;">
                    <div style="display:flex; justify-content:space-between;">
                        <h4>PNR: {t['pnr']}</h4>
                        <span style="font-weight:700; color:{'#16A34A' if t['status']=='Booked' else '#DC2626'}">{t['status']}</span>
                    </div>
                    <p style="margin:4px 0;"><strong>Passenger:</strong> {t['name']} ({t['phone']})</p>
                    <p style="margin:4px 0;"><strong>Route:</strong> {t['source']} ➔ {t['destination']}</p>
                    <p style="margin:4px 0;"><strong>Reserved Seats:</strong> {t['seats']} | <strong>Total Paid:</strong> ₹{t['fare']}</p>
                </div>
                """, unsafe_allow_html=True)

                if t['status'] == "Booked":
                    if st.button("Cancel Reservation", type="secondary"):
                        run("UPDATE passengers SET status='Cancelled' WHERE pnr=?", (t['pnr'],))
                        run("UPDATE buses SET available_seats=available_seats+? WHERE bus_id=?", (int(t['seats']), t['bus_id']))
                        st.toast("Booking Cancelled & Seat Restored", icon="⚠️")
                        st.rerun()
            else:
                st.error("No ticket found with this PNR.")

# =========================================================
# 2. FLEET & DISPATCH OPS
# =========================================================
elif view_mode == "Fleet & Dispatch Ops":
    st.markdown("### 🚌 Fleet & Transit Administration")

    tab1, tab2, tab3 = st.tabs(["Active Fleet Directory", "Register Bus Unit", "Depot Routes"])

    with tab1:
        f_col1, f_col2 = st.columns([2, 1])
        with f_col1:
            q_search = st.text_input("Filter by Registration, Corporation, or Corridor")
        with f_col2:
            q_corp = st.selectbox("Corporation Filter", ["All"] + CORPORATIONS)

        fleet_df = query("SELECT * FROM buses WHERE status != 'Inactive'")
        if q_corp != "All":
            fleet_df = fleet_df[fleet_df['corporation'] == q_corp]
        if q_search:
            s = q_search.lower()
            fleet_df = fleet_df[fleet_df.apply(lambda r: s in " ".join(map(str, r.values)).lower(), axis=1)]

        st.dataframe(fleet_df, use_container_width=True, hide_index=True)

    with tab2:
        if not admin:
            st.warning("⚠️ Restricted area. Login via Depot / Admin Portal in the sidebar to add units.")
        else:
            with st.form("bus_reg_form"):
                c1, c2, c3 = st.columns(3)
                bid = c1.text_input("Bus ID", "BUS" + str(datetime.now().strftime("%f")[:3]))
                reg = c2.text_input("Registration Plate", "TN")
                corp = c3.selectbox("Corporation", CORPORATIONS)

                c4, c5, c6 = st.columns(3)
                rt_no = c4.text_input("Assigned Route No", "R12")
                rt_desc = c5.text_input("Route Name", "Erode - Coimbatore")
                driver_name = c6.text_input("Assigned Crew", "Govt Driver")

                c7, c8, c9 = st.columns(3)
                btype = c7.selectbox("Bus Classification", BUS_TYPES)
                cap = c8.number_input("Max Capacity", 20, 70, 50)
                status = c9.selectbox("Operational Status", STATUSES)

                submit = st.form_submit_button("Deploy Bus to Fleet", use_container_width=True)
                if submit:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    run("""INSERT INTO buses VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                           ON CONFLICT(bus_id) DO UPDATE SET
                           reg_no=excluded.reg_no, corporation=excluded.corporation,
                           route_no=excluded.route_no, route=excluded.route,
                           driver=excluded.driver, bus_type=excluded.bus_type,
                           capacity=excluded.capacity, available_seats=excluded.capacity,
                           status=excluded.status, depot=excluded.depot, updated_at=excluded.updated_at""",
                        (bid.upper(), reg.upper(), corp, rt_no, rt_desc, driver_name,
                         btype, int(cap), int(cap), status, "Head Depot", now))
                    st.success(f"Bus {bid} dispatched successfully.")
                    st.rerun()

    with tab3:
        st.markdown("#### Operational Route Corridors")
        st.dataframe(query("SELECT * FROM routes WHERE active=1"), use_container_width=True, hide_index=True)

# =========================================================
# 3. ANALYTICS
# =========================================================
elif view_mode == "System Analytics":
    st.markdown("### 📊 Network Capacity & Demand Analytics")

    b_data = query("SELECT * FROM buses WHERE status != 'Inactive'")
    p_data = query("SELECT * FROM passengers WHERE status = 'Booked'")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active Buses", len(b_data))
    m2.metric("Seats Reserved", int(p_data["seats"].sum()) if not p_data.empty else 0)
    m3.metric("Passenger Revenue", f"₹{p_data['fare'].sum():,.0f}" if not p_data.empty else "₹0")
    m4.metric("Avg Seat Occupancy", f"{round(((b_data['capacity'] - b_data['available_seats']).sum() / b_data['capacity'].sum()) * 100, 1)}%" if not b_data.empty else "0%")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Fleet Share by Corporation")
        if not b_data.empty:
            corp_counts = b_data.groupby("corporation").size()
            st.bar_chart(corp_counts)
    with c2:
        st.markdown("##### Peak Booking Volume (Hourly)")
        if not p_data.empty:
            p_data['hour'] = pd.to_datetime(p_data['booked_at']).dt.hour
            st.bar_chart(p_data.groupby('hour').size())
        else:
            st.info("No passenger transactions recorded yet.")
