import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="SMART BUS", page_icon="🚌", layout="wide")

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
        ("BUS101","TN33N0101","TNSTC Coimbatore","R12","Erode - Coimbatore","Government Driver","Express",50,50,"Running","Erode"),
        ("BUS102","TN38N0102","TNSTC Salem","R21","Salem - Erode","Government Driver","Ordinary",52,52,"Scheduled","Salem"),
        ("BUS103","TN57N0103","TNSTC Madurai","R31","Madurai - Trichy","Government Driver","Super Deluxe",48,48,"Running","Madurai"),
        ("BUS104","TN72N0104","TNSTC Tirunelveli","R41","Tirunelveli - Madurai","Government Driver","Ultra Deluxe",48,48,"Running","Tirunelveli"),
        ("BUS105","TN01N0105","MTC","M1","Chennai City Service","Government Driver","Ordinary",50,50,"Running","Chennai"),
        ("BUS106","TN01N0106","SETC","S1","Chennai - Coimbatore","Government Driver","Volvo",40,40,"Scheduled","Chennai"),
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

st.markdown("""
<style>
.block-container{padding-top:1.5rem}
.title{font-size:36px;font-weight:800;margin:0}
.subtitle{color:#666;font-size:16px}
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🚌 SMART BUS")
st.sidebar.caption("BUS ROUTE AND PASSENGER MANAGEMENT SYSTEM")

if "admin" not in st.session_state:
    st.session_state.admin = False

with st.sidebar.expander("🔐 Admin Login"):
    password = st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        if password == ADMIN_PASSWORD:
            st.session_state.admin = True
            st.success("Admin logged in")
            st.rerun()
        else:
            st.error("Wrong password")

admin = st.session_state.admin

page = st.sidebar.radio("MENU", [
    "🏠 Dashboard", "🚌 Bus Management", "🗺️ Route Management",
    "🎫 Passenger Management", "💰 Fare Calculator",
    "📊 Analytics", "📋 Bus Status Report", "🔐 Admin Portal"
])

st.markdown('<p class="title">SMART BUS</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">BUS ROUTE AND PASSENGER MANAGEMENT SYSTEM</p>', unsafe_allow_html=True)
st.divider()

# DASHBOARD
if page == "🏠 Dashboard":
    buses = query("SELECT * FROM buses WHERE status!='Inactive'")
    routes = query("SELECT * FROM routes WHERE active=1")
    passengers = query("SELECT * FROM passengers WHERE status='Booked'")

    a,b,c,d = st.columns(4)
    a.metric("Total Buses", len(buses))
    b.metric("Active Routes", len(routes))
    c.metric("Booked Tickets", len(passengers))
    d.metric("Available Seats", int(buses.available_seats.sum()) if not buses.empty else 0)

    st.subheader("Tamil Nadu Government Transport Corporations")
    cols = st.columns(4)
    for i, corp in enumerate(CORPORATIONS):
        n = len(buses[buses.corporation == corp])
        cols[i % 4].info(f"**{corp}**\n\n{n} buses")

    st.subheader("Fleet")
    st.dataframe(buses, use_container_width=True, hide_index=True)

# BUS MANAGEMENT
elif page == "🚌 Bus Management":
    st.subheader("Bus Management")
    t1,t2,t3 = st.tabs(["🔎 Search / View","➕ Add / Update","🗑️ Delete"])

    with t1:
        search = st.text_input("Search Bus ID, Registration, Corporation or Route")
        df = query("SELECT * FROM buses WHERE status!='Inactive'")
        if search:
            s = search.lower()
            df = df[df.apply(lambda r: s in " ".join(map(str,r.values)).lower(), axis=1)]
        st.dataframe(df, use_container_width=True, hide_index=True)

    with t2:
        with st.form("bus_form"):
            a,b,c = st.columns(3)
            bus_id = a.text_input("Bus ID *")
            reg_no = b.text_input("Registration No. *")
            corp = c.selectbox("Corporation", CORPORATIONS)
            a,b,c = st.columns(3)
            route_no = a.text_input("Route No.")
            route = b.text_input("Route")
            driver = c.text_input("Driver", "Government Driver")
            a,b,c = st.columns(3)
            bus_type = a.selectbox("Bus Type", BUS_TYPES)
            capacity = b.number_input("Capacity", 1, 200, 50)
            available = c.number_input("Available Seats", 0, 200, 50)
            a,b = st.columns(2)
            status = a.selectbox("Status", STATUSES)
            depot = b.text_input("Depot")
            save = st.form_submit_button("💾 SAVE / UPDATE BUS", use_container_width=True)

        if save:
            if not bus_id or not reg_no:
                st.error("Bus ID and Registration No. are required.")
            else:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                c = db()
                c.execute("""INSERT INTO buses VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(bus_id) DO UPDATE SET
                    reg_no=excluded.reg_no, corporation=excluded.corporation,
                    route_no=excluded.route_no, route=excluded.route,
                    driver=excluded.driver, bus_type=excluded.bus_type,
                    capacity=excluded.capacity,
                    available_seats=excluded.available_seats,
                    status=excluded.status, depot=excluded.depot,
                    updated_at=excluded.updated_at""",
                    (bus_id.upper(),reg_no.upper(),corp,route_no,route,driver,
                     bus_type,int(capacity),min(int(available),int(capacity)),
                     status,depot,now))
                c.commit()
                c.close()
                st.success("Bus saved successfully.")
                st.rerun()

    with t3:
        ids = query("SELECT bus_id FROM buses WHERE status!='Inactive'").bus_id.tolist()
        if ids:
            selected = st.selectbox("Select Bus", ids)
            if st.button("Deactivate Bus", type="primary"):
                run("UPDATE buses SET status='Inactive' WHERE bus_id=?", (selected,))
                st.success("Bus deactivated.")
                st.rerun()

# ROUTES
elif page == "🗺️ Route Management":
    st.subheader("Route Management")
    with st.form("route_form"):
        a,b = st.columns(2)
        route_no = a.text_input("Route No. *")
        source = b.text_input("Source *")
        a,b = st.columns(2)
        destination = a.text_input("Destination *")
        distance = b.number_input("Distance (KM)", 0.0, 5000.0, 0.0)
        stops = st.text_area("Stops (comma separated)")
        save = st.form_submit_button("💾 SAVE / UPDATE ROUTE", use_container_width=True)

    if save:
        if not route_no or not source or not destination:
            st.error("Route No., Source and Destination are required.")
        else:
            run("""INSERT INTO routes VALUES(?,?,?,?,?,1)
                ON CONFLICT(route_no) DO UPDATE SET
                source=excluded.source, destination=excluded.destination,
                stops=excluded.stops, distance_km=excluded.distance_km, active=1""",
                (route_no.upper(),source,destination,stops,distance))
            st.success("Route saved.")
            st.rerun()

    st.dataframe(query("SELECT * FROM routes WHERE active=1"),
                 use_container_width=True, hide_index=True)

# PASSENGERS
elif page == "🎫 Passenger Management":
    st.subheader("Passenger Management")
    t1,t2 = st.tabs(["🎫 Book Ticket","🔎 Passenger Details"])

    with t1:
        buses = query("SELECT bus_id FROM buses WHERE status!='Inactive'")
        if buses.empty:
            st.warning("No active buses.")
        else:
            with st.form("ticket_form"):
                a,b,c = st.columns(3)
                name = a.text_input("Passenger Name")
                phone = b.text_input("Phone")
                bus_id = c.selectbox("Bus", buses.bus_id.tolist())
                a,b,c = st.columns(3)
                source = a.text_input("From")
                destination = b.text_input("To")
                seats = c.number_input("Seats",1,10,1)
                fare = st.number_input("Fare per Seat (₹)",0.0,10000.0,50.0)
                book = st.form_submit_button("🎟️ BOOK TICKET", use_container_width=True)

            if book:
                row = query("SELECT * FROM buses WHERE bus_id=?", (bus_id,)).iloc[0]
                if not name or not phone:
                    st.error("Enter passenger name and phone.")
                elif seats > int(row.available_seats):
                    st.error(f"Only {int(row.available_seats)} seats available.")
                else:
                    pnr = "PNR" + datetime.now().strftime("%y%m%d%H%M%S%f")[-10:]
                    run("""INSERT INTO passengers VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                        (pnr,name,phone,bus_id,str(row.route_no),source,destination,
                         int(seats),float(seats*fare),"Booked",
                         datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    run("UPDATE buses SET available_seats=available_seats-? WHERE bus_id=?",
                        (int(seats),bus_id))
                    st.success(f"Ticket booked successfully. PNR: {pnr}")

    with t2:
        p = query("SELECT * FROM passengers ORDER BY booked_at DESC")
        st.dataframe(p, use_container_width=True, hide_index=True)
        if not p.empty:
            pnr = st.selectbox("PNR to cancel", p.pnr.tolist())
            if st.button("Cancel Ticket", type="primary"):
                row = p[p.pnr == pnr].iloc[0]
                if row.status == "Booked":
                    run("UPDATE passengers SET status='Cancelled' WHERE pnr=?", (pnr,))
                    run("UPDATE buses SET available_seats=available_seats+? WHERE bus_id=?",
                        (int(row.seats),row.bus_id))
                    st.success("Ticket cancelled and seats restored.")
                    st.rerun()
                else:
                    st.warning("This ticket is already cancelled.")

# FARE
elif page == "💰 Fare Calculator":
    st.subheader("Fare Calculator")
    a,b,c = st.columns(3)
    distance = a.number_input("Distance (KM)",1.0,2000.0,100.0)
    rate = b.number_input("Rate per KM (₹)",0.0,100.0,0.75)
    passengers = c.number_input("Passengers",1,100,1)
    st.metric("Estimated Total Fare", f"₹{distance * rate * passengers:,.2f}")
    st.caption("Use the verified rate supplied by your project/admin for real fares.")

# ANALYTICS
elif page == "📊 Analytics":
    st.subheader("Fleet & Passenger Analytics")
    buses = query("SELECT * FROM buses")
    p = query("SELECT * FROM passengers")

    active = buses[buses.status != "Inactive"].copy()
    if not active.empty:
        st.write("### Fleet by Corporation")
        st.bar_chart(active.groupby("corporation").size())

        active["Passengers"] = active["capacity"] - active["available_seats"]
        active["Load %"] = (active["Passengers"] / active["capacity"] * 100).round(1)
        st.write("### Passenger Load Analysis")
        st.dataframe(active[["bus_id","corporation","capacity","Passengers",
                             "available_seats","Load %","status"]],
                     use_container_width=True, hide_index=True)

    st.write("### Peak-Hour Analysis")
    if not p.empty:
        p["hour"] = pd.to_datetime(p.booked_at, errors="coerce").dt.hour
        peak = p[p.status=="Booked"].groupby("hour").size()
        if not peak.empty:
            st.bar_chart(peak)
        else:
            st.info("No booked-ticket data yet.")
    else:
        st.info("Book tickets to generate peak-hour data.")

# STATUS REPORT
elif page == "📋 Bus Status Report":
    st.subheader("Bus Status Report")
    df = query("""SELECT bus_id, reg_no, corporation, route_no, route,
                  capacity, capacity-available_seats AS passengers,
                  available_seats, status
                  FROM buses WHERE status!='Inactive'""")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode(),
                       "bus_status_report.csv", "text/csv")

# ADMIN
elif page == "🔐 Admin Portal":
    if not admin:
        st.warning("Admin login required.")
        st.info("Demo password: admin123")
    else:
        st.subheader("🔐 ADMIN PORTAL")
        st.success("Administrator access active.")

        st.write("### Automatic Fleet Import / Update")
        st.caption("Upload a VERIFIED CSV. Existing Bus IDs are updated and new Bus IDs are added automatically.")

        upload = st.file_uploader("Upload Fleet CSV", type=["csv"])
        if upload:
            data = pd.read_csv(upload)
            required = ["bus_id","reg_no","corporation","route_no","route","driver",
                        "bus_type","capacity","available_seats","status","depot"]
            missing = [x for x in required if x not in data.columns]

            if missing:
                st.error("Missing columns: " + ", ".join(missing))
            else:
                st.dataframe(data.head(20), use_container_width=True, hide_index=True)
                if st.button("⬆️ IMPORT / UPDATE FLEET", type="primary"):
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    c = db()
                    for _, r in data.iterrows():
                        capacity = int(r["capacity"])
                        available = min(int(r["available_seats"]), capacity)
                        c.execute("""INSERT INTO buses VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                            ON CONFLICT(bus_id) DO UPDATE SET
                            reg_no=excluded.reg_no, corporation=excluded.corporation,
                            route_no=excluded.route_no, route=excluded.route,
                            driver=excluded.driver, bus_type=excluded.bus_type,
                            capacity=excluded.capacity,
                            available_seats=excluded.available_seats,
                            status=excluded.status, depot=excluded.depot,
                            updated_at=excluded.updated_at""",
                            (str(r["bus_id"]),str(r["reg_no"]),str(r["corporation"]),
                             str(r["route_no"]),str(r["route"]),str(r["driver"]),
                             str(r["bus_type"]),capacity,available,str(r["status"]),
                             str(r["depot"]),now))
                    c.commit()
                    c.close()
                    st.success(f"{len(data)} buses imported/updated.")
                    st.rerun()

        st.write("### Database Export")
        fleet = query("SELECT * FROM buses")
        st.download_button("⬇️ Download Fleet CSV", fleet.to_csv(index=False).encode(),
                           "smart_bus_fleet.csv", "text/csv")

        if st.button("🚪 Logout"):
            st.session_state.admin = False
            st.rerun()

st.caption("SMART BUS • Python + Streamlit")
