import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import random
import json
import math
import os

# -----------------------------------------------------------------------------
# 0. SAFE HTML RENDERING HELPER (Prevents Markdown Indented Code Block Glitches)
# -----------------------------------------------------------------------------
def render_html(html_str):
    """
    Renders HTML safely in Streamlit without triggering Markdown indented code block formatting.
    Strips leading whitespace from every line so markdown-it never treats HTML tags as <pre><code>.
    """
    clean_lines = [line.strip() for line in html_str.splitlines() if line.strip()]
    st.markdown("\n".join(clean_lines), unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1. TAMIL NADU TRANSPORT REGISTRY & ADMINISTRATIVE DIVISIONS
# -----------------------------------------------------------------------------
TN_DIVISIONS = {
    "TNSTC Coimbatore": {
        "depots": ["Coimbatore Central", "Singanallur", "Ukkadam", "Mettupalayam", "Pollachi", "Sathyamangalam", "Gobichettipalayam", "Erode Central", "Tiruppur"],
        "rto_codes": ["TN-38", "TN-37", "TN-39", "TN-33", "TN-43", "TN-66", "TN-86"]
    },
    "TNSTC Salem": {
        "depots": ["Salem Central", "Mettur", "Attur", "Namakkal", "Tiruchengode", "Dharmapuri", "Hosur", "Krishnagiri"],
        "rto_codes": ["TN-27", "TN-30", "TN-34", "TN-28", "TN-29", "TN-70", "TN-77"]
    },
    "TNSTC Villupuram": {
        "depots": ["Villupuram", "Cuddalore", "Chidambaram", "Tiruvannamalai", "Kallakurichi", "Kanchipuram", "Vellore"],
        "rto_codes": ["TN-32", "TN-21", "TN-23", "TN-25", "TN-31"]
    },
    "TNSTC Kumbakonam": {
        "depots": ["Kumbakonam", "Trichy Central", "Thanjavur", "Karur", "Pudukkottai", "Nagapattinam", "Mayiladuthurai"],
        "rto_codes": ["TN-45", "TN-49", "TN-51", "TN-68", "TN-83"]
    },
    "TNSTC Madurai": {
        "depots": ["Madurai MGR Stand", "Arapalayam", "Dindigul", "Theni", "Virudhunagar", "Karaikudi"],
        "rto_codes": ["TN-57", "TN-58", "TN-59", "TN-65", "TN-67"]
    },
    "TNSTC Tirunelveli": {
        "depots": ["Tirunelveli New Stand", "Nagercoil Vadasery", "Tenkasi", "Tuticorin", "Kanyakumari"],
        "rto_codes": ["TN-72", "TN-74", "TN-69", "TN-76"]
    },
    "SETC (State Express)": {
        "depots": ["Chennai Central (KCBT)", "Coimbatore SETC", "Madurai SETC", "Trichy SETC", "Bengaluru SETC"],
        "rto_codes": ["TN-01-AN", "TN-01-N", "TN-01-AL"]
    }
}

LOCATION_REGISTRY = {
    # Kongu & Western Region
    "Erode District": ["Erode Central Bus Stand", "Sathyamangalam", "Gobichettipalayam", "Bhavani", "Perundurai", "Punjai Puliampatti", "Anthiyur", "Kavindapadi", "Bhavanisagar", "Kodumudi", "Chennimalai"],
    "Coimbatore District": ["Coimbatore (Gandhipuram)", "Coimbatore (Singanallur)", "Coimbatore (Ukkadam)", "Pollachi", "Mettupalayam", "Annur", "Sulur", "Valparai", "Kinathukadavu", "Saravanampatti", "Kovilpalayam"],
    "Tiruppur District": ["Tiruppur New Bus Stand", "Dharapuram", "Kangeyam", "Udumalpet", "Avinashi", "Palladam", "Madathukulam", "Uthukuli"],
    "Salem District": ["Salem New Bus Stand", "Attur", "Mettur Dam", "Edappadi", "Omalur", "Sankagiri", "Vazhapadi", "Yercaud"],
    "Namakkal District": ["Namakkal", "Tiruchengode", "Rasipuram", "Paramathi Velur", "Komarapalayam", "Kolli Hills"],
    "Dharmapuri District": ["Dharmapuri", "Harur", "Palacode", "Pennagaram (Hogenakkal)", "Pappireddipatti"],
    "Krishnagiri District": ["Krishnagiri", "Hosur Central Stand", "Pochampalli", "Uthangarai", "Denkanikottai"],
    "Nilgiris District": ["Nilgiris (Udhagamandalam / Ooty)", "Coonoor", "Kotagiri", "Gudalur"],

    # Chennai & Northern Region
    "Chennai Region": ["Chennai (KCBT Kilambakkam)", "Chennai (CMBT Koyambedu)", "Chennai (Madhavaram MMBT)", "Chennai Central / Broadway", "Tambaram"],
    "Chengalpattu District": ["Chengalpattu", "Mahabalipuram (Mamallapuram)", "Maduranthakam", "Maraimalai Nagar"],
    "Kanchipuram District": ["Kanchipuram", "Sriperumbudur", "Walajabad"],
    "Tiruvallur District": ["Tiruvallur", "Avadi", "Poonamallee", "Tirutani"],
    "Vellore District": ["Vellore New Bus Stand", "Katpadi", "Gudiyatham"],
    "Ranipet District": ["Ranipet", "Arakkonam", "Arcot"],
    "Tirupathur District": ["Tirupathur", "Vaniyambadi", "Ambur", "Jolarpettai"],
    "Tiruvannamalai District": ["Tiruvannamalai", "Arani", "Cheyyar", "Polur"],
    "Viluppuram District": ["Viluppuram", "Tindivanam", "Gingee"],
    "Cuddalore District": ["Cuddalore", "Chidambaram", "Panruti", "Vridhachalam", "Neyveli"],
    "Kallakurichi District": ["Kallakurichi", "Ulundurpet", "Sankarapuram"],

    # Central & Delta Region
    "Tiruchirappalli District": ["Tiruchirappalli (Trichy Central)", "Chatram Bus Stand", "Srirangam", "Manapparai", "Thuraiyur"],
    "Thanjavur District": ["Thanjavur New Bus Stand", "Kumbakonam", "Pattukkottai", "Papanasam"],
    "Karur District": ["Karur", "Kulithalai", "Aravakurichi"],
    "Perambalur District": ["Perambalur", "Veppanthattai"],
    "Ariyalur District": ["Ariyalur", "Jayankondam"],
    "Nagapattinam District": ["Nagapattinam", "Velankanni", "Vedaranyam"],
    "Mayiladuthurai District": ["Mayiladuthurai", "Sirkazhi", "Tharangambadi"],
    "Tiruvarur District": ["Tiruvarur", "Mannargudi", "Thiruthuraipoondi"],
    "Pudukkottai District": ["Pudukkottai", "Aranthangi", "Viralimalai"],

    # Southern Region
    "Madurai District": ["Madurai (Mattuthavani - MGR Stand)", "Madurai (Arapalayam)", "Madurai (Periyar Stand)", "Melur", "Thirumangalam"],
    "Dindigul District": ["Dindigul", "Palani", "Kodaikanal", "Oddanchatram", "Batlagundu"],
    "Theni District": ["Theni", "Periyakulam", "Bodinayakanur", "Cumbum"],
    "Virudhunagar District": ["Virudhunagar", "Sivakasi", "Rajapalayam", "Srivilliputhur", "Aruppukkottai"],
    "Ramanathapuram District": ["Ramanathapuram", "Rameswaram", "Paramakudi"],
    "Sivaganga District": ["Sivaganga", "Karaikudi", "Devakottai"],
    "Tirunelveli District": ["Tirunelveli New Bus Stand", "Palayamkottai", "Ambasamudram", "Valliyur"],
    "Tenkasi District": ["Tenkasi", "Sankarankovil", "Courtallam", "Shenkottai"],
    "Thoothukudi District": ["Thoothukudi Old/New Stand", "Kovilpatti", "Tiruchendur"],
    "Kanniyakumari District": ["Nagercoil (Vadasery)", "Kanniyakumari", "Marthandam", "Thuckalay"],

    # Interstate Terminals
    "Interstate Terminals": [
        "Bengaluru (Shantinagar / Majestic - Karnataka)",
        "Mysuru (Suburban Bus Stand - Karnataka)",
        "Chamarajanagar (Karnataka)",
        "Tirupati (APSRTC / TNSTC Stand - Andhra Pradesh)",
        "Puducherry (Pondicherry Central Stand)",
        "Palakkad (Kerala)",
        "Ernakulam / Kochi (Kerala)",
        "Thiruvananthapuram (Tampanoor - Kerala)"
    ]
}

ALL_LOCATIONS = sorted(list(set(place for places in LOCATION_REGISTRY.values() for place in places)))

# -----------------------------------------------------------------------------
# 2. OFFICIAL GOVERNMENT FARE MATRIX & TVK "VETTRI PAYANAM" SCHEME RULES
# -----------------------------------------------------------------------------
OFFICIAL_FARE_RULES = {
    "Town Ordinary (Vettri Payanam)": {
        "type_label": "Town Ordinary (Vettri Payanam Free for Women)",
        "per_km_paise": 55,
        "base_min_fare": 5,
        "is_stage_based": True,
        "vettri_free_women": True,
        "speed_kmh": 32,
        "toll_applicable": False,
        "badge_color": "#2e7d32",
        "description": "Standard town & city municipal service. 100% Free zero-fare travel for women and transgender persons under TVK Govt Vettri Payanam Thittam (Valid Aadhaar/Govt ID)."
    },
    "Mofussil Ordinary (Vettri Payanam)": {
        "type_label": "Mofussil Ordinary (Vettri Payanam Free for Women)",
        "per_km_paise": 60,
        "base_min_fare": 7,
        "is_stage_based": False,
        "vettri_free_women": True,
        "speed_kmh": 38,
        "toll_applicable": False,
        "badge_color": "#388e3c",
        "description": "Connecting taluks, rural panchayats, and ordinary ghat routes beyond 40 km. Free zero-fare travel for women under expanded TVK scheme."
    },
    "TNSTC Express": {
        "type_label": "TNSTC Express",
        "per_km_paise": 80,
        "base_min_fare": 15,
        "is_stage_based": False,
        "vettri_free_women": False,
        "speed_kmh": 50,
        "toll_applicable": True,
        "badge_color": "#0288d1",
        "description": "State highway and National highway fast passenger service with limited intermediate halts."
    },
    "Point-to-Point Superfast": {
        "type_label": "Point-to-Point Superfast (1-to-1)",
        "per_km_paise": 85,
        "base_min_fare": 20,
        "is_stage_based": False,
        "vettri_free_women": False,
        "speed_kmh": 55,
        "toll_applicable": True,
        "badge_color": "#0097a7",
        "description": "Direct non-stop service between major divisional bus stands."
    },
    "TNSTC Super Deluxe": {
        "type_label": "TNSTC Super Deluxe (2x2 Reclining)",
        "per_km_paise": 90,
        "base_min_fare": 30,
        "is_stage_based": False,
        "vettri_free_women": False,
        "speed_kmh": 55,
        "toll_applicable": True,
        "badge_color": "#f57c00",
        "description": "2x2 pushback cushioned seating with air suspension."
    },
    "SETC Ultra Deluxe": {
        "type_label": "SETC Ultra Deluxe Classic",
        "per_km_paise": 110,
        "base_min_fare": 50,
        "is_stage_based": False,
        "vettri_free_women": False,
        "speed_kmh": 60,
        "toll_applicable": True,
        "badge_color": "#d32f2f",
        "description": "State Express inter-district long haul with 2x2 luxury pushback seats."
    },
    "SETC Non-AC Sleeper": {
        "type_label": "SETC Non-AC Sleeper (2+1)",
        "per_km_paise": 155,
        "base_min_fare": 120,
        "is_stage_based": False,
        "vettri_free_women": False,
        "speed_kmh": 58,
        "toll_applicable": True,
        "badge_color": "#7b1fa2",
        "description": "Berth sleeper service with lower and upper bunks for night travel."
    },
    "SETC AC Seater": {
        "type_label": "SETC AC Seater / Deluxe",
        "per_km_paise": 160,
        "base_min_fare": 100,
        "is_stage_based": False,
        "vettri_free_women": False,
        "speed_kmh": 62,
        "toll_applicable": True,
        "badge_color": "#303f9f",
        "description": "Air-conditioned 2x2 pushback coach."
    },
    "SETC AC Sleeper": {
        "type_label": "SETC AC Sleeper (2+1)",
        "per_km_paise": 200,
        "base_min_fare": 180,
        "is_stage_based": False,
        "vettri_free_women": False,
        "speed_kmh": 62,
        "toll_applicable": True,
        "badge_color": "#c2185b",
        "description": "Premium multi-axle Air Conditioned berth coach."
    }
}

GHAT_LOCATIONS = {
    "Nilgiris (Udhagamandalam / Ooty)", "Coonoor", "Kotagiri", "Gudalur",
    "Kodaikanal", "Yercaud", "Valparai", "Kolli Hills", "Pennagaram (Hogenakkal)"
}

# -----------------------------------------------------------------------------
# 3. HIGHWAY DISTANCE ENGINE & NODAL GRAPH
# -----------------------------------------------------------------------------
BASE_COORDINATES = {
    "Sathyamangalam": (11.5034, 77.2444),
    "Coimbatore (Gandhipuram)": (11.0168, 76.9558),
    "Coimbatore (Singanallur)": (11.0003, 77.0264),
    "Coimbatore (Ukkadam)": (10.9890, 76.9580),
    "Erode Central Bus Stand": (11.3410, 77.7172),
    "Tiruppur New Bus Stand": (11.1085, 77.3411),
    "Salem New Bus Stand": (11.6643, 78.1460),
    "Madurai (Mattuthavani - MGR Stand)": (9.9252, 78.1198),
    "Madurai (Arapalayam)": (9.9328, 78.1065),
    "Tiruchirappalli (Trichy Central)": (10.7905, 78.7047),
    "Tirunelveli New Bus Stand": (8.7139, 77.7567),
    "Chennai (KCBT Kilambakkam)": (12.8687, 80.0768),
    "Chennai (CMBT Koyambedu)": (13.0694, 80.1948),
    "Nagercoil (Vadasery)": (8.1833, 77.4119),
    "Dindigul": (10.3673, 77.9803),
    "Thanjavur New Bus Stand": (10.7870, 79.1378),
    "Dharmapuri": (12.1211, 78.1582),
    "Krishnagiri": (12.5186, 78.2137),
    "Hosur Central Stand": (12.7409, 77.8253),
    "Bengaluru (Shantinagar / Majestic - Karnataka)": (12.9716, 77.5946),
    "Mysuru (Suburban Bus Stand - Karnataka)": (12.3118, 76.6529),
    "Nilgiris (Udhagamandalam / Ooty)": (11.4102, 76.6950),
    "Mettupalayam": (11.2996, 76.9388),
    "Gobichettipalayam": (11.4549, 77.4385),
    "Bhavani": (11.4489, 77.6833),
    "Perundurai": (11.2750, 77.5830),
    "Annur": (11.2330, 77.1330),
    "Pollachi": (10.6580, 77.0090),
    "Kumbakonam": (10.9601, 79.3845),
    "Rameswaram": (9.2876, 79.3129),
    "Puducherry (Pondicherry Central Stand)": (11.9416, 79.8083),
    "Viluppuram": (11.9401, 79.4861),
    "Karur": (10.9601, 78.0766),
    "Vellore New Bus Stand": (12.9165, 79.1325),
    "Kanchipuram": (12.8342, 79.7036),
    "Chidambaram": (11.3992, 79.6935),
    "Tenkasi": (8.9594, 77.3150),
    "Thoothukudi Old/New Stand": (8.7642, 78.1348),
    "Theni": (10.0104, 77.4768),
    "Palani": (10.4503, 77.5197),
    "Kodaikanal": (10.2381, 77.4892)
}

EXACT_CORRIDOR_DISTANCES = {
    ("Sathyamangalam", "Coimbatore (Gandhipuram)"): 68,
    ("Sathyamangalam", "Erode Central Bus Stand"): 65,
    ("Sathyamangalam", "Mysuru (Suburban Bus Stand - Karnataka)"): 155,
    ("Sathyamangalam", "Gobichettipalayam"): 28,
    ("Coimbatore (Gandhipuram)", "Salem New Bus Stand"): 165,
    ("Coimbatore (Gandhipuram)", "Madurai (Mattuthavani - MGR Stand)"): 215,
    ("Coimbatore (Gandhipuram)", "Madurai (Arapalayam)"): 210,
    ("Coimbatore (Gandhipuram)", "Bengaluru (Shantinagar / Majestic - Karnataka)"): 365,
    ("Coimbatore (Gandhipuram)", "Nilgiris (Udhagamandalam / Ooty)"): 86,
    ("Coimbatore (Gandhipuram)", "Tiruppur New Bus Stand"): 55,
    ("Coimbatore (Gandhipuram)", "Trichy Central"): 218,
    ("Chennai (KCBT Kilambakkam)", "Madurai (Mattuthavani - MGR Stand)"): 435,
    ("Chennai (KCBT Kilambakkam)", "Coimbatore (Gandhipuram)"): 495,
    ("Chennai (KCBT Kilambakkam)", "Tiruchirappalli (Trichy Central)"): 315,
    ("Chennai (KCBT Kilambakkam)", "Salem New Bus Stand"): 330,
    ("Chennai (KCBT Kilambakkam)", "Tirunelveli New Bus Stand"): 595,
    ("Chennai (KCBT Kilambakkam)", "Nagercoil (Vadasery)"): 675,
    ("Chennai (KCBT Kilambakkam)", "Thanjavur New Bus Stand"): 335,
    ("Chennai (KCBT Kilambakkam)", "Kumbakonam"): 285,
    ("Chennai (KCBT Kilambakkam)", "Puducherry (Pondicherry Central Stand)"): 135,
    ("Madurai (Mattuthavani - MGR Stand)", "Tirunelveli New Bus Stand"): 160,
    ("Madurai (Mattuthavani - MGR Stand)", "Rameswaram"): 172,
    ("Madurai (Mattuthavani - MGR Stand)", "Tiruchirappalli (Trichy Central)"): 130,
    ("Tiruchirappalli (Trichy Central)", "Thanjavur New Bus Stand"): 56,
    ("Salem New Bus Stand", "Bengaluru (Shantinagar / Majestic - Karnataka)"): 202,
    ("Salem New Bus Stand", "Erode Central Bus Stand"): 68,
    ("Erode Central Bus Stand", "Tiruppur New Bus Stand"): 52,
    ("Erode Central Bus Stand", "Coimbatore (Gandhipuram)"): 100,
    ("Dindigul", "Madurai (Mattuthavani - MGR Stand)"): 65,
    ("Dindigul", "Coimbatore (Gandhipuram)"): 155
}

def calculate_route_distance(src, dst):
    """Calculates official highway route distance in kilometers."""
    if (src, dst) in EXACT_CORRIDOR_DISTANCES:
        return EXACT_CORRIDOR_DISTANCES[(src, dst)]
    if (dst, src) in EXACT_CORRIDOR_DISTANCES:
        return EXACT_CORRIDOR_DISTANCES[(dst, src)]
    
    def get_coords(name):
        for k, v in BASE_COORDINATES.items():
            if k in name or name in k:
                return v
        seed = sum(ord(c) for c in name)
        rng = random.Random(seed)
        return (10.0 + rng.random() * 3.0, 77.0 + rng.random() * 2.5)

    c1 = get_coords(src)
    c2 = get_coords(dst)
    
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    direct_km = 6371 * c
    return max(18, int(direct_km * 1.32))

def compute_official_fare(src, dst, service_type, distance_km, is_female_passenger=False):
    """
    Computes exact fare based on official Tamil Nadu Transport Department rules:
    - Base fare per km (paise/km)
    - 20% surcharge on ghat/hill routes
    - Vettri Payanam Thittam (TVK Govt Scheme) 100% Free concession on Town & Mofussil Ordinary buses
    - Toll charges & Passenger amenity cess for express/superfast buses
    """
    rule = OFFICIAL_FARE_RULES.get(service_type, OFFICIAL_FARE_RULES["TNSTC Express"])
    
    # 1. TVK Govt "Vettri Payanam" Scheme Check
    if rule.get("vettri_free_women", False) and is_female_passenger:
        return {
            "base_fare": 0,
            "ghat_surcharge": 0,
            "toll_fee": 0,
            "reservation_fee": 0,
            "total_fare": 0,
            "is_free_vettri": True,
            "distance_km": distance_km
        }
    
    # 2. Base Fare (Stage vs Distance)
    if rule["is_stage_based"]:
        stages = max(1, math.ceil(distance_km / 3))
        base = min(45, rule["base_min_fare"] + (stages - 1) * 2)
    else:
        base = (distance_km * rule["per_km_paise"]) / 100.0
        base = max(rule["base_min_fare"], round(base))

    # 3. Ghat Road Surcharge (+20% base fare)
    has_ghat = any(h in src or h in dst for h in GHAT_LOCATIONS)
    ghat_surcharge = round(base * 0.20) if has_ghat else 0
    
    # 4. Highway Toll Fee
    toll_fee = 0
    if rule["toll_applicable"] and distance_km > 60:
        toll_gates = int(distance_km // 60)
        toll_fee = min(40, toll_gates * 8)
        
    # 5. Online Reservation / Passenger Amenity Fee
    reservation_fee = 0
    if "SETC" in service_type or "Deluxe" in service_type:
        reservation_fee = 10 if "Ultra" in service_type or "Deluxe" in service_type else 20

    subtotal = base + ghat_surcharge + toll_fee + reservation_fee
    final_fare = int(math.ceil(subtotal / 5.0) * 5)
    
    return {
        "base_fare": int(base),
        "ghat_surcharge": int(ghat_surcharge),
        "toll_fee": int(toll_fee),
        "reservation_fee": int(reservation_fee),
        "total_fare": final_fare,
        "is_free_vettri": False,
        "distance_km": distance_km
    }

# -----------------------------------------------------------------------------
# 4. OFFICIAL TIMETABLE & REALISTIC CORRIDORS
# -----------------------------------------------------------------------------
HIGH_FREQUENCY_OFFICIAL_TIMETABLES = {
    ("Sathyamangalam", "Coimbatore (Gandhipuram)"): [
        {"dep": "04:45 AM", "type": "Town Ordinary (Vettri Payanam)", "rto": "TN-38-N-1102", "depot": "Sathy Depot", "via": ["Sathyamangalam", "Ariyappampalayam", "P. Puliampatti", "Annur", "Kovilpalayam", "Saravanampatti", "Gandhipuram"]},
        {"dep": "05:15 AM", "type": "TNSTC Express", "rto": "TN-38-N-1204", "depot": "Sathy Depot", "via": ["Sathyamangalam", "P. Puliampatti", "Annur", "Saravanampatti", "Gandhipuram"]},
        {"dep": "06:00 AM", "type": "Point-to-Point Superfast", "rto": "TN-38-N-1542", "depot": "Coimbatore Central", "via": ["Sathyamangalam", "P. Puliampatti", "Annur", "Gandhipuram"]},
        {"dep": "06:45 AM", "type": "Town Ordinary (Vettri Payanam)", "rto": "TN-38-N-1890", "depot": "Sathy Depot", "via": ["Sathyamangalam", "Ariyappampalayam", "P. Puliampatti", "Annur", "Kovilpalayam", "Saravanampatti", "Gandhipuram"]},
        {"dep": "07:30 AM", "type": "TNSTC Express", "rto": "TN-38-N-2101", "depot": "Coimbatore Central", "via": ["Sathyamangalam", "P. Puliampatti", "Annur", "Saravanampatti", "Gandhipuram"]},
        {"dep": "08:15 AM", "type": "Point-to-Point Superfast", "rto": "TN-38-N-2250", "depot": "Sathy Depot", "via": ["Sathyamangalam", "P. Puliampatti", "Annur", "Gandhipuram"]},
        {"dep": "09:45 AM", "type": "TNSTC Express", "rto": "TN-38-N-2610", "depot": "Coimbatore Central", "via": ["Sathyamangalam", "P. Puliampatti", "Annur", "Saravanampatti", "Gandhipuram"]},
        {"dep": "11:15 AM", "type": "Town Ordinary (Vettri Payanam)", "rto": "TN-38-N-2780", "depot": "Sathy Depot", "via": ["Sathyamangalam", "Ariyappampalayam", "P. Puliampatti", "Annur", "Kovilpalayam", "Saravanampatti", "Gandhipuram"]},
        {"dep": "01:30 PM", "type": "Point-to-Point Superfast", "rto": "TN-38-N-2900", "depot": "Coimbatore Central", "via": ["Sathyamangalam", "P. Puliampatti", "Annur", "Gandhipuram"]},
        {"dep": "03:15 PM", "type": "TNSTC Express", "rto": "TN-38-N-3120", "depot": "Sathy Depot", "via": ["Sathyamangalam", "P. Puliampatti", "Annur", "Saravanampatti", "Gandhipuram"]},
        {"dep": "05:00 PM", "type": "Town Ordinary (Vettri Payanam)", "rto": "TN-38-N-3345", "depot": "Sathy Depot", "via": ["Sathyamangalam", "Ariyappampalayam", "P. Puliampatti", "Annur", "Saravanampatti", "Gandhipuram"]},
        {"dep": "06:30 PM", "type": "Point-to-Point Superfast", "rto": "TN-38-N-3560", "depot": "Coimbatore Central", "via": ["Sathyamangalam", "P. Puliampatti", "Annur", "Gandhipuram"]},
        {"dep": "08:15 PM", "type": "TNSTC Express", "rto": "TN-38-N-3720", "depot": "Sathy Depot", "via": ["Sathyamangalam", "P. Puliampatti", "Annur", "Gandhipuram"]},
        {"dep": "09:45 PM", "type": "TNSTC Express", "rto": "TN-38-N-3890", "depot": "Coimbatore Central", "via": ["Sathyamangalam", "P. Puliampatti", "Annur", "Gandhipuram"]}
    ],

    ("Chennai (KCBT Kilambakkam)", "Madurai (Mattuthavani - MGR Stand)"): [
        {"dep": "05:30 AM", "type": "SETC Ultra Deluxe", "rto": "TN-01-AN-0820", "depot": "Madurai SETC", "via": ["Kilambakkam", "Tindivanam", "Villupuram Bypass", "Tiruchirappalli Central", "Melur", "Mattuthavani"]},
        {"dep": "07:00 AM", "type": "TNSTC Express", "rto": "TN-58-N-2210", "depot": "Madurai Region", "via": ["Kilambakkam", "Chengalpattu", "Villupuram", "Ulundurpet", "Trichy Bypass", "Melur", "Madurai"]},
        {"dep": "10:30 AM", "type": "SETC AC Seater", "rto": "TN-01-AN-1205", "depot": "Chennai SETC", "via": ["Kilambakkam", "Villupuram Toll", "Perambalur", "Trichy Central", "Madurai"]},
        {"dep": "02:15 PM", "type": "SETC Ultra Deluxe", "rto": "TN-01-AN-1450", "depot": "Madurai SETC", "via": ["Kilambakkam", "Tindivanam", "Trichy Central", "Madurai"]},
        {"dep": "06:00 PM", "type": "TNSTC Express", "rto": "TN-58-N-3012", "depot": "Madurai Region", "via": ["Kilambakkam", "Villupuram", "Trichy", "Melur", "Madurai"]},
        {"dep": "08:30 PM", "type": "SETC AC Sleeper", "rto": "TN-01-AL-0440", "depot": "Chennai SETC", "via": ["Kilambakkam", "Villupuram Toll", "Trichy Bypass", "Madurai"]},
        {"dep": "09:15 PM", "type": "SETC Non-AC Sleeper", "rto": "TN-01-AN-2190", "depot": "Madurai SETC", "via": ["Kilambakkam", "Villupuram", "Trichy Central", "Madurai"]},
        {"dep": "10:00 PM", "type": "SETC AC Sleeper", "rto": "TN-01-AL-0512", "depot": "Madurai SETC", "via": ["Kilambakkam", "Trichy Bypass", "Madurai"]},
        {"dep": "10:45 PM", "type": "SETC Ultra Deluxe", "rto": "TN-01-AN-2340", "depot": "Chennai SETC", "via": ["Kilambakkam", "Villupuram", "Trichy", "Madurai"]}
    ],

    ("Sathyamangalam", "Erode Central Bus Stand"): [
        {"dep": "05:00 AM", "type": "Town Ordinary (Vettri Payanam)", "rto": "TN-33-N-1402", "depot": "Erode 1", "via": ["Sathyamangalam", "Gobichettipalayam", "Kavindapadi", "Bhavani", "Erode Central"]},
        {"dep": "06:15 AM", "type": "TNSTC Express", "rto": "TN-33-N-1820", "depot": "Sathy Depot", "via": ["Sathyamangalam", "Gobichettipalayam", "Kavindapadi", "Bhavani", "Erode Central"]},
        {"dep": "07:30 AM", "type": "Point-to-Point Superfast", "rto": "TN-33-N-2104", "depot": "Erode 2", "via": ["Sathyamangalam", "Gobichettipalayam", "Bhavani", "Erode Central"]},
        {"dep": "09:00 AM", "type": "Town Ordinary (Vettri Payanam)", "rto": "TN-33-N-2350", "depot": "Sathy Depot", "via": ["Sathyamangalam", "Gobichettipalayam", "Kavindapadi", "Bhavani", "Erode Central"]},
        {"dep": "11:30 AM", "type": "TNSTC Express", "rto": "TN-33-N-2790", "depot": "Erode 1", "via": ["Sathyamangalam", "Gobichettipalayam", "Bhavani", "Erode Central"]},
        {"dep": "02:15 PM", "type": "Point-to-Point Superfast", "rto": "TN-33-N-3010", "depot": "Sathy Depot", "via": ["Sathyamangalam", "Gobichettipalayam", "Bhavani", "Erode Central"]},
        {"dep": "04:45 PM", "type": "Town Ordinary (Vettri Payanam)", "rto": "TN-33-N-3420", "depot": "Erode 2", "via": ["Sathyamangalam", "Gobichettipalayam", "Kavindapadi", "Bhavani", "Erode Central"]},
        {"dep": "06:45 PM", "type": "TNSTC Express", "rto": "TN-33-N-3810", "depot": "Sathy Depot", "via": ["Sathyamangalam", "Gobichettipalayam", "Bhavani", "Erode Central"]},
        {"dep": "08:30 PM", "type": "TNSTC Express", "rto": "TN-33-N-4050", "depot": "Erode 1", "via": ["Sathyamangalam", "Gobichettipalayam", "Bhavani", "Erode Central"]}
    ],

    ("Sathyamangalam", "Mysuru (Suburban Bus Stand - Karnataka)"): [
        {"dep": "06:00 AM", "type": "TNSTC Express", "rto": "TN-38-N-1904", "depot": "Sathy Depot", "via": ["Sathyamangalam", "Bannari", "Dhimbam Ghat (27 Bends)", "Hasanur", "Chamarajanagar", "Nanjangud", "Mysuru"]},
        {"dep": "08:30 AM", "type": "TNSTC Express", "rto": "TN-33-N-2210", "depot": "Erode Depot", "via": ["Sathyamangalam", "Bannari", "Dhimbam Ghat", "Hasanur", "Chamarajanagar", "Nanjangud", "Mysuru"]},
        {"dep": "11:00 AM", "type": "TNSTC Super Deluxe", "rto": "TN-38-N-2800", "depot": "Coimbatore", "via": ["Sathyamangalam", "Dhimbam Ghat", "Hasanur", "Chamarajanagar", "Nanjangud", "Mysuru"]},
        {"dep": "01:30 PM", "type": "TNSTC Express", "rto": "TN-38-N-3190", "depot": "Sathy Depot", "via": ["Sathyamangalam", "Bannari", "Dhimbam Ghat", "Hasanur", "Chamarajanagar", "Nanjangud", "Mysuru"]},
        {"dep": "04:00 PM", "type": "TNSTC Express", "rto": "TN-33-N-3600", "depot": "Erode Depot", "via": ["Sathyamangalam", "Bannari", "Dhimbam Ghat", "Hasanur", "Chamarajanagar", "Nanjangud", "Mysuru"]}
    ]
}

def parse_time_str(t_str):
    try:
        t = datetime.strptime(t_str.strip(), "%I:%M %p")
        return t.hour * 60 + t.minute
    except Exception:
        return 0

def format_minutes_to_time(total_min):
    total_min = int(total_min) % (24 * 60)
    hr = total_min // 60
    mn = total_min % 60
    ampm = "AM" if hr < 12 else "PM"
    display_hr = hr if (1 <= hr <= 12) else (hr - 12 if hr > 12 else 12)
    return f"{display_hr:02d}:{mn:02d} {ampm}"

def generate_procedural_schedule(src, dst):
    dist_km = calculate_route_distance(src, dst)
    seed_val = sum(ord(c) for c in (src + dst))
    rng = random.Random(seed_val)
    is_ghat = any(h in src or h in dst for h in GHAT_LOCATIONS)

    if dist_km <= 50:
        eligible_types = ["Town Ordinary (Vettri Payanam)", "Mofussil Ordinary (Vettri Payanam)", "TNSTC Express", "Point-to-Point Superfast"]
    elif dist_km <= 150:
        eligible_types = ["TNSTC Express", "Point-to-Point Superfast", "Town Ordinary (Vettri Payanam)", "Mofussil Ordinary (Vettri Payanam)", "TNSTC Super Deluxe"]
    elif dist_km <= 300:
        eligible_types = ["TNSTC Express", "Point-to-Point Superfast", "TNSTC Super Deluxe", "SETC Ultra Deluxe", "SETC Non-AC Sleeper"]
    else:
        eligible_types = ["SETC Ultra Deluxe", "SETC AC Seater", "SETC Non-AC Sleeper", "SETC AC Sleeper", "TNSTC Express"]

    num_buses = min(12, max(5, int(180 / max(20, dist_km)) + rng.randint(4, 7)))
    base_hours = [4, 5, 6, 7, 8, 9, 11, 13, 15, 17, 18, 19, 20, 21, 22]
    sampled_hours = sorted(rng.sample(base_hours, min(num_buses, len(base_hours))))

    schedule = []
    candidate_junctions = [
        "Avinashi Bypass", "Perundurai Toll", "Bhavani Junction", "Salem New Stand", 
        "Dindigul Bypass", "Trichy Central Toll", "Villupuram Plaza", "Tindivanam Bypass",
        "Ulundurpet Junction", "Dharmapuri Toll", "Krishnagiri Plaza", "Hosur Ring Road",
        "Madurai Ring Road", "Kovilpatti Bypass", "Karur Bypass", "Melur Toll"
    ]
    route_intermediates = rng.sample(candidate_junctions, k=min(3, max(1, dist_km // 90)))
    stops_chain = [src] + route_intermediates + [dst]
    division_names = list(TN_DIVISIONS.keys())

    for idx, hr in enumerate(sampled_hours):
        minute = rng.choice([0, 15, 30, 45])
        t_dep_min = hr * 60 + minute
        t_dep_str = format_minutes_to_time(t_dep_min)

        chosen_type = eligible_types[idx % len(eligible_types)]
        speed = OFFICIAL_FARE_RULES[chosen_type]["speed_kmh"]
        if is_ghat:
            speed = int(speed * 0.75)

        duration_hours = dist_km / max(25, speed)
        duration_min = int(duration_hours * 60)
        t_arr_min = t_dep_min + duration_min
        t_arr_str = format_minutes_to_time(t_arr_min)

        fare_info = compute_official_fare(src, dst, chosen_type, dist_km, is_female_passenger=False)

        div_choice = TN_DIVISIONS[division_names[rng.randint(0, len(division_names) - 1)]]
        rto_prefix = div_choice["rto_codes"][rng.randint(0, len(div_choice["rto_codes"]) - 1)]
        rto_number = f"{rto_prefix}-N-{rng.randint(1000, 9999)}"
        depot = div_choice["depots"][rng.randint(0, len(div_choice["depots"]) - 1)]

        max_seats = 30 if "Sleeper" in chosen_type else (44 if "Deluxe" in chosen_type else 52)
        seats_left = rng.randint(4, max_seats - 2)

        schedule.append({
            "bus_no": rto_number,
            "type": chosen_type,
            "dep": t_dep_str,
            "arr": t_arr_str,
            "dep_minutes": t_dep_min,
            "duration_str": f"{duration_min // 60}h {duration_min % 60}m",
            "fare": fare_info["total_fare"],
            "fare_breakdown": fare_info,
            "seats": seats_left,
            "max_seats": max_seats,
            "depot": depot,
            "via": stops_chain,
            "distance_km": dist_km
        })

    return schedule

def get_complete_schedule(src, dst):
    dist_km = calculate_route_distance(src, dst)
    if (src, dst) in HIGH_FREQUENCY_OFFICIAL_TIMETABLES:
        raw_list = HIGH_FREQUENCY_OFFICIAL_TIMETABLES[(src, dst)]
        processed = []
        for item in raw_list:
            chosen_type = item["type"]
            speed = OFFICIAL_FARE_RULES.get(chosen_type, OFFICIAL_FARE_RULES["TNSTC Express"])["speed_kmh"]
            duration_min = int((dist_km / speed) * 60)
            dep_min = parse_time_str(item["dep"])
            arr_min = dep_min + duration_min
            fare_info = compute_official_fare(src, dst, chosen_type, dist_km, is_female_passenger=False)
            
            processed.append({
                "bus_no": item["rto"],
                "type": chosen_type,
                "dep": item["dep"],
                "arr": format_minutes_to_time(arr_min),
                "dep_minutes": dep_min,
                "duration_str": f"{duration_min // 60}h {duration_min % 60}m",
                "fare": fare_info["total_fare"],
                "fare_breakdown": fare_info,
                "seats": random.randint(8, 36),
                "max_seats": 50 if "Town" in chosen_type or "Express" in chosen_type else 36,
                "depot": item["depot"],
                "via": item["via"],
                "distance_km": dist_km
            })
        return processed
    else:
        return generate_procedural_schedule(src, dst)

# -----------------------------------------------------------------------------
# 5. STREAMLIT APP STATE MANAGEMENT
# -----------------------------------------------------------------------------
if "booked_tickets" not in st.session_state:
    st.session_state.booked_tickets = []
if "custom_ai_buses" not in st.session_state:
    st.session_state.custom_ai_buses = []
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

MASTER_ADMIN_PASSWORD = os.environ.get("TN_ADMIN_PASSWORD", "")

# -----------------------------------------------------------------------------
# 6. SMART BUS MANAGEMENT DATABASE (SESSION-BASED DEMO)
# -----------------------------------------------------------------------------
DEFAULT_BUSES = [
    {
        "bus_id": "BUS101", "registration_no": "TN-38-N-101", "route_no": "R12",
        "driver": "Arun Kumar", "capacity": 50, "available_seats": 8,
        "status": "Running", "source": "Erode Central Bus Stand",
        "destination": "Coimbatore (Gandhipuram)", "depot": "Erode Central",
        "service_type": "TNSTC Express", "departure": "06:30 AM", "arrival": "08:45 AM"
    },
    {
        "bus_id": "BUS102", "registration_no": "TN-38-N-102", "route_no": "R13",
        "driver": "Suresh Kumar", "capacity": 52, "available_seats": 24,
        "status": "Running", "source": "Coimbatore (Gandhipuram)",
        "destination": "Salem New Bus Stand", "depot": "Coimbatore Central",
        "service_type": "Point-to-Point Superfast", "departure": "09:00 AM", "arrival": "12:15 PM"
    },
    {
        "bus_id": "BUS103", "registration_no": "TN-01-N-103", "route_no": "R20",
        "driver": "Ravi Shankar", "capacity": 50, "available_seats": 35,
        "status": "Maintenance", "source": "Chennai (KCBT Kilambakkam)",
        "destination": "Salem New Bus Stand", "depot": "Chennai SETC",
        "service_type": "SETC Ultra Deluxe", "departure": "07:00 PM", "arrival": "11:30 PM"
    }
]

DEFAULT_ROUTES = [
    {"route_no": "R12", "route_name": "Erode - Coimbatore", "source": "Erode Central Bus Stand", "destination": "Coimbatore (Gandhipuram)", "stops": ["Erode Central Bus Stand", "Bhavani", "Perundurai", "Tiruppur New Bus Stand", "Coimbatore (Gandhipuram)"]},
    {"route_no": "R13", "route_name": "Coimbatore - Salem", "source": "Coimbatore (Gandhipuram)", "destination": "Salem New Bus Stand", "stops": ["Coimbatore (Gandhipuram)", "Avinashi", "Tiruppur New Bus Stand", "Erode Central Bus Stand", "Salem New Bus Stand"]},
    {"route_no": "R20", "route_name": "Chennai - Salem", "source": "Chennai (KCBT Kilambakkam)", "destination": "Salem New Bus Stand", "stops": ["Chennai (KCBT Kilambakkam)", "Chengalpattu", "Villupuram", "Trichy Central", "Salem New Bus Stand"]}
]

if "smart_buses" not in st.session_state:
    st.session_state.smart_buses = [dict(x) for x in DEFAULT_BUSES]
if "smart_routes" not in st.session_state:
    st.session_state.smart_routes = [dict(x) for x in DEFAULT_ROUTES]
if "bus_management_message" not in st.session_state:
    st.session_state.bus_management_message = ""


def get_route_by_number(route_no):
    return next((r for r in st.session_state.smart_routes if r["route_no"] == route_no), None)


def get_bus_by_id(bus_id):
    return next((b for b in st.session_state.smart_buses if b["bus_id"] == bus_id), None)


def managed_bus_to_schedule(bus):
    route = get_route_by_number(bus["route_no"])
    stops = route["stops"] if route else [bus["source"], bus["destination"]]
    return {
        "bus_no": bus["registration_no"],
        "bus_id": bus["bus_id"],
        "route_no": bus["route_no"],
        "type": bus["service_type"],
        "dep": bus["departure"],
        "arr": bus["arrival"],
        "dep_minutes": parse_time_str(bus["departure"]),
        "duration_str": "Managed Service",
        "fare": compute_official_fare(bus["source"], bus["destination"], bus["service_type"], max(1, calculate_route_distance(bus["source"], bus["destination"])), False)["total_fare"],
        "fare_breakdown": {},
        "seats": bus["available_seats"],
        "max_seats": bus["capacity"],
        "depot": bus["depot"],
        "via": stops,
        "distance_km": max(1, calculate_route_distance(bus["source"], bus["destination"])),
        "from": bus["source"],
        "to": bus["destination"],
        "status": bus["status"],
        "driver": bus["driver"]
    }

# -----------------------------------------------------------------------------
# 7. MODERN STREAMLIT UI CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SMART BUS - Bus Route & Passenger Management System",
    page_icon="🚍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Official TN Government Aesthetic)
render_html("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #0b1e36 0%, #1a365d 50%, #0d233a 100%);
        padding: 24px;
        border-radius: 14px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(255, 215, 0, 0.2);
    }
    
    .gold-badge {
        background: linear-gradient(90deg, #d4af37, #f39c12);
        color: #0b1e36;
        font-weight: 700;
        font-size: 11px;
        padding: 3px 8px;
        border-radius: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: inline-block;
    }
    
    .bus-card {
        background: #111d2d;
        border: 1px solid #1e334d;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .bus-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 14px rgba(0, 122, 255, 0.12);
    }

    .seat-box {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 38px;
        height: 38px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        margin: 3px;
        cursor: pointer;
    }
    .seat-avail { background-color: #1e293b; color: #94a3b8; border: 1px solid #334155; }
    .seat-ladies { background-color: #831843; color: #fbcfe8; border: 1px solid #be185d; }
    .seat-booked { background-color: #374151; color: #6b7280; text-decoration: line-through; cursor: not-allowed; }
    .seat-selected { background-color: #059669; color: #ffffff; border: 1px solid #10b981; }

    .route-node {
        font-size: 12px;
        padding: 2px 8px;
        border-radius: 12px;
        background: #1e293b;
        color: #38bdf8;
        border: 1px solid #0284c7;
        margin: 2px;
        display: inline-block;
    }

    /* Separate Arasu Bus dashboard - modern grey theme */
    .arasu-dashboard {
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, #111827 0%, #1f2937 50%, #374151 100%);
        border: 1px solid rgba(156, 163, 175, 0.55);
        border-radius: 16px;
        padding: 20px;
        margin: 0 0 20px 0;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.32);
    }
    .arasu-dashboard-inner {
        background: rgba(255,255,255,0.055);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 12px;
        padding: 18px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
        flex-wrap: wrap;
        backdrop-filter: blur(8px);
    }
    .arasu-dashboard-title {
        color: #f9fafb;
        font-size: 20px;
        font-weight: 800;
        margin: 0 0 6px 0;
    }
    .arasu-dashboard-text {
        color: #d1d5db;
        font-size: 13px;
        margin: 0;
        line-height: 1.6;
    }
    .arasu-dashboard-badge {
        display: inline-block;
        background: #4b5563;
        color: #f9fafb;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.7px;
        text-transform: uppercase;
        padding: 5px 9px;
        border-radius: 999px;
        margin-bottom: 8px;
        border: 1px solid #6b7280;
    }
    .arasu-dashboard-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 230px;
        padding: 12px 18px;
        border-radius: 9px;
        background: linear-gradient(135deg, #6b7280, #374151);
        color: #ffffff !important;
        text-decoration: none !important;
        font-size: 13px;
        font-weight: 800;
        border: 1px solid #9ca3af;
        box-shadow: 0 5px 14px rgba(0,0,0,0.25);
        transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
    }
    .arasu-dashboard-button:hover {
        transform: translateY(-2px);
        background: linear-gradient(135deg, #9ca3af, #4b5563);
        box-shadow: 0 8px 18px rgba(0,0,0,0.32);
        color: #ffffff !important;
    }
</style>
""")

# Main Banner Header with Current Date Context
render_html(f"""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div>
            <span class="gold-badge">INDEPENDENT DEMO • SAMPLE DATA • UPDATED: {date.today().strftime('%d-%b-%Y').upper()}</span>
            <h1 style="color: #ffffff; margin: 8px 0 4px 0; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;">
                🚍 தமிழ்நாடு அரசுப் போக்குவரத்துக் கழகம் (TNSTC & SETC)
            </h1>
            <p style="color: #cbd5e1; margin: 0; font-size: 14px;">
                Complete bus management, route management, passenger management, fare calculation, status reports and analytics
            </p>
        </div>
        <div style="text-align: right; background: rgba(0,0,0,0.25); padding: 10px 16px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
            <div style="color: #38bdf8; font-size: 12px; font-weight: 600;">24x7 PASSENGER HELPLINE</div>
            <div style="color: #ffffff; font-size: 17px; font-weight: 700;">📞 1800-419-4287 / 149</div>
            <div style="color: #ec4899; font-size: 11px;">Women Helpline: 181</div>
        </div>
    </div>
</div>
""")

# Separate dashboard for the official Arasu Bus home page
render_html("""
<div class="arasu-dashboard">
    <div class="arasu-dashboard-inner">
        <div style="flex: 1 1 520px;">
            <span class="arasu-dashboard-badge">Official external link</span>
            <div class="arasu-dashboard-title">🚌 Arasu Bus — தமிழ்நாடு அரசு பேருந்து இணையதளம்</div>
            <p class="arasu-dashboard-text">
                Access the official Arasu Bus home page for government bus information. This opens in a separate browser tab.
            </p>
        </div>
        <div style="flex: 0 0 auto;">
            <a class="arasu-dashboard-button" href="https://arasubus.tn.gov.in/" target="_blank" rel="noopener noreferrer">
                Open Arasu Bus Home Page ↗
            </a>
        </div>
    </div>
</div>
""")

# Special Operational Advisory Bulletin with TVK Vettri Payanam Notice
st.warning("""
**Prototype notice:** This independent demo is not affiliated with TNSTC, SETC, or the Government of Tamil Nadu. Schedules, fares, seat availability, concessions, and booking confirmations are simulated examples and are not valid for travel.

📢 **Sample service advisory (verify all details with official sources):**
- Route, fare, service, and scheme information displayed below is illustrative only.
- Check current information through official transport channels before travelling.
""")

tab_timing, tab_booking, tab_passengers, tab_fare_matrix, tab_management, tab_admin = st.tabs([
    "🕒 Bus Timings & Schedules",
    "🎫 Book Ticket & Seat Picker",
    "📋 My Boarding Passes",
    "📊 Fare Calculator",
    "🛠️ SMART BUS Management",
    "🤖 Demo Admin & AI"
])

# -----------------------------------------------------------------------------
# TAB 1: BUS TIMINGS & REAL-TIME SCHEDULES
# -----------------------------------------------------------------------------
with tab_timing:
    st.subheader("🔍 Sample Bus Timetable & Route Enquiry")
    st.caption("Timings and fares sourced directly according to the Tamil Nadu Department of Bus Transport standards.")

    sc1, sc_swap, sc2 = st.columns([10, 1, 10])
    
    with sc1:
        default_org_idx = ALL_LOCATIONS.index("Sathyamangalam") if "Sathyamangalam" in ALL_LOCATIONS else 0
        src_station = st.selectbox("From (Origin Station):", ALL_LOCATIONS, index=default_org_idx, key="search_src")
    
    with sc_swap:
        st.write("")
        st.write("")
        st.button("⇄", help="Swap Stations")
    
    with sc2:
        dest_pool = [x for x in ALL_LOCATIONS if x != src_station]
        default_dst_idx = dest_pool.index("Coimbatore (Gandhipuram)") if "Coimbatore (Gandhipuram)" in dest_pool else 0
        dst_station = st.selectbox("To (Destination Station):", dest_pool, index=default_dst_idx, key="search_dst")

    schedule_data = get_complete_schedule(src_station, dst_station)
    ai_buses = [
        b for b in st.session_state.custom_ai_buses 
        if b.get("from") == src_station and b.get("to") == dst_station
    ]
    all_buses = schedule_data + ai_buses

    dist_val = calculate_route_distance(src_station, dst_station)
    is_ghat = any(h in src_station or h in dst_station for h in GHAT_LOCATIONS)

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.metric("Highway Distance", f"{dist_val} km", delta="Ghat Section" if is_ghat else "State Corridor")
    with kpi2:
        st.metric("Daily Services", f"{len(all_buses)} Buses", delta="Regular Frequency")
    with kpi3:
        first_bus = all_buses[0]["dep"] if all_buses else "N/A"
        st.metric("First Bus Departs", first_bus)
    with kpi4:
        last_bus = all_buses[-1]["dep"] if all_buses else "N/A"
        st.metric("Last Night Service", last_bus)
    with kpi5:
        min_fare = min((b["fare"] for b in all_buses), default=0)
        has_vettri = any("Vettri" in b["type"] for b in all_buses)
        st.metric("Fares From", f"₹{min_fare}", delta="₹0 for Women (TVK)" if has_vettri else "Standard G.O.")

    st.markdown("---")

    fc1, fc2, fc3 = st.columns([4, 4, 4])
    with fc1:
        time_slot = st.selectbox(
            "Departure Time Slot:",
            ["All Timings", "🌅 Early Morning (04:00 - 08:00 AM)", "☀️ Day Service (08:00 AM - 04:00 PM)", "🌆 Evening Peak (04:00 - 08:00 PM)", "🌙 Night Express (08:00 PM - 04:00 AM)"]
        )
    with fc2:
        types_available = ["All Bus Categories"] + sorted(list(set(b["type"] for b in all_buses)))
        type_filter = st.selectbox("Filter Service Type:", types_available)
    with fc3:
        sort_by = st.selectbox("Sort Schedules By:", ["Earliest Departure", "Lowest Fare", "Fastest Journey", "Available Seats"])

    filtered_buses = []
    for b in all_buses:
        dep_min = b["dep_minutes"]
        slot_match = True
        if time_slot.startswith("🌅 Early"):
            slot_match = (4 * 60 <= dep_min < 8 * 60)
        elif time_slot.startswith("☀️ Day"):
            slot_match = (8 * 60 <= dep_min < 16 * 60)
        elif time_slot.startswith("🌆 Evening"):
            slot_match = (16 * 60 <= dep_min < 20 * 60)
        elif time_slot.startswith("🌙 Night"):
            slot_match = (dep_min >= 20 * 60 or dep_min < 4 * 60)
            
        type_match = (type_filter == "All Bus Categories" or b["type"] == type_filter)
        if slot_match and type_match:
            filtered_buses.append(b)

    if sort_by == "Earliest Departure":
        filtered_buses.sort(key=lambda x: x["dep_minutes"])
    elif sort_by == "Lowest Fare":
        filtered_buses.sort(key=lambda x: x["fare"])
    elif sort_by == "Fastest Journey":
        filtered_buses.sort(key=lambda x: x.get("duration_str", "99"))
    elif sort_by == "Available Seats":
        filtered_buses.sort(key=lambda x: x["seats"], reverse=True)

    st.write(f"Showing **{len(filtered_buses)}** government operated services for **{src_station} ➔ {dst_station}**:")

    if not filtered_buses:
        st.warning("No bus services match your selected filter criteria. Try choosing 'All Timings' or another category.")
    else:
        for bus in filtered_buses:
            rule_info = OFFICIAL_FARE_RULES.get(bus["type"], {})
            badge_color = rule_info.get("badge_color", "#0288d1")
            is_vettri = rule_info.get("vettri_free_women", False)

            with st.container():
                route_nodes_html = ' '.join([f'<span class="route-node">{stop}</span>' for stop in bus['via']])
                vettri_badge = '<span style="background-color: #10b981; color: white; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; margin-left: 6px;">👩 வெற்றிப் பயணம் (₹0 for Women - TVK Govt)</span>' if is_vettri else ''
                seats_color = '#4ade80' if bus['seats'] > 12 else '#f87171'

                card_markup = f"""
                <div class="bus-card" style="border-left: 6px solid {badge_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                        <div>
                            <span style="background-color: {badge_color}; color: white; padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: 700;">
                                {bus['type']}
                            </span>
                            {vettri_badge}
                        </div>
                        <div style="font-size: 13px; color: #94a3b8;">
                            <b>Depot:</b> <span style="color: #f1f5f9;">{bus['depot']}</span> | 
                            <b>Bus RTO:</b> <code style="color: #38bdf8; background: #0f172a; padding: 2px 6px; border-radius: 4px;">{bus['bus_no']}</code>
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 15px; margin-top: 14px;">
                        <div>
                            <span style="font-size: 12px; color: #94a3b8;">DEPARTURE</span>
                            <div style="font-size: 18px; font-weight: 800; color: #38bdf8;">⏱️ {bus['dep']}</div>
                            <span style="font-size: 11px; color: #64748b;">{src_station}</span>
                        </div>
                        <div>
                            <span style="font-size: 12px; color: #94a3b8;">EST. ARRIVAL</span>
                            <div style="font-size: 18px; font-weight: 800; color: #f1f5f9;">🏁 {bus['arr']}</div>
                            <span style="font-size: 11px; color: #64748b;">{dst_station}</span>
                        </div>
                        <div>
                            <span style="font-size: 12px; color: #94a3b8;">DURATION</span>
                            <div style="font-size: 16px; font-weight: 700; color: #cbd5e1;">⏳ {bus['duration_str']}</div>
                            <span style="font-size: 11px; color: #64748b;">Distance: {bus['distance_km']} km</span>
                        </div>
                        <div>
                            <span style="font-size: 12px; color: #94a3b8;">ESTIMATED FARE</span>
                            <div style="font-size: 20px; font-weight: 800; color: #10b981;">₹{bus['fare']}</div>
                            <span style="font-size: 11px; color: #64748b;">Per Passenger</span>
                        </div>
                        <div>
                            <span style="font-size: 12px; color: #94a3b8;">SAMPLE SEATS</span>
                            <div style="font-size: 16px; font-weight: 700; color: {seats_color};">
                                💺 {bus['seats']} Left
                            </div>
                            <span style="font-size: 11px; color: #64748b;">of {bus['max_seats']} total</span>
                        </div>
                    </div>

                    <div style="margin-top: 14px; padding-top: 10px; border-top: 1px dashed #334155; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                        <div>
                            <span style="font-size: 12px; font-weight: 600; color: #94a3b8;">Route Stops:</span>
                            {route_nodes_html}
                        </div>
                    </div>
                </div>
                """
                render_html(card_markup)

                with st.expander(f"ℹ️ Estimated Fare Breakdown & Sample Stop Timings for {bus['bus_no']}"):
                    fb_col1, fb_col2 = st.columns(2)
                    with fb_col1:
                        st.markdown("**Estimated fare calculation (demo):**")
                        breakdown = bus.get("fare_breakdown", {})
                        st.write(f"- **Base Fare ({bus['distance_km']} km):** ₹{breakdown.get('base_fare', bus['fare'])}")
                        if breakdown.get("ghat_surcharge", 0) > 0:
                            st.write(f"- **Hill Terrain Surcharge (+20%):** ₹{breakdown['ghat_surcharge']}")
                        if breakdown.get("toll_fee", 0) > 0:
                            st.write(f"- **Highway Toll Plaza User Charge:** ₹{breakdown['toll_fee']}")
                        if breakdown.get("reservation_fee", 0) > 0:
                            st.write(f"- **Passenger Amenity & Online Booking Fee:** ₹{breakdown['reservation_fee']}")
                        st.markdown(f"**Estimated fare: ₹{bus['fare']}**")
                        if is_vettri:
                            st.success("✨ **வெற்றிப் பயணம் திட்டம் Active**: 100% Free zero-fare travel for women passengers upon presenting valid Govt ID / Aadhaar card.")

                    with fb_col2:
                        st.markdown("**Estimated Stage Progression:**")
                        stops = bus["via"]
                        total_stops = len(stops)
                        dep_minutes = bus["dep_minutes"]
                        tot_duration = int(bus["distance_km"] / rule_info.get("speed_kmh", 45) * 60)
                        
                        timeline_df = []
                        for s_idx, stop_name in enumerate(stops):
                            ratio = s_idx / max(1, total_stops - 1)
                            halt_min = dep_minutes + int(tot_duration * ratio)
                            timeline_df.append({
                                "Stage Sequence": f"Stop #{s_idx + 1}",
                                "Station / Junction": stop_name,
                                "Est. Time": format_minutes_to_time(halt_min)
                            })
                        st.dataframe(pd.DataFrame(timeline_df), hide_index=True, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 2: ONLINE BUS TICKET BOOKING & INTERACTIVE SEAT PICKER
# -----------------------------------------------------------------------------
with tab_booking:
    st.subheader("🎟️ Seat Selection Demo & Sample Boarding Pass")
    st.caption("Try the seat selection flow. Bookings are temporary demo records and do not reserve a real bus seat.")

    st.link_button("Open Official TNSTC Online Booking", "https://www.tnstc.in/OTRSOnline/", type="primary", use_container_width=True)

    b_col1, b_col2, b_col3 = st.columns(3)
    with b_col1:
        bk_src = st.selectbox("Origin Boarding Point:", ALL_LOCATIONS, index=ALL_LOCATIONS.index("Sathyamangalam") if "Sathyamangalam" in ALL_LOCATIONS else 0, key="bk_from_key")
    with b_col2:
        bk_dst_opts = [x for x in ALL_LOCATIONS if x != bk_src]
        bk_dst = st.selectbox("Destination Dropping Point:", bk_dst_opts, index=0, key="bk_to_key")
    with b_col3:
        journey_date = st.date_input("Date of Journey:", min_value=date.today(), max_value=date.today() + timedelta(days=60))

    available_buses = get_complete_schedule(bk_src, bk_dst)
    managed_buses = [
        managed_bus_to_schedule(b) for b in st.session_state.smart_buses
        if b["source"] == bk_src and b["destination"] == bk_dst and b["status"] != "Maintenance"
    ]
    ai_added_bk = [b for b in st.session_state.custom_ai_buses if b.get("from") == bk_src and b.get("to") == bk_dst]
    all_booking_buses = managed_buses + available_buses + ai_added_bk

    if not all_booking_buses:
        st.error("No bus schedules found for this corridor.")
    else:
        bus_select_map = {
            f"⏱️ {b['dep']} | {b['type']} | Fare: ₹{b['fare']} | Bus No: {b['bus_no']} ({b['seats']} seats left)": b
            for b in all_booking_buses
        }
        chosen_bus_key = st.selectbox("Select Scheduled Bus Service:", list(bus_select_map.keys()))
        selected_bus = bus_select_map[chosen_bus_key]

        render_html(f"""
        <div style="background: #1e293b; padding: 14px 18px; border-radius: 8px; margin: 12px 0; border-left: 4px solid #38bdf8;">
            <b>Selected Service:</b> {selected_bus['type']} ({selected_bus['bus_no']}) &bull; <b>Depot:</b> {selected_bus['depot']}<br>
            <b>Route Path:</b> {' ➔ '.join(selected_bus['via'])} &bull; <b>Est. Travel Time:</b> {selected_bus['duration_str']}
        </div>
        """)

        st.markdown("#### 1. Passenger Details & Concession")
        pf1, pf2, pf3, pf4 = st.columns(4)
        with pf1:
            passenger_name = st.text_input("Passenger Full Name:*", placeholder="e.g. Anandhi Kumar")
        with pf2:
            passenger_phone = st.text_input("Mobile Number (+91):*", placeholder="e.g. 9876543210")
        with pf3:
            passenger_gender = st.selectbox("Passenger Gender:", ["Female (பெண்)", "Male (ஆண்)", "Transgender (திருநங்கை)"])
        with pf4:
            passenger_age = st.number_input("Age:", min_value=5, max_value=110, value=28)

        is_female = "Female" in passenger_gender or "Transgender" in passenger_gender
        is_vettri_route = OFFICIAL_FARE_RULES.get(selected_bus["type"], {}).get("vettri_free_women", False)

        if is_female and is_vettri_route:
            st.success("🎉 **வெற்றிப் பயணம் திட்டம் (Vettri Payanam Thittam) Concession Applied!** 100% Free Travel (₹0 Fare) for women passengers under the expanded TVK Government policy. Valid Aadhaar or Govt ID to be produced during travel.")
            effective_fare_per_ticket = 0
        else:
            effective_fare_per_ticket = selected_bus["fare"]

        st.markdown("#### 2. Interactive Seat Selection")
        st.caption("Select your preferred seats from the vehicle diagram below:")

        is_sleeper = "Sleeper" in selected_bus["type"]
        selected_seats = []

        if not is_sleeper:
            render_html("""
            <div style="display: flex; gap: 20px; align-items: center; margin-bottom: 10px; font-size: 12px; color: #94a3b8;">
                <div><span class="seat-box seat-avail" style="width: 22px; height: 22px;"></span> Available</div>
                <div><span class="seat-box seat-ladies" style="width: 22px; height: 22px;"></span> Ladies Reserved</div>
                <div><span class="seat-box seat-booked" style="width: 22px; height: 22px;"></span> Occupied</div>
            </div>
            """)

            rng_seed = int(selected_bus["dep_minutes"]) + len(selected_bus["bus_no"])
            seat_rng = random.Random(rng_seed)
            booked_seat_set = set(seat_rng.sample(range(1, 41), max(0, 40 - selected_bus["seats"])))

            with st.container():
                st.write("🚗 **FRONT OF BUS (Driver Cabin)**")
                seat_selection_options = []
                for row in range(1, 11):
                    row_seats = [f"{(row-1)*4 + 1}W", f"{(row-1)*4 + 2}A", f"{(row-1)*4 + 3}A", f"{(row-1)*4 + 4}W"]
                    for seat_id in row_seats:
                        num_part = int(seat_id[:-1])
                        if num_part not in booked_seat_set:
                            label_tag = " [Ladies]" if num_part in [1, 2, 5, 6, 9, 10] else ""
                            seat_selection_options.append(f"Seat {seat_id}{label_tag}")

                selected_seats = st.multiselect(
                    "Pick Your Seat Numbers:",
                    options=seat_selection_options,
                    default=[seat_selection_options[0]] if seat_selection_options else [],
                    max_selections=6
                )
        else:
            st.write("🛌 **SETC Sleeper Coach Layout**")
            sleeper_options = [f"Lower Berth L{i} (Single)" for i in range(1, 7)] + [f"Lower Berth L{i} (Double)" for i in range(7, 13)] + [f"Upper Berth U{i}" for i in range(1, 13)]
            selected_seats = st.multiselect(
                "Pick Sleeper Berth(s):",
                options=sleeper_options,
                default=[sleeper_options[0]],
                max_selections=4
            )

        num_passengers = max(1, len(selected_seats))
        total_fare_bill = num_passengers * effective_fare_per_ticket

        st.markdown("---")
        st.markdown("#### 3. Fare Summary & Boarding Pass Issuance")
        
        fs1, fs2, fs3 = st.columns(3)
        with fs1:
            st.metric("Total Passengers / Seats", f"{num_passengers} Seat(s)")
        with fs2:
            st.metric("Rate Per Passenger", f"₹{effective_fare_per_ticket}")
        with fs3:
            st.metric("Net Total to Pay", f"₹{total_fare_bill}", delta="₹0 (Vettri Scheme)" if effective_fare_per_ticket == 0 else "G.O. Compliant")

        if st.button("💳 Confirm Booking & Generate Boarding Pass", type="primary"):
            if not passenger_name.strip() or not passenger_phone.strip():
                st.error("Please enter a valid passenger name and 10-digit mobile number.")
            elif not selected_seats:
                st.error("Please select at least one seat from the seat layout above.")
            else:
                pnr_code = f"TNSTC-{date.today().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
                ticket_no = f"TKT-{random.randint(100000, 999999)}"

                new_ticket = {
                    "PNR": pnr_code,
                    "Ticket_No": ticket_no,
                    "Passenger": passenger_name.strip(),
                    "Gender": passenger_gender,
                    "Age": passenger_age,
                    "Phone": passenger_phone.strip(),
                    "From": bk_src,
                    "To": bk_dst,
                    "Date": str(journey_date),
                    "Departure": selected_bus["dep"],
                    "Arrival": selected_bus["arr"],
                    "Bus_No": selected_bus["bus_no"],
                    "Depot": selected_bus["depot"],
                    "Service_Type": selected_bus["type"],
                    "Seats": ", ".join(selected_seats),
                    "Seats_Count": num_passengers,
                    "Total_Paid": total_fare_bill,
                    "Is_Vettri": (effective_fare_per_ticket == 0),
                    "Booked_At": datetime.now().strftime("%d-%b-%Y %I:%M %p"),
                    "Status": "Confirmed"
                }

                st.session_state.booked_tickets.append(new_ticket)
                selected_bus["seats"] = max(0, selected_bus["seats"] - num_passengers)
                st.success(f"Ticket Booked Successfully! PNR: {pnr_code}")
                st.balloons()

# -----------------------------------------------------------------------------
# TAB 3: BOOKED PASSENGER BOARDING PASSES
# -----------------------------------------------------------------------------
with tab_passengers:
    st.subheader("📋 Verified Digital Ticket Ledger & Boarding Pass")
    st.caption("Temporary demo boarding passes stored only in this browser session. They are not valid for travel.")

    if not st.session_state.booked_tickets:
        st.info("No tickets have been booked in this session yet. Go to the 'Book Ticket' tab to reserve your journey!")
    else:
        st.write(f"Total Active Reservations in Session: **{len(st.session_state.booked_tickets)}**")
        
        for idx, tkt in enumerate(reversed(st.session_state.booked_tickets)):
            with st.container():
                tkt_status = tkt.get("Status", "Confirmed")
                fare_display = '₹0 (வெற்றிப் பயணம் - TVK Govt)' if tkt['Is_Vettri'] else f"₹{tkt['Total_Paid']}"
                fare_color = '#10b981' if tkt['Is_Vettri'] else '#38bdf8'
                hash_code = abs(hash(tkt['PNR'])) % 100000000

                pass_html = f"""
                <div style="background: #0f172a; border: 2px solid #334155; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                    <!-- Header -->
                    <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding-bottom: 12px; align-items: center; flex-wrap: wrap;">
                        <div>
                            <div style="font-size: 11px; color: #d4af37; font-weight: 700; letter-spacing: 0.5px;">TAMIL NADU STATE TRANSPORT CORPORATION</div>
                            <div style="font-size: 18px; font-weight: 800; color: #ffffff;">தமிழ்நாடு அரசுப் போக்குவரத்து மின்-பயணச்சீட்டு</div>
                        </div>
                        <div style="text-align: right;">
                            <span style="background: #1e293b; color: #38bdf8; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 13px;">PNR: {tkt['PNR']}</span>
                            <div style="margin-top: 5px; color: {'#10b981' if tkt_status == 'Confirmed' else '#ef4444'}; font-weight: 800; font-size: 12px;">STATUS: {tkt_status.upper()}</div>
                            <div style="font-size: 11px; color: #94a3b8; margin-top: 3px;">Ticket #{tkt['Ticket_No']}</div>
                        </div>
                    </div>

                    <!-- Journey Points -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin: 16px 0;">
                        <div>
                            <span style="font-size: 11px; color: #94a3b8;">ORIGIN / BOARDING</span>
                            <div style="font-size: 16px; font-weight: 700; color: #f8fafc;">{tkt['From']}</div>
                            <div style="color: #38bdf8; font-weight: 600; font-size: 14px;">⏱️ Departs: {tkt['Departure']}</div>
                        </div>
                        <div>
                            <span style="font-size: 11px; color: #94a3b8;">DESTINATION / DROPPING</span>
                            <div style="font-size: 16px; font-weight: 700; color: #f8fafc;">{tkt['To']}</div>
                            <div style="color: #cbd5e1; font-weight: 600; font-size: 14px;">🏁 Est. Arrival: {tkt['Arrival']}</div>
                        </div>
                        <div>
                            <span style="font-size: 11px; color: #94a3b8;">JOURNEY DATE</span>
                            <div style="font-size: 16px; font-weight: 700; color: #f8fafc;">📅 {tkt['Date']}</div>
                            <div style="font-size: 11px; color: #94a3b8;">Reporting Time: 15 min prior</div>
                        </div>
                    </div>

                    <!-- Passenger & Seat Matrix -->
                    <div style="background: #1e293b; padding: 12px 16px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                        <div>
                            <span style="font-size: 11px; color: #94a3b8;">PASSENGER</span>
                            <div style="font-size: 15px; font-weight: 700; color: #ffffff;">{tkt['Passenger']} ({tkt['Gender']}, {tkt['Age']} yrs)</div>
                            <div style="font-size: 12px; color: #94a3b8;">Phone: +91 {tkt['Phone']}</div>
                        </div>
                        <div>
                            <span style="font-size: 11px; color: #94a3b8;">SERVICE DETAILS</span>
                            <div style="font-size: 14px; font-weight: 600; color: #f8fafc;">{tkt['Service_Type']}</div>
                            <div style="font-size: 12px; color: #38bdf8;">Bus: {tkt['Bus_No']} ({tkt['Depot']})</div>
                        </div>
                        <div>
                            <span style="font-size: 11px; color: #94a3b8;">SEAT NUMBERS</span>
                            <div style="font-size: 16px; font-weight: 800; color: #10b981;">💺 {tkt['Seats']}</div>
                            <div style="font-size: 11px; color: #94a3b8;">Total: {tkt['Seats_Count']} Seat(s)</div>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 11px; color: #94a3b8;">TOTAL FARE PAID</span>
                            <div style="font-size: 22px; font-weight: 800; color: {fare_color};">
                                {fare_display}
                            </div>
                            <div style="font-size: 11px; color: #94a3b8;">Govt Tax & Cess Included</div>
                        </div>
                    </div>

                    <!-- Footer Barcode & Emergency Support -->
                    <div style="margin-top: 14px; display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: #64748b; flex-wrap: wrap; gap: 8px;">
                        <div>
                            <b>Security Hash:</b> <code style="color: #94a3b8;">TNSTC-SHA256-{hash_code}</code> &bull; Booked on {tkt['Booked_At']}
                        </div>
                        <div>
                            <b>Helpline:</b> 1800-419-4287 &bull; <b>Women Safety:</b> 181 &bull; <b>Police:</b> 100
                        </div>
                    </div>
                </div>
                """
                render_html(pass_html)
                if tkt_status == "Confirmed":
                    if st.button(f"❌ Cancel Ticket {tkt['Ticket_No']}", key=f"cancel_ticket_{tkt['Ticket_No']}"):
                        tkt["Status"] = "Cancelled"
                        st.warning(f"Ticket {tkt['Ticket_No']} cancelled successfully.")
                        st.rerun()
                else:
                    st.error(f"Ticket status: {tkt_status}")

        st.download_button(
            label="📥 Export Digital Ledger to JSON",
            data=json.dumps(st.session_state.booked_tickets, indent=2),
            file_name=f"tnstc_booking_ledger_{date.today().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

# -----------------------------------------------------------------------------
# TAB 4: ESTIMATED FARE MATRIX & TARIFF CALCULATOR
# -----------------------------------------------------------------------------
with tab_fare_matrix:
    st.subheader("📊 Sample Fare Matrix & Tariff Estimates")
    st.markdown("""
    Under the provisions of the **Tamil Nadu Motor Vehicles Rules** and **Government Order G.O. (Ms) No. 229, Home (Transport) Department**,
    the Government has standardized the per-kilometer tariff slabs, minimum base fares, and hill terrain surcharges across state carriage operations.
    
    *Update (02-Oct-2026 / 03-Oct-2026)*: The Tamil Nadu Government (TVK) officially expanded the free bus travel scheme into the **'வெற்றிப் பயணம் திட்டம்' (Vettri Payanam Thittam)** covering 12,692 buses across Town and Mofussil Ordinary services.
    """)

    st.markdown("#### 1. Sample Fare Slab Table")
    
    tariff_rows = []
    for k, v in OFFICIAL_FARE_RULES.items():
        tariff_rows.append({
            "Service Category": k,
            "Rate per Passenger-KM (Paise)": f"{v['per_km_paise']} p/km",
            "Effective Rate (₹/km)": f"₹{v['per_km_paise']/100:.2f} / km",
            "Minimum Base Fare": f"₹{v['base_min_fare']}",
            "Pricing Type": "Stage-wise (₹5 min)" if v["is_stage_based"] else "Distance Linear",
            "Vettri Payanam Concession (TVK Govt)": "✅ 100% Free for Women" if v.get("vettri_free_women", False) else "❌ Standard Fare",
            "Toll Surcharge Applicable": "Yes" if v["toll_applicable"] else "Exempt",
            "Operating Speed": f"{v['speed_kmh']} km/h"
        })
    st.dataframe(pd.DataFrame(tariff_rows), hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 2. Interactive Distance Tariff Calculator")
    st.caption("Calculate exact government-prescribed fares for any custom journey distance across Tamil Nadu:")

    tc1, tc2 = st.columns(2)
    with tc1:
        calc_dist = st.slider("Enter Journey Distance (in Kilometers):", min_value=5, max_value=800, value=70, step=5)
    with tc2:
        calc_is_hill = st.checkbox("Journey passes through Hill / Mountain Ghat Road (+20% Surcharge)")

    comparison_data = []
    for s_name, s_rule in OFFICIAL_FARE_RULES.items():
        base = s_rule["base_min_fare"] if s_rule["is_stage_based"] else max(s_rule["base_min_fare"], round((calc_dist * s_rule["per_km_paise"])/100.0))
        ghat = round(base * 0.20) if calc_is_hill else 0
        toll = min(40, int(calc_dist // 60) * 8) if (s_rule["toll_applicable"] and calc_dist > 60) else 0
        res = 10 if "Ultra" in s_name or "Deluxe" in s_name else (20 if "Sleeper" in s_name else 0)
        tot = int(math.ceil((base + ghat + toll + res)/5.0)*5)

        comparison_data.append({
            "Bus Service Category": s_name,
            "Base Fare": f"₹{base}",
            "Ghat Surcharge": f"₹{ghat}",
            "Toll & Cess": f"₹{toll + res}",
            "Total Government Fare": f"₹{tot}",
            "Women Passenger Fare (Vettri Scheme)": "₹0 (Free - TVK Scheme)" if s_rule.get("vettri_free_women", False) else f"₹{tot}"
        })
    st.dataframe(pd.DataFrame(comparison_data), hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 3. Administrative Transport Divisions & Regional Headquarters")
    st.write("Browse depots and designated RTO vehicle registration prefixes across Tamil Nadu:")

    d_cols = st.columns(3)
    for idx, (div_title, div_info) in enumerate(TN_DIVISIONS.items()):
        target_col = d_cols[idx % 3]
        with target_col:
            with st.expander(f"🏢 {div_title}", expanded=False):
                st.markdown(f"**Vehicle Registration Series:** `{'`, `'.join(div_info['rto_codes'])}`")
                st.markdown("**Major Operational Depots:**")
                for dp in div_info["depots"]:
                    st.markdown(f"- {dp}")

# -----------------------------------------------------------------------------
# TAB 5: SMART BUS ROUTE & PASSENGER MANAGEMENT SYSTEM
# -----------------------------------------------------------------------------
with tab_management:
    st.subheader("🛠️ SMART BUS - Bus Route & Passenger Management System")
    st.caption("All management functions are implemented in Python using Streamlit session state. Data is a demo and resets when the app session restarts.")

    # Dashboard / special challenge report
    st.markdown("### 📊 Bus Status Dashboard")
    total_buses = len(st.session_state.smart_buses)
    running = sum(1 for b in st.session_state.smart_buses if b["status"] == "Running")
    maintenance = sum(1 for b in st.session_state.smart_buses if b["status"] == "Maintenance")
    total_capacity = sum(int(b["capacity"]) for b in st.session_state.smart_buses)
    total_available = sum(int(b["available_seats"]) for b in st.session_state.smart_buses)
    passengers = max(0, total_capacity - total_available)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Buses", total_buses)
    m2.metric("Running", running)
    m3.metric("Maintenance", maintenance)
    m4.metric("Passengers", passengers)
    m5.metric("Available Seats", total_available)

    st.markdown("#### Special Challenge: Bus Status Report")
    report_bus = get_bus_by_id("BUS101") or (st.session_state.smart_buses[0] if st.session_state.smart_buses else None)
    if report_bus:
        report_route = get_route_by_number(report_bus["route_no"])
        report_cols = st.columns(4)
        report_cols[0].metric("Bus ID", report_bus["bus_id"])
        report_cols[1].metric("Route", report_bus["route_no"])
        report_cols[2].metric("Source", report_bus["source"])
        report_cols[3].metric("Destination", report_bus["destination"])
        report_cols = st.columns(4)
        report_cols[0].metric("Capacity", report_bus["capacity"])
        report_cols[1].metric("Passengers", int(report_bus["capacity"]) - int(report_bus["available_seats"]))
        report_cols[2].metric("Available Seats", report_bus["available_seats"])
        report_cols[3].metric("Status", report_bus["status"])
        st.info(f"Driver: {report_bus['driver']} | Registration: {report_bus['registration_no']} | Stops: {' → '.join(report_route['stops']) if report_route else 'Route not found'}")

    st.markdown("---")
    mg_bus, mg_route, mg_pass, mg_analytics = st.tabs([
        "🚌 Bus Management", "🗺️ Route Management", "🎫 Passenger Management", "📈 Analytics"
    ])

    with mg_bus:
        st.markdown("### 🚌 Bus Management")
        badd, bview, bsearch, bupdate, bdelete = st.tabs(["Add Bus", "View Buses", "Search Bus", "Update Bus", "Delete Bus"])

        with badd:
            with st.form("add_bus_form"):
                c1, c2, c3 = st.columns(3)
                bus_id = c1.text_input("Bus ID*", placeholder="BUS104")
                reg_no = c2.text_input("Registration Number*", placeholder="TN-38-N-104")
                route_no = c3.text_input("Route Number*", placeholder="R14")
                c1, c2, c3 = st.columns(3)
                driver = c1.text_input("Driver Name*", placeholder="Driver name")
                capacity = c2.number_input("Capacity*", min_value=1, max_value=100, value=50)
                available = c3.number_input("Available Seats*", min_value=0, max_value=100, value=50)
                c1, c2, c3 = st.columns(3)
                source = c1.text_input("Source*", placeholder="Erode Central Bus Stand")
                destination = c2.text_input("Destination*", placeholder="Coimbatore (Gandhipuram)")
                status = c3.selectbox("Status", ["Running", "Stopped", "Maintenance", "Completed"])
                c1, c2, c3 = st.columns(3)
                depot = c1.text_input("Depot", value="Central Depot")
                service_type = c2.selectbox("Service Type", ["TNSTC Express", "Point-to-Point Superfast", "Town Ordinary (Vettri Payanam)", "SETC Ultra Deluxe", "SETC AC Sleeper"])
                departure = c3.text_input("Departure", value="08:00 AM")
                arrival = st.text_input("Arrival", value="11:00 AM")
                submitted = st.form_submit_button("➕ Add Bus", type="primary")
                if submitted:
                    if available > capacity:
                        st.error("Available seats cannot be greater than capacity.")
                    elif not all([bus_id.strip(), reg_no.strip(), route_no.strip(), driver.strip(), source.strip(), destination.strip()]):
                        st.error("Please fill all required fields.")
                    elif get_bus_by_id(bus_id.strip()):
                        st.error("Bus ID already exists.")
                    else:
                        st.session_state.smart_buses.append({
                            "bus_id": bus_id.strip(), "registration_no": reg_no.strip(), "route_no": route_no.strip(),
                            "driver": driver.strip(), "capacity": int(capacity), "available_seats": int(available),
                            "status": status, "source": source.strip(), "destination": destination.strip(),
                            "depot": depot.strip(), "service_type": service_type, "departure": departure.strip(), "arrival": arrival.strip()
                        })
                        st.success(f"Bus {bus_id.strip()} added successfully.")

        with bview:
            if st.session_state.smart_buses:
                view_rows = []
                for b in st.session_state.smart_buses:
                    view_rows.append({
                        "Bus ID": b["bus_id"], "Registration": b["registration_no"], "Route": b["route_no"],
                        "Driver": b["driver"], "Capacity": b["capacity"], "Available Seats": b["available_seats"],
                        "Passengers": int(b["capacity"]) - int(b["available_seats"]), "Status": b["status"],
                        "Source": b["source"], "Destination": b["destination"]
                    })
                st.dataframe(pd.DataFrame(view_rows), hide_index=True, use_container_width=True)

        with bsearch:
            query = st.text_input("Search by Bus ID, Registration, Route, Driver, Source or Destination")
            q = query.strip().lower()
            results = [b for b in st.session_state.smart_buses if not q or any(q in str(b[k]).lower() for k in ["bus_id","registration_no","route_no","driver","source","destination"])]
            if results:
                st.dataframe(pd.DataFrame([{
                    "Bus ID": b["bus_id"], "Registration": b["registration_no"], "Route": b["route_no"],
                    "Driver": b["driver"], "Capacity": b["capacity"], "Available": b["available_seats"], "Status": b["status"]
                } for b in results]), hide_index=True, use_container_width=True)
            else:
                st.warning("No bus found.")

        with bupdate:
            if st.session_state.smart_buses:
                selected_id = st.selectbox("Select Bus to Update", [b["bus_id"] for b in st.session_state.smart_buses], key="update_bus_id")
                bus = get_bus_by_id(selected_id)
                if bus:
                    c1, c2, c3 = st.columns(3)
                    new_reg = c1.text_input("Registration Number", value=bus["registration_no"], key="upd_reg")
                    new_route = c2.text_input("Route Number", value=bus["route_no"], key="upd_route")
                    new_driver = c3.text_input("Driver", value=bus["driver"], key="upd_driver")
                    c1, c2, c3 = st.columns(3)
                    new_cap = c1.number_input("Capacity", min_value=1, max_value=100, value=int(bus["capacity"]), key="upd_cap")
                    new_avail = c2.number_input("Available Seats", min_value=0, max_value=100, value=int(bus["available_seats"]), key="upd_avail")
                    new_status = c3.selectbox("Status", ["Running", "Stopped", "Maintenance", "Completed"], index=["Running", "Stopped", "Maintenance", "Completed"].index(bus["status"]) if bus["status"] in ["Running", "Stopped", "Maintenance", "Completed"] else 0, key="upd_status")
                    if st.button("💾 Update Bus", type="primary", key="update_bus_btn"):
                        if new_avail > new_cap:
                            st.error("Available seats cannot exceed capacity.")
                        else:
                            bus.update({"registration_no": new_reg.strip(), "route_no": new_route.strip(), "driver": new_driver.strip(), "capacity": int(new_cap), "available_seats": int(new_avail), "status": new_status})
                            st.success(f"Bus {selected_id} updated successfully.")
                            st.rerun()

        with bdelete:
            if st.session_state.smart_buses:
                delete_id = st.selectbox("Select Bus to Delete", [b["bus_id"] for b in st.session_state.smart_buses], key="delete_bus_id")
                st.warning("Deleting a bus removes it from the current demo session.")
                if st.button("🗑️ Delete Bus", type="primary", key="delete_bus_btn"):
                    st.session_state.smart_buses = [b for b in st.session_state.smart_buses if b["bus_id"] != delete_id]
                    st.success(f"Bus {delete_id} deleted successfully.")
                    st.rerun()

    with mg_route:
        st.markdown("### 🗺️ Route Management")
        radd, rstops, rupdate, rsearch = st.tabs(["Add Route", "Add Stops", "Update Route", "Search Route"])
        with radd:
            with st.form("add_route_form"):
                c1, c2 = st.columns(2)
                rn = c1.text_input("Route Number*", placeholder="R14")
                rname = c2.text_input("Route Name*", placeholder="Erode - Salem")
                c1, c2 = st.columns(2)
                rs = c1.text_input("Source*", placeholder="Erode Central Bus Stand")
                rd = c2.text_input("Destination*", placeholder="Salem New Bus Stand")
                stops_text = st.text_input("Stops (comma separated)", placeholder="Erode, Bhavani, Perundurai, Salem")
                if st.form_submit_button("➕ Add Route", type="primary"):
                    if not rn.strip() or not rname.strip() or not rs.strip() or not rd.strip():
                        st.error("Please fill all required route fields.")
                    elif get_route_by_number(rn.strip()):
                        st.error("Route number already exists.")
                    else:
                        stops = [x.strip() for x in stops_text.split(",") if x.strip()]
                        if rs.strip() not in stops: stops.insert(0, rs.strip())
                        if rd.strip() not in stops: stops.append(rd.strip())
                        st.session_state.smart_routes.append({"route_no": rn.strip(), "route_name": rname.strip(), "source": rs.strip(), "destination": rd.strip(), "stops": stops})
                        st.success(f"Route {rn.strip()} added successfully.")
        with rstops:
            if st.session_state.smart_routes:
                route_choice = st.selectbox("Select Route", [r["route_no"] for r in st.session_state.smart_routes], key="stop_route")
                route = get_route_by_number(route_choice)
                new_stop = st.text_input("New Stop Name", placeholder="New Bus Stop")
                if st.button("➕ Add Stop", key="add_stop_btn"):
                    if new_stop.strip() and new_stop.strip() not in route["stops"]:
                        route["stops"].insert(max(1, len(route["stops"]) - 1), new_stop.strip())
                        st.success(f"Stop added to {route_choice}.")
                        st.rerun()
                    else:
                        st.error("Enter a new stop name.")
                st.write("Current Stops:")
                st.write(" → ".join(route["stops"]))
        with rupdate:
            route_choice = st.selectbox("Select Route to Update", [r["route_no"] for r in st.session_state.smart_routes], key="upd_route_no")
            route = get_route_by_number(route_choice)
            if route:
                new_name = st.text_input("Route Name", value=route["route_name"], key="route_name_upd")
                new_source = st.text_input("Source", value=route["source"], key="route_source_upd")
                new_dest = st.text_input("Destination", value=route["destination"], key="route_dest_upd")
                new_stops = st.text_area("Stops (one per line)", value="\n".join(route["stops"]), key="route_stops_upd")
                if st.button("💾 Update Route", type="primary", key="route_update_btn"):
                    route.update({"route_name": new_name.strip(), "source": new_source.strip(), "destination": new_dest.strip(), "stops": [x.strip() for x in new_stops.splitlines() if x.strip()]})
                    st.success(f"Route {route_choice} updated successfully.")
                    st.rerun()
        with rsearch:
            rq = st.text_input("Search Route Number, Name, Source, Destination or Stop")
            q = rq.strip().lower()
            found_routes = [r for r in st.session_state.smart_routes if not q or q in r["route_no"].lower() or q in r["route_name"].lower() or q in r["source"].lower() or q in r["destination"].lower() or any(q in stop.lower() for stop in r["stops"])]
            for r in found_routes:
                with st.expander(f"🗺️ {r['route_no']} - {r['route_name']}"):
                    st.write(f"**Source:** {r['source']} | **Destination:** {r['destination']}")
                    st.write("**Stops:** " + " → ".join(r["stops"]))
            if not found_routes:
                st.warning("No route found.")

    with mg_pass:
        st.markdown("### 🎫 Passenger Management")
        active_tickets = [t for t in st.session_state.booked_tickets if t.get("Status", "Confirmed") == "Confirmed"]
        st.metric("Active Bookings", len(active_tickets))
        if not st.session_state.booked_tickets:
            st.info("No passenger bookings yet. Use the Book Ticket tab first.")
        else:
            ticket_options = [f"{t['Ticket_No']} | {t['Passenger']} | {t['From']} → {t['To']}" for t in st.session_state.booked_tickets]
            chosen = st.selectbox("Select Passenger / Ticket", ticket_options, key="manage_ticket_select")
            chosen_no = chosen.split(" | ")[0]
            ticket = next(t for t in st.session_state.booked_tickets if t["Ticket_No"] == chosen_no)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Passenger", ticket["Passenger"])
            c2.metric("Seats", ticket["Seats_Count"])
            c3.metric("Fare", f"₹{ticket['Total_Paid']}")
            c4.metric("Status", ticket.get("Status", "Confirmed"))
            st.json(ticket)
            if ticket.get("Status", "Confirmed") == "Confirmed":
                if st.button("❌ Cancel Selected Ticket", type="primary", key="manage_cancel"):
                    ticket["Status"] = "Cancelled"
                    st.success(f"Ticket {ticket['Ticket_No']} cancelled successfully.")
                    st.rerun()

    with mg_analytics:
        st.markdown("### 📈 Passenger Load Analysis")
        if st.session_state.smart_buses:
            analytics_rows = []
            for b in st.session_state.smart_buses:
                cap = int(b["capacity"])
                avail = int(b["available_seats"])
                pax = max(0, cap - avail)
                load = round((pax / cap) * 100, 1) if cap else 0
                analytics_rows.append({"Bus ID": b["bus_id"], "Route": b["route_no"], "Passengers": pax, "Capacity": cap, "Available": avail, "Load %": load, "Status": b["status"]})
            adf = pd.DataFrame(analytics_rows)
            st.dataframe(adf, hide_index=True, use_container_width=True)
            st.bar_chart(adf.set_index("Bus ID")["Load %"])
            busiest = adf.loc[adf["Load %"].idxmax()]
            st.success(f"Highest passenger load: {busiest['Bus ID']} on {busiest['Route']} at {busiest['Load %']}%.")

        st.markdown("### ⏰ Peak-Hour Analysis")
        hour_rows = []
        for t in st.session_state.booked_tickets:
            if t.get("Status", "Confirmed") != "Confirmed":
                continue
            try:
                dt = datetime.strptime(t["Departure"], "%I:%M %p")
                hour_rows.append({"Hour": dt.hour, "Passenger Seats": int(t.get("Seats_Count", 1))})
            except Exception:
                pass
        if hour_rows:
            hdf = pd.DataFrame(hour_rows).groupby("Hour", as_index=False)["Passenger Seats"].sum()
            hdf["Time Slot"] = hdf["Hour"].apply(lambda h: f"{h:02d}:00 - {h:02d}:59")
            st.dataframe(hdf[["Time Slot", "Passenger Seats"]], hide_index=True, use_container_width=True)
            peak = hdf.loc[hdf["Passenger Seats"].idxmax()]
            st.success(f"Peak booked departure hour: {int(peak['Hour']):02d}:00 - {int(peak['Hour']):02d}:59 with {int(peak['Passenger Seats'])} passenger seat(s).")
        else:
            st.info("Book some tickets to activate peak-hour analysis.")

# -----------------------------------------------------------------------------
# TAB 6: GEMINI AI TRANSIT ASSISTANT & ADMIN NEWS SYNC
# -----------------------------------------------------------------------------
with tab_admin:
    st.subheader("🤖 Master AI Control & Tamil Nadu Transport Intelligence")
    st.caption("Powered by Google Gemini to analyze transport press releases, passenger queries, and automate route sync.")

    if not st.session_state.admin_logged_in:
        st.markdown("#### 🔐 Administrator Sign-In")
        pwd_input = st.text_input("Enter Admin Security Credential:", type="password", key="adm_pwd")
        if st.button("Unlock Admin Features"):
            if MASTER_ADMIN_PASSWORD and pwd_input == MASTER_ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.success("Admin demo features unlocked.")
                st.rerun()
            else:
                st.error("Admin access is disabled. Set the TN_ADMIN_PASSWORD environment variable before launching this demo.")
    else:
        st.success("Logged in as Transport Operations Administrator.")
        if st.button("Log Out"):
            st.session_state.admin_logged_in = False
            st.rerun()

        st.markdown("---")
        st.markdown("#### 1. Gemini AI Autonomous News & New Route Synchronizer")
        st.write("Scan recent Tamil Nadu government notifications and transport press circulars to auto-inject newly announced bus routes into the portal.")

        gemini_api_key = st.text_input("Gemini API Key (optional - built-in simulation fallback available):", type="password")

        sync_col1, sync_col2 = st.columns(2)
        with sync_col1:
            sync_source = st.selectbox("Select Route Type to Sync:", [
                "TVK Govt Vettri Payanam Thittam Expansion Routes",
                "New Festival / Weekend Special Services",
                "New Direct Inter-District Express (e.g. KCBT to Southern TN)"
            ])

        if st.button("🚀 Execute AI News Scan & Database Ingestion", type="primary"):
            with st.spinner("Analyzing transport circulars and synthesizing route schedules..."):
                new_services = []
                
                if gemini_api_key.strip():
                    try:
                        from google import genai
                        client = genai.Client(api_key=gemini_api_key.strip())
                        
                        prompt = f"""
                        Act as the official Tamil Nadu State Transport Corporation (TNSTC) route planning system.
                        Generate 2 realistic, newly announced government bus routes in Tamil Nadu based on: '{sync_source}'.
                        Available places to pick from: Sathyamangalam, Coimbatore (Gandhipuram), Chennai (KCBT Kilambakkam), 
                        Madurai (Mattuthavani - MGR Stand), Tiruchirappalli (Trichy Central), Salem New Bus Stand, 
                        Tirunelveli New Bus Stand, Erode Central Bus Stand, Mysuru (Suburban Bus Stand - Karnataka).
                        
                        Output ONLY a JSON array of objects with these exact keys:
                        - 'bus_no': string like 'TN-38-N-4421' or 'TN-01-AN-3120'
                        - 'type': one of 'TNSTC Express', 'Point-to-Point Superfast', 'SETC Ultra Deluxe', 'Town Ordinary (Vettri Payanam)', 'SETC AC Sleeper'
                        - 'from': exact station name from list
                        - 'to': exact station name from list
                        - 'dep': string like '07:30 AM'
                        - 'arr': string like '11:45 AM'
                        - 'dep_minutes': integer minutes from midnight (e.g. 450)
                        - 'duration_str': string like '4h 15m'
                        - 'fare': integer in rupees (computed realistically)
                        - 'seats': integer (e.g. 35)
                        - 'max_seats': integer (40 or 52)
                        - 'depot': string
                        - 'via': list of 3 intermediate towns
                        - 'distance_km': integer km
                        Return raw JSON only, no markdown.
                        """
                        response = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=prompt
                        )
                        clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
                        new_services = json.loads(clean_text)
                    except Exception as ex:
                        st.warning(f"Could not connect to live Gemini API ({ex}). Using official TNSTC offline sync simulation.")
                        new_services = []

                if not new_services:
                    new_services = [
                        {
                            "bus_no": "TN-38-N-4920",
                            "type": "Point-to-Point Superfast",
                            "from": "Sathyamangalam",
                            "to": "Madurai (Mattuthavani - MGR Stand)",
                            "dep": "06:15 AM",
                            "arr": "11:45 AM",
                            "dep_minutes": 375,
                            "duration_str": "5h 30m",
                            "fare": 210,
                            "seats": 38,
                            "max_seats": 48,
                            "depot": "Sathy Depot",
                            "via": ["Sathyamangalam", "Tiruppur", "Dharapuram", "Oddanchatram", "Madurai"],
                            "distance_km": 240
                        },
                        {
                            "bus_no": "TN-01-AN-3890",
                            "type": "SETC AC Sleeper",
                            "from": "Chennai (KCBT Kilambakkam)",
                            "to": "Tirunelveli New Bus Stand",
                            "dep": "09:30 PM",
                            "arr": "08:15 AM",
                            "dep_minutes": 1290,
                            "duration_str": "10h 45m",
                            "fare": 1190,
                            "seats": 24,
                            "max_seats": 30,
                            "depot": "Chennai SETC",
                            "via": ["Kilambakkam", "Villupuram", "Trichy Bypass", "Madurai Ring Road", "Tirunelveli"],
                            "distance_km": 595
                        }
                    ]

                for item in new_services:
                    st.session_state.custom_ai_buses.append(item)

                st.success(f"Successfully processed official bulletin! Added {len(new_services)} new services to the active database.")
                st.json(new_services)

        st.markdown("---")
        st.markdown("#### 2. Tamil Nadu Transit Q&A Assistant")
        st.caption("Ask questions regarding bus timings, concession schemes, luggage policies, or route connections:")

        user_q = st.text_input("Enter passenger enquiry:", placeholder="e.g. What are the rules and guidelines for the TVK Vettri Payanam Thittam free travel scheme?")
        if st.button("Ask Transit AI"):
            if not user_q.strip():
                st.error("Please enter a question.")
            else:
                with st.spinner("Consulting Tamil Nadu Motor Vehicles Act & Department Guidelines..."):
                    if gemini_api_key.strip():
                        try:
                            from google import genai
                            client = genai.Client(api_key=gemini_api_key.strip())
                            resp = client.models.generate_content(
                                model="gemini-3.8-flash",
                                contents=f"You are the official helpdesk for Tamil Nadu State Transport Corporation (TNSTC & SETC). Answer concisely and factually based on Tamil Nadu transport department rules and the TVK Government Vettri Payanam Thittam launched on Oct 2, 2026:\nQuestion: {user_q}"
                            )
                            st.markdown(f"**Official Response:**\n\n{resp.text}")
                        except Exception as ex:
                            st.info(f"Offline Helpdesk Rule: Free luggage allowance in TNSTC ordinary buses is up to 25 kg per passenger. Children below 3 years travel free. Women and transgender persons travel 100% free under Vettri Payanam Thittam across 12,692 Town & Mofussil ordinary buses upon presenting valid Aadhaar card.")
                    else:
                        st.info(f"**TNSTC Transit Desk (Automated Response):**\n- **TVK 'வெற்றிப் பயணம் திட்டம்' (Vettri Payanam Thittam)**: Expanded on Oct 2, 2026. 100% free travel for women and transgender persons across 12,692 buses including Town Ordinary, Mofussil Ordinary, and LSS/Deluxe buses (Aadhaar or Government ID required). SETC luxury coaches remain excluded.\n- **Luggage Allowance**: Standard personal baggage up to 25 kg is free. Commercial cargo or packages above 50 kg attract excess luggage fees.\n- **Concessions**: Senior citizens (above 60 years) are eligible for free tokens per month in town buses upon submitting token passes issued by the Transport Department.") 

