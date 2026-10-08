# app.py
# Smart Bus - Bus Route & Passenger Management System
# Python 3.13 | Tkinter | SQLite | Standard Library Only

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import random
import webbrowser
import math

DB_NAME = "smart_bus.db"


# ============================================================
# DATABASE
# ============================================================

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.seed_data()

    def create_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS buses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bus_id TEXT UNIQUE NOT NULL,
                registration TEXT,
                route_number TEXT,
                driver TEXT,
                capacity INTEGER NOT NULL,
                available_seats INTEGER NOT NULL,
                status TEXT NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_number TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                destination TEXT NOT NULL,
                distance REAL DEFAULT 0,
                fare REAL DEFAULT 0,
                stops TEXT DEFAULT ''
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS passengers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                age INTEGER,
                gender TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pnr TEXT UNIQUE NOT NULL,
                passenger_name TEXT NOT NULL,
                phone TEXT,
                bus_id TEXT,
                route_number TEXT,
                source TEXT,
                destination TEXT,
                travel_date TEXT,
                seat_number TEXT,
                fare REAL,
                scheme TEXT,
                status TEXT DEFAULT 'CONFIRMED',
                created_at TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS official_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                url TEXT,
                category TEXT
            )
        """)

        self.conn.commit()

    def seed_data(self):
        cur = self.conn.cursor()

        cur.execute("SELECT COUNT(*) FROM buses")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO buses
                (bus_id, registration, route_number, driver, capacity,
                 available_seats, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "BUS101",
                "TN 33 AB 1234",
                "R12",
                "Demo Driver",
                50,
                8,
                "Running"
            ))

            cur.execute("""
                INSERT INTO buses
                (bus_id, registration, route_number, driver, capacity,
                 available_seats, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "BUS102",
                "TN 38 CD 5678",
                "R13",
                "Kumar",
                52,
                30,
                "Available"
            ))

        cur.execute("SELECT COUNT(*) FROM routes")
        if cur.fetchone()[0] == 0:
            routes = [
                ("R12", "Erode", "Coimbatore", 100, 120,
                 "Erode, Perundurai, Chithode, Bhavani, Avinashi, Coimbatore"),
                ("R13", "Salem", "Erode", 65, 90,
                 "Salem, Sankari, Bhavani, Erode"),
                ("R14", "Chennai", "Coimbatore", 510, 550,
                 "Chennai, Vellore, Salem, Erode, Tiruppur, Coimbatore"),
                ("R15", "Madurai", "Coimbatore", 215, 260,
                 "Madurai, Dindigul, Karur, Erode, Tiruppur, Coimbatore")
            ]

            cur.executemany("""
                INSERT INTO routes
                (route_number, source, destination, distance, fare, stops)
                VALUES (?, ?, ?, ?, ?, ?)
            """, routes)

        cur.execute("SELECT COUNT(*) FROM official_links")
        if cur.fetchone()[0] == 0:
            links = [
                ("TNSTC Online Booking",
                 "https://www.tnstc.in/OTRSOnline/",
                 "Transport"),
                ("TNSTC Main Website",
                 "https://www.tnstc.in/",
                 "Transport"),
                ("MTC Chennai",
                 "https://mtcbus.tn.gov.in/",
                 "Transport"),
                ("Tamil Nadu Government",
                 "https://www.tn.gov.in/",
                 "Government"),
                ("TN e-Sevai",
                 "https://www.tnesevai.tn.gov.in/",
                 "Government"),
                ("Parivahan",
                 "https://parivahan.gov.in/",
                 "Transport"),
                ("Google Maps",
                 "https://www.google.com/maps/",
                 "Maps"),
                ("Tamil Nadu Police",
                 "https://eservices.tnpolice.gov.in/",
                 "Emergency")
            ]

            cur.executemany("""
                INSERT INTO official_links (name, url, category)
                VALUES (?, ?, ?)
            """, links)

        self.conn.commit()

    def execute(self, query, params=()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        self.conn.commit()
        return cur

    def fetchall(self, query, params=()):
        return self.conn.execute(query, params).fetchall()

    def fetchone(self, query, params=()):
        return self.conn.execute(query, params).fetchone()


# ============================================================
# MAIN APPLICATION
# ============================================================

class SmartBusApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("SMART BUS - Bus Route & Passenger Management System")
        self.geometry("1400x850")
        self.minsize(1100, 700)

        self.db = Database()

        self.configure(bg="#eef3f8")

        self.setup_style()
        self.create_header()
        self.create_navigation()
        self.create_main_area()
        self.show_dashboard()

    # --------------------------------------------------------
    # STYLE
    # --------------------------------------------------------

    def setup_style(self):
        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Treeview",
            rowheight=30,
            font=("Segoe UI", 10)
        )

        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold")
        )

        style.configure(
            "TButton",
            font=("Segoe UI", 10, "bold"),
            padding=7
        )

        style.configure(
            "TLabel",
            background="#eef3f8",
            font=("Segoe UI", 10)
        )

        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 22, "bold"),
            background="#12355b",
            foreground="white"
        )

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    def create_header(self):
        header = tk.Frame(self, bg="#12355b", height=75)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="🚌 SMART BUS",
            font=("Segoe UI", 24, "bold"),
            fg="white",
            bg="#12355b"
        ).pack(side="left", padx=25)

        tk.Label(
            header,
            text="Bus Route & Passenger Management System",
            font=("Segoe UI", 12),
            fg="#dcecff",
            bg="#12355b"
        ).pack(side="left")

        tk.Button(
            header,
            text="🚨 Emergency",
            command=self.show_emergency,
            bg="#c62828",
            fg="white",
            activebackground="#8e0000",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=15,
            pady=8
        ).pack(side="right", padx=20)

    # --------------------------------------------------------
    # NAVIGATION
    # --------------------------------------------------------

    def create_navigation(self):
        nav = tk.Frame(self, bg="#1d4e89", height=55)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        buttons = [
            ("Dashboard", self.show_dashboard),
            ("Buses", self.show_buses),
            ("Routes", self.show_routes),
            ("Passengers", self.show_passengers),
            ("Booking", self.show_booking),
            ("PNR Search", self.show_pnr),
            ("Reports", self.show_reports),
            ("Admin", self.show_admin),
        ]

        for text, command in buttons:
            tk.Button(
                nav,
                text=text,
                command=command,
                bg="#1d4e89",
                fg="white",
                activebackground="#2867ad",
                activeforeground="white",
                relief="flat",
                font=("Segoe UI", 10, "bold"),
                padx=15
            ).pack(side="left", fill="y")

    # --------------------------------------------------------
    # MAIN AREA
    # --------------------------------------------------------

    def create_main_area(self):
        self.main = tk.Frame(self, bg="#eef3f8")
        self.main.pack(fill="both", expand=True)

    def clear_main(self):
        for widget in self.main.winfo_children():
            widget.destroy()

    def page_title(self, title, subtitle=""):
        tk.Label(
            self.main,
            text=title,
            font=("Segoe UI", 22, "bold"),
            bg="#eef3f8",
            fg="#12355b"
        ).pack(anchor="w", padx=25, pady=(20, 3))

        if subtitle:
            tk.Label(
                self.main,
                text=subtitle,
                font=("Segoe UI", 10),
                bg="#eef3f8",
                fg="#555"
            ).pack(anchor="w", padx=27, pady=(0, 15))

    # ========================================================
    # DASHBOARD
    # ========================================================

    def show_dashboard(self):
        self.clear_main()

        self.page_title(
            "Dashboard",
            "Welcome to Smart Bus Management System"
        )

        stats_frame = tk.Frame(self.main, bg="#eef3f8")
        stats_frame.pack(fill="x", padx=25)

        buses = self.db.fetchone("SELECT COUNT(*) AS c FROM buses")["c"]
        routes = self.db.fetchone("SELECT COUNT(*) AS c FROM routes")["c"]
        passengers = self.db.fetchone(
            "SELECT COUNT(*) AS c FROM passengers"
        )["c"]
        bookings = self.db.fetchone(
            "SELECT COUNT(*) AS c FROM bookings WHERE status='CONFIRMED'"
        )["c"]

        cards = [
            ("🚌", "Total Buses", buses),
            ("🗺", "Routes", routes),
            ("👥", "Passengers", passengers),
            ("🎫", "Confirmed Tickets", bookings),
        ]

        for icon, title, value in cards:
            card = tk.Frame(
                stats_frame,
                bg="white",
                highlightbackground="#d4dce5",
                highlightthickness=1
            )
            card.pack(
                side="left",
                fill="both",
                expand=True,
                padx=7
            )

            tk.Label(
                card,
                text=icon,
                font=("Segoe UI Emoji", 28),
                bg="white"
            ).pack(pady=(15, 0))

            tk.Label(
                card,
                text=str(value),
                font=("Segoe UI", 24, "bold"),
                fg="#12355b",
                bg="white"
            ).pack()

            tk.Label(
                card,
                text=title,
                font=("Segoe UI", 10),
                fg="#666",
                bg="white"
            ).pack(pady=(0, 15))

        # Challenge section
        challenge = tk.LabelFrame(
            self.main,
            text=" Special Challenge Bus ",
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg="#12355b",
            padx=15,
            pady=15
        )
        challenge.pack(fill="x", padx=25, pady=25)

        values = [
            ("Bus", "BUS101"),
            ("Route", "R12"),
            ("Source", "Erode"),
            ("Destination", "Coimbatore"),
            ("Capacity", "50"),
            ("Passengers", "42"),
            ("Available Seats", "8"),
            ("Status", "Running")
        ]

        for i, (label, value) in enumerate(values):
            frame = tk.Frame(challenge, bg="white")
            frame.grid(
                row=i // 4,
                column=i % 4,
                sticky="ew",
                padx=10,
                pady=10
            )

            tk.Label(
                frame,
                text=label,
                bg="white",
                fg="#777",
                font=("Segoe UI", 9)
            ).pack()

            tk.Label(
                frame,
                text=value,
                bg="white",
                fg="#12355b",
                font=("Segoe UI", 12, "bold")
            ).pack()

        for i in range(4):
            challenge.columnconfigure(i, weight=1)

        # Quick actions
        quick = tk.LabelFrame(
            self.main,
            text=" Quick Actions ",
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg="#12355b",
            padx=15,
            pady=15
        )
        quick.pack(fill="x", padx=25)

        actions = [
            ("🎫 Book Ticket", self.show_booking),
            ("🚌 Manage Buses", self.show_buses),
            ("🗺 Manage Routes", self.show_routes),
            ("👥 Passengers", self.show_passengers),
            ("🔎 Search PNR", self.show_pnr),
            ("📊 Reports", self.show_reports)
        ]

        for text, command in actions:
            tk.Button(
                quick,
                text=text,
                command=command,
                bg="#1d4e89",
                fg="white",
                relief="flat",
                font=("Segoe UI", 10, "bold"),
                padx=15,
                pady=10
            ).pack(side="left", padx=7, pady=8)

    # ========================================================
    # BUSES
    # ========================================================

    def show_buses(self):
        self.clear_main()

        self.page_title(
            "Bus Management",
            "Add, update, search and manage buses"
        )

        form = tk.LabelFrame(
            self.main,
            text=" Bus Details ",
            bg="white",
            fg="#12355b",
            font=("Segoe UI", 11, "bold"),
            padx=15,
            pady=15
        )
        form.pack(fill="x", padx=25)

        fields = [
            "Bus ID",
            "Registration",
            "Route Number",
            "Driver",
            "Capacity",
            "Available Seats",
            "Status"
        ]

        entries = {}

        for i, field in enumerate(fields):
            tk.Label(
                form,
                text=field,
                bg="white"
            ).grid(
                row=i // 4 * 2,
                column=i % 4,
                sticky="w",
                padx=8,
                pady=(5, 0)
            )

            if field == "Status":
                entry = ttk.Combobox(
                    form,
                    values=["Running", "Available", "Maintenance", "Inactive"],
                    state="readonly"
                )
                entry.set("Available")
            else:
                entry = tk.Entry(form, width=25)

            entry.grid(
                row=i // 4 * 2 + 1,
                column=i % 4,
                sticky="ew",
                padx=8,
                pady=(0, 8)
            )

            entries[field] = entry

        for i in range(4):
            form.columnconfigure(i, weight=1)

        def add_bus():
            try:
                capacity = int(entries["Capacity"].get())
                available = int(entries["Available Seats"].get())

                if capacity <= 0:
                    raise ValueError

                self.db.execute("""
                    INSERT INTO buses
                    (bus_id, registration, route_number, driver,
                     capacity, available_seats, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    entries["Bus ID"].get().strip(),
                    entries["Registration"].get().strip(),
                    entries["Route Number"].get().strip(),
                    entries["Driver"].get().strip(),
                    capacity,
                    available,
                    entries["Status"].get()
                ))

                messagebox.showinfo("Success", "Bus added successfully.")
                refresh()

            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Capacity and available seats must be numbers."
                )
            except sqlite3.IntegrityError:
                messagebox.showerror(
                    "Error",
                    "Bus ID already exists."
                )

        def delete_bus():
            selected = tree.selection()

            if not selected:
                messagebox.showwarning(
                    "Select Bus",
                    "Please select a bus."
                )
                return

            values = tree.item(selected[0], "values")

            if messagebox.askyesno(
                "Delete",
                f"Delete bus {values[0]}?"
            ):
                self.db.execute(
                    "DELETE FROM buses WHERE bus_id=?",
                    (values[0],)
                )
                refresh()

        def refresh():
            for item in tree.get_children():
                tree.delete(item)

            rows = self.db.fetchall("""
                SELECT bus_id, registration, route_number, driver,
                       capacity, available_seats, status
                FROM buses
                ORDER BY bus_id
            """)

            for row in rows:
                tree.insert("", "end", values=tuple(row))

        tk.Button(
            form,
            text="➕ Add Bus",
            command=add_bus,
            bg="#198754",
            fg="white",
            relief="flat",
            padx=20,
            pady=7
        ).grid(row=4, column=0, padx=8, pady=10)

        tk.Button(
            form,
            text="🗑 Delete Selected",
            command=delete_bus,
            bg="#c62828",
            fg="white",
            relief="flat",
            padx=20,
            pady=7
        ).grid(row=4, column=1, padx=8, pady=10)

        table_frame = tk.Frame(self.main, bg="#eef3f8")
        table_frame.pack(fill="both", expand=True, padx=25, pady=15)

        columns = (
            "Bus ID",
            "Registration",
            "Route",
            "Driver",
            "Capacity",
            "Available",
            "Status"
        )

        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=130)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=tree.yview
        )

        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        refresh()

    # ========================================================
    # ROUTES
    # ========================================================

    def show_routes(self):
        self.clear_main()

        self.page_title(
            "Route Management",
            "Manage routes, distances, fares and stops"
        )

        form = tk.LabelFrame(
            self.main,
            text=" Route Details ",
            bg="white",
            fg="#12355b",
            font=("Segoe UI", 11, "bold"),
            padx=15,
            pady=15
        )
        form.pack(fill="x", padx=25)

        labels = [
            "Route Number",
            "Source",
            "Destination",
            "Distance (km)",
            "Fare (₹)",
            "Stops"
        ]

        entries = {}

        for i, label in enumerate(labels):
            tk.Label(
                form,
                text=label,
                bg="white"
            ).grid(
                row=0,
                column=i,
                padx=7,
                sticky="w"
            )

            entry = tk.Entry(form, width=22)
            entry.grid(
                row=1,
                column=i,
                padx=7,
                pady=7
            )

            entries[label] = entry

        def add_route():
            try:
                distance = float(entries["Distance (km)"].get())
                fare = float(entries["Fare (₹)"].get())

                self.db.execute("""
                    INSERT INTO routes
                    (route_number, source, destination,
                     distance, fare, stops)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    entries["Route Number"].get().strip(),
                    entries["Source"].get().strip(),
                    entries["Destination"].get().strip(),
                    distance,
                    fare,
                    entries["Stops"].get().strip()
                ))

                messagebox.showinfo(
                    "Success",
                    "Route added successfully."
                )
                refresh()

            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Distance and fare must be numeric."
                )
            except sqlite3.IntegrityError:
                messagebox.showerror(
                    "Error",
                    "Route number already exists."
                )

        tk.Button(
            form,
            text="➕ Add Route",
            command=add_route,
            bg="#198754",
            fg="white",
            relief="flat",
            padx=20
        ).grid(row=2, column=0, pady=10)

        table_frame = tk.Frame(self.main, bg="#eef3f8")
        table_frame.pack(fill="both", expand=True, padx=25, pady=15)

        columns = (
            "Route",
            "Source",
            "Destination",
            "Distance",
            "Fare",
            "Stops"
        )

        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        tree.pack(fill="both", expand=True)

        def refresh():
            for item in tree.get_children():
                tree.delete(item)

            rows = self.db.fetchall("""
                SELECT route_number, source, destination,
                       distance, fare, stops
                FROM routes
                ORDER BY route_number
            """)

            for row in rows:
                tree.insert("", "end", values=tuple(row))

        refresh()

    # ========================================================
    # PASSENGERS
    # ========================================================

    def show_passengers(self):
        self.clear_main()

        self.page_title(
            "Passenger Management",
            "Add and manage passenger information"
        )

        form = tk.LabelFrame(
            self.main,
            text=" Passenger Details ",
            bg="white",
            fg="#12355b",
            font=("Segoe UI", 11, "bold"),
            padx=15,
            pady=15
        )
        form.pack(fill="x", padx=25)

        name = tk.Entry(form, width=25)
        phone = tk.Entry(form, width=20)
        age = tk.Entry(form, width=10)
        gender = ttk.Combobox(
            form,
            values=["Male", "Female", "Other"],
            state="readonly",
            width=15
        )
        gender.set("Male")

        fields = [
            ("Name", name),
            ("Phone", phone),
            ("Age", age),
            ("Gender", gender)
        ]

        for i, (label, widget) in enumerate(fields):
            tk.Label(
                form,
                text=label,
                bg="white"
            ).grid(row=0, column=i, padx=10)

            widget.grid(row=1, column=i, padx=10, pady=7)

        def add_passenger():
            if not name.get().strip():
                messagebox.showwarning(
                    "Required",
                    "Passenger name is required."
                )
                return

            try:
                passenger_age = int(age.get())
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Age must be a number."
                )
                return

            self.db.execute("""
                INSERT INTO passengers
                (name, phone, age, gender)
                VALUES (?, ?, ?, ?)
            """, (
                name.get().strip(),
                phone.get().strip(),
                passenger_age,
                gender.get()
            ))

            messagebox.showinfo(
                "Success",
                "Passenger added successfully."
            )

            name.delete(0, "end")
            phone.delete(0, "end")
            age.delete(0, "end")
            refresh()

        tk.Button(
            form,
            text="➕ Add Passenger",
            command=add_passenger,
            bg="#198754",
            fg="white",
            relief="flat",
            padx=20
        ).grid(row=2, column=0, pady=10)

        table_frame = tk.Frame(self.main, bg="#eef3f8")
        table_frame.pack(fill="both", expand=True, padx=25, pady=15)

        columns = (
            "ID",
            "Name",
            "Phone",
            "Age",
            "Gender"
        )

        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        tree.pack(fill="both", expand=True)

        def refresh():
            for item in tree.get_children():
                tree.delete(item)

            rows = self.db.fetchall("""
                SELECT id, name, phone, age, gender
                FROM passengers
                ORDER BY id DESC
            """)

            for row in rows:
                tree.insert("", "end", values=tuple(row))

        refresh()

    # ========================================================
    # BOOKING
    # ========================================================

    def show_booking(self):
        self.clear_main()

        self.page_title(
            "Ticket Booking",
            "Book a Smart Bus ticket"
        )

        container = tk.Frame(self.main, bg="white")
        container.pack(fill="both", expand=True, padx=25, pady=5)

        fields = [
            "Passenger Name",
            "Phone",
            "Bus ID",
            "Route",
            "Source",
            "Destination",
            "Travel Date",
            "Seat Number",
            "Scheme"
        ]

        entries = {}

        for i, field in enumerate(fields):
            row = i // 3
            col = i % 3

            tk.Label(
                container,
                text=field,
                bg="white",
                fg="#444"
            ).grid(
                row=row * 2,
                column=col,
                sticky="w",
                padx=25,
                pady=(20, 3)
            )

            if field == "Scheme":
                widget = ttk.Combobox(
                    container,
                    values=[
                        "GENERAL",
                        "WOMAN-ZERO",
                        "STUDENT",
                        "SENIOR"
                    ],
                    state="readonly",
                    width=30
                )
                widget.set("GENERAL")
            elif field == "Bus ID":
                widget = ttk.Combobox(
                    container,
                    values=[
                        row["bus_id"]
                        for row in self.db.fetchall(
                            "SELECT bus_id FROM buses ORDER BY bus_id"
                        )
                    ],
                    width=30
                )
            elif field == "Route":
                widget = ttk.Combobox(
                    container,
                    values=[
                        row["route_number"]
                        for row in self.db.fetchall(
                            "SELECT route_number FROM routes ORDER BY route_number"
                        )
                    ],
                    width=30
                )
            else:
                widget = tk.Entry(container, width=32)

            widget.grid(
                row=row * 2 + 1,
                column=col,
                padx=25,
                pady=(0, 10),
                sticky="ew"
            )

            entries[field] = widget

        def calculate_fare():
            route = entries["Route"].get().strip()

            row = self.db.fetchone(
                "SELECT fare, distance FROM routes WHERE route_number=?",
                (route,)
            )

            if not row:
                messagebox.showerror(
                    "Error",
                    "Route not found."
                )
                return

            fare = float(row["fare"])

            scheme = entries["Scheme"].get()

            if scheme == "WOMAN-ZERO":
                fare = 0
            elif scheme == "STUDENT":
                fare *= 0.5
            elif scheme == "SENIOR":
                fare *= 0.5

            fare_label.config(
                text=f"Estimated Fare: ₹{fare:.2f}"
            )

        def book_ticket():
            passenger = entries["Passenger Name"].get().strip()
            bus_id = entries["Bus ID"].get().strip()
            route = entries["Route"].get().strip()

            if not passenger or not bus_id or not route:
                messagebox.showwarning(
                    "Required",
                    "Passenger, Bus ID and Route are required."
                )
                return

            bus = self.db.fetchone(
                "SELECT * FROM buses WHERE bus_id=?",
                (bus_id,)
            )

            if not bus:
                messagebox.showerror(
                    "Error",
                    "Bus not found."
                )
                return

            if int(bus["available_seats"]) <= 0:
                messagebox.showerror(
                    "Full",
                    "No seats available."
                )
                return

            route_data = self.db.fetchone(
                "SELECT * FROM routes WHERE route_number=?",
                (route,)
            )

            if not route_data:
                messagebox.showerror(
                    "Error",
                    "Route not found."
                )
                return

            fare = float(route_data["fare"])

            scheme = entries["Scheme"].get()

            if scheme == "WOMAN-ZERO":
                fare = 0
            elif scheme in ("STUDENT", "SENIOR"):
                fare *= 0.5

            available = int(bus["available_seats"])
            seat = entries["Seat Number"].get().strip()

            if not seat:
                occupied = self.db.fetchall("""
                    SELECT seat_number
                    FROM bookings
                    WHERE bus_id=? AND travel_date=? AND status='CONFIRMED'
                """, (
                    bus_id,
                    entries["Travel Date"].get().strip()
                ))

                occupied_set = {
                    str(row["seat_number"])
                    for row in occupied
                }

                for number in range(1, int(bus["capacity"]) + 1):
                    if str(number) not in occupied_set:
                        seat = str(number)
                        break

            pnr = (
                "SB"
                + datetime.now().strftime("%y%m%d")
                + str(random.randint(1000, 9999))
            )

            try:
                self.db.execute("""
                    INSERT INTO bookings
                    (pnr, passenger_name, phone, bus_id,
                     route_number, source, destination,
                     travel_date, seat_number, fare,
                     scheme, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pnr,
                    passenger,
                    entries["Phone"].get().strip(),
                    bus_id,
                    route,
                    entries["Source"].get().strip(),
                    entries["Destination"].get().strip(),
                    entries["Travel Date"].get().strip(),
                    seat,
                    fare,
                    scheme,
                    "CONFIRMED",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                self.db.execute("""
                    UPDATE buses
                    SET available_seats=available_seats-1
                    WHERE bus_id=?
                """, (bus_id,))

                self.db.execute("""
                    INSERT INTO passengers
                    (name, phone, age, gender)
                    VALUES (?, ?, ?, ?)
                """, (
                    passenger,
                    entries["Phone"].get().strip(),
                    0,
                    "Not Specified"
                ))

                messagebox.showinfo(
                    "Booking Successful",
                    f"Ticket booked successfully!\n\n"
                    f"PNR: {pnr}\n"
                    f"Seat: {seat}\n"
                    f"Fare: ₹{fare:.2f}\n"
                    f"Scheme: {scheme}"
                )

            except sqlite3.IntegrityError:
                messagebox.showerror(
                    "Booking Error",
                    "Could not create booking. Please try again."
                )

        fare_label = tk.Label(
            container,
            text="Estimated Fare: ₹0.00",
            bg="white",
            fg="#198754",
            font=("Segoe UI", 18, "bold")
        )

        fare_label.grid(
            row=7,
            column=0,
            columnspan=3,
            pady=20
        )

        tk.Button(
            container,
            text="💰 Calculate Fare",
            command=calculate_fare,
            bg="#1d4e89",
            fg="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=10
        ).grid(
            row=8,
            column=0,
            padx=20,
            pady=10
        )

        tk.Button(
            container,
            text="🎫 BOOK TICKET",
            command=book_ticket,
            bg="#198754",
            fg="white",
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padx=30,
            pady=12
        ).grid(
            row=8,
            column=1,
            padx=20,
            pady=10
        )

    # ========================================================
    # PNR SEARCH
    # ========================================================

    def show_pnr(self):
        self.clear_main()

        self.page_title(
            "PNR Search & Ticket Cancellation",
            "Search your booking using the PNR number"
        )

        search_frame = tk.Frame(
            self.main,
            bg="white",
            padx=25,
            pady=25
        )
        search_frame.pack(fill="x", padx=25)

        tk.Label(
            search_frame,
            text="PNR Number:",
            bg="white",
            font=("Segoe UI", 11, "bold")
        ).pack(side="left")

        pnr_entry = tk.Entry(
            search_frame,
            width=35,
            font=("Segoe UI", 11)
        )
        pnr_entry.pack(side="left", padx=15)

        result = tk.Text(
            self.main,
            height=18,
            font=("Consolas", 11),
            bg="white",
            relief="flat",
            padx=20,
            pady=20
        )
        result.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=20
        )

        def search():
            result.delete("1.0", "end")

            pnr = pnr_entry.get().strip()

            row = self.db.fetchone(
                "SELECT * FROM bookings WHERE pnr=?",
                (pnr,)
            )

            if not row:
                result.insert(
                    "end",
                    "No booking found for this PNR."
                )
                return

            text = f"""
SMART BUS
========================================
PNR             : {row['pnr']}
Passenger       : {row['passenger_name']}
Phone           : {row['phone']}
Bus ID          : {row['bus_id']}
Route           : {row['route_number']}
Source          : {row['source']}
Destination     : {row['destination']}
Travel Date     : {row['travel_date']}
Seat Number     : {row['seat_number']}
Fare            : ₹{row['fare']:.2f}
Scheme          : {row['scheme']}
Status          : {row['status']}
Booked At       : {row['created_at']}
========================================
"""

            result.insert("end", text)

        def cancel():
            pnr = pnr_entry.get().strip()

            row = self.db.fetchone(
                "SELECT * FROM bookings WHERE pnr=?",
                (pnr,)
            )

            if not row:
                messagebox.showerror(
                    "Error",
                    "PNR not found."
                )
                return

            if row["status"] == "CANCELLED":
                messagebox.showinfo(
                    "Already Cancelled",
                    "This ticket is already cancelled."
                )
                return

            if not messagebox.askyesno(
                "Cancel Ticket",
                f"Cancel ticket {pnr}?"
            ):
                return

            self.db.execute("""
                UPDATE bookings
                SET status='CANCELLED'
                WHERE pnr=?
            """, (pnr,))

            self.db.execute("""
                UPDATE buses
                SET available_seats=available_seats+1
                WHERE bus_id=?
            """, (row["bus_id"],))

            messagebox.showinfo(
                "Cancelled",
                "Ticket cancelled successfully."
            )

            search()

        tk.Button(
            search_frame,
            text="🔎 Search",
            command=search,
            bg="#1d4e89",
            fg="white",
            relief="flat",
            padx=20
        ).pack(side="left")

        tk.Button(
            search_frame,
            text="❌ Cancel Ticket",
            command=cancel,
            bg="#c62828",
            fg="white",
            relief="flat",
            padx=20
        ).pack(side="left", padx=10)

    # ========================================================
    # REPORTS
    # ========================================================

    def show_reports(self):
        self.clear_main()

        self.page_title(
            "Reports & Passenger Load Analysis",
            "View current Smart Bus statistics"
        )

        frame = tk.Frame(self.main, bg="white")
        frame.pack(fill="both", expand=True, padx=25, pady=10)

        buses = self.db.fetchall(
            "SELECT * FROM buses ORDER BY bus_id"
        )

        columns = (
            "Bus",
            "Route",
            "Capacity",
            "Available",
            "Passengers",
            "Load %",
            "Status"
        )

        tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings"
        )

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        tree.pack(fill="both", expand=True)

        for bus in buses:
            capacity = int(bus["capacity"])
            available = int(bus["available_seats"])
            passengers = capacity - available

            load = (
                passengers / capacity * 100
                if capacity else 0
            )

            tree.insert(
                "",
                "end",
                values=(
                    bus["bus_id"],
                    bus["route_number"],
                    capacity,
                    available,
                    passengers,
                    f"{load:.1f}%",
                    bus["status"]
                )
            )

        total = self.db.fetchone(
            "SELECT COUNT(*) AS c FROM bookings WHERE status='CONFIRMED'"
        )["c"]

        revenue = self.db.fetchone(
            "SELECT COALESCE(SUM(fare),0) AS total "
            "FROM bookings WHERE status='CONFIRMED'"
        )["total"]

        bottom = tk.Frame(
            self.main,
            bg="#eef3f8"
        )
        bottom.pack(fill="x", padx=25, pady=15)

        tk.Label(
            bottom,
            text=f"Confirmed Bookings: {total}",
            font=("Segoe UI", 12, "bold"),
            bg="#eef3f8",
            fg="#12355b"
        ).pack(side="left", padx=20)

        tk.Label(
            bottom,
            text=f"Total Revenue: ₹{revenue:.2f}",
            font=("Segoe UI", 12, "bold"),
            bg="#eef3f8",
            fg="#198754"
        ).pack(side="left", padx=20)

    # ========================================================
    # ADMIN
    # ========================================================

    def show_admin(self):
        self.clear_main()

        self.page_title(
            "Admin Dashboard",
            "Official transport websites and useful government services"
        )

        frame = tk.Frame(self.main, bg="white")
        frame.pack(fill="both", expand=True, padx=25, pady=10)

        columns = ("Name", "Category", "URL")

        tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings"
        )

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=250)

        tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        links = self.db.fetchall("""
            SELECT name, category, url
            FROM official_links
            ORDER BY category, name
        """)

        for row in links:
            tree.insert(
                "",
                "end",
                values=(
                    row["name"],
                    row["category"],
                    row["url"]
                )
            )

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=tree.yview
        )

        tree.configure(
            yscrollcommand=scrollbar.set
        )

        scrollbar.pack(side="right", fill="y")

        def open_link():
            selected = tree.selection()

            if not selected:
                messagebox.showwarning(
                    "Select",
                    "Please select a website."
                )
                return

            values = tree.item(
                selected[0],
                "values"
            )

            webbrowser.open(values[2])

        tk.Button(
            self.main,
            text="🌐 Open Selected Official Website",
            command=open_link,
            bg="#1d4e89",
            fg="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=10
        ).pack(pady=10)

    # ========================================================
    # EMERGENCY
    # ========================================================

    def show_emergency(self):
        window = tk.Toplevel(self)
        window.title("Emergency & Important Helplines")
        window.geometry("600x600")
        window.configure(bg="white")
        window.transient(self)

        tk.Label(
            window,
            text="🚨 Emergency & Helplines",
            font=("Segoe UI", 20, "bold"),
            bg="white",
            fg="#c62828"
        ).pack(pady=20)

        contacts = [
            ("Police", "100 / 112"),
            ("Ambulance", "108"),
            ("Fire & Rescue", "101"),
            ("Women Helpline", "181"),
            ("Child Helpline", "1098"),
            ("Railway Helpline", "139"),
            ("MTC Customer Care", "149"),
            ("MTC Customer Care Mobile", "9445030516"),
            ("Tamil Nadu Transport Authority", "044-28528030")
        ]

        for name, number in contacts:
            row = tk.Frame(
                window,
                bg="white"
            )
            row.pack(fill="x", padx=40, pady=6)

            tk.Label(
                row,
                text=name,
                width=30,
                anchor="w",
                bg="white",
                font=("Segoe UI", 11, "bold")
            ).pack(side="left")

            tk.Label(
                row,
                text=number,
                bg="white",
                fg="#c62828",
                font=("Segoe UI", 11, "bold")
            ).pack(side="left")

        tk.Button(
            window,
            text="Close",
            command=window.destroy,
            bg="#12355b",
            fg="white",
            relief="flat",
            padx=30,
            pady=8
        ).pack(pady=25)


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":
    app = SmartBusApp()
    app.mainloop()
