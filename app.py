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


# Required Bus / Route / Passenger Management System data
if "managed_buses" not in st.session_state:
    st.session_state.managed_buses = [
        {"bus_id": "BUS101", "registration": "TN-38-N-4421", "route_no": "R12", "driver": "Arun Kumar", "capacity": 50, "available": 8, "status": "Running"},
        {"bus_id": "BUS102", "registration": "TN-33-N-1845", "route_no": "R18", "driver": "Suresh", "capacity": 52, "available": 21, "status": "Running"},
        {"bus_id": "BUS103", "registration": "TN-38-N-7752", "route_no": "R25", "driver": "Ravi", "capacity": 48, "available": 48, "status": "Available"},
    ]
if "managed_routes" not in st.session_state:
    st.session_state.managed_routes = [
        {"route_no": "R12", "source": "Erode", "destination": "Coimbatore", "stops": ["Erode", "Perundurai", "Tiruppur", "Avinashi", "Coimbatore"]},
        {"route_no": "R18", "source": "Salem", "destination": "Erode", "stops": ["Salem", "Sankagiri", "Bhavani", "Erode"]},
        {"route_no": "R25", "source": "Erode", "destination": "Sathyamangalam", "stops": ["Erode", "Bhavani", "Gobichettipalayam", "Sathyamangalam"]},
    ]

# -----------------------------------------------------------------------------
# 6. MODERN STREAMLIT UI CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SMART BUS - Bus Route and Passenger Management System",
    page_icon="🚌",
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

# Main Banner Header
render_html(f"""
<div class="main-header">
    <div style="display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap;">
        <div style="flex:1;min-width:520px;">
            <span class="gold-badge">SMART TRANSPORT MANAGEMENT SYSTEM • UPDATED: {date.today().strftime('%d-%b-%Y').upper()}</span>
            <h1 style="color:#ffffff;margin:10px 0 5px 0;font-size:34px;font-weight:800;letter-spacing:-0.8px;">
                🚌 SMART BUS
            </h1>
            <div style="color:#ffffff;font-size:21px;font-weight:700;margin-bottom:7px;">
                Bus Route and Passenger Management System
            </div>
            <p style="color:#cbd5e1;margin:0;font-size:14px;">
                Bus Management • Route Management • Passenger Management • Fare Calculation • Status Reports • Analytics
            </p>
        </div>
        <div style="text-align:right;background:rgba(0,0,0,0.25);padding:12px 18px;border-radius:10px;border:1px solid rgba(255,255,255,0.08);">
            <div style="color:#38bdf8;font-size:12px;font-weight:600;">PASSENGER HELPLINE</div>
            <div style="color:#ffffff;font-size:17px;font-weight:700;">📞 1800-419-4287 / 149</div>
            <div style="color:#ec4899;font-size:11px;">Women Helpline: 181</div>
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

tab_timing, tab_bus, tab_route, tab_booking, tab_passengers, tab_fare_matrix, tab_reports = st.tabs([
    "🕒 Bus Timings",
    "🚌 Bus Management",
    "🗺️ Route Management",
    "🎫 Passenger Management",
    "📋 Passenger Details",
    "💰 Fare Calculation",
    "📊 Status & Analytics"
])


# -----------------------------------------------------------------------------
# BUS MANAGEMENT - Add / View / Search / Update / Delete
# -----------------------------------------------------------------------------
with tab_bus:
    st.subheader("🚌 Bus Management")
    st.caption("Manage Bus ID, registration number, route number, driver, capacity, available seats and status.")

    action = st.radio("Select Operation", ["Add Bus", "View Buses", "Search Bus", "Update Bus", "Delete Bus"], horizontal=True, key="bus_action")

    if action == "Add Bus":
        with st.form("add_bus_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            bus_id = c1.text_input("Bus ID", placeholder="BUS104")
            registration = c2.text_input("Registration Number", placeholder="TN-38-N-1234")
            route_no = c3.text_input("Route Number", placeholder="R12")
            c4, c5, c6, c7 = st.columns(4)
            driver = c4.text_input("Driver")
            capacity = c5.number_input("Capacity", min_value=1, max_value=100, value=50)
            available = c6.number_input("Available Seats", min_value=0, max_value=100, value=50)
            status = c7.selectbox("Status", ["Running", "Available", "Maintenance", "Out of Service"])
            submitted = st.form_submit_button("➕ Add Bus", type="primary")
            if submitted:
                ids = [b["bus_id"].upper() for b in st.session_state.managed_buses]
                regs = [b["registration"].upper() for b in st.session_state.managed_buses]
                if not bus_id.strip() or not registration.strip() or not route_no.strip() or not driver.strip():
                    st.error("Please fill all bus details.")
                elif bus_id.upper() in ids:
                    st.error("Bus ID already exists.")
                elif registration.upper() in regs:
                    st.error("Registration number already exists.")
                elif available > capacity:
                    st.error("Available seats cannot be greater than capacity.")
                else:
                    st.session_state.managed_buses.append({"bus_id": bus_id.strip().upper(), "registration": registration.strip().upper(), "route_no": route_no.strip().upper(), "driver": driver.strip(), "capacity": int(capacity), "available": int(available), "status": status})
                    st.success(f"Bus {bus_id.upper()} added successfully.")

    elif action == "View Buses":
        st.dataframe(pd.DataFrame(st.session_state.managed_buses), hide_index=True, use_container_width=True)

    elif action == "Search Bus":
        q = st.text_input("Search by Bus ID, Registration Number, Route Number or Driver")
        if q.strip():
            ql = q.lower().strip()
            found = [b for b in st.session_state.managed_buses if ql in " ".join(str(v) for v in b.values()).lower()]
            if found:
                st.dataframe(pd.DataFrame(found), hide_index=True, use_container_width=True)
            else:
                st.warning("No matching bus found.")

    elif action == "Update Bus":
        if not st.session_state.managed_buses:
            st.info("No buses available.")
        else:
            selected_id = st.selectbox("Select Bus ID", [b["bus_id"] for b in st.session_state.managed_buses])
            bus = next(b for b in st.session_state.managed_buses if b["bus_id"] == selected_id)
            with st.form("update_bus_form"):
                c1, c2, c3 = st.columns(3)
                reg = c1.text_input("Registration Number", value=bus["registration"])
                route = c2.text_input("Route Number", value=bus["route_no"])
                drv = c3.text_input("Driver", value=bus["driver"])
                c4, c5, c6 = st.columns(3)
                cap = c4.number_input("Capacity", min_value=1, max_value=100, value=int(bus["capacity"]))
                avail = c5.number_input("Available Seats", min_value=0, max_value=100, value=int(bus["available"]))
                stat = c6.selectbox("Status", ["Running", "Available", "Maintenance", "Out of Service"], index=["Running", "Available", "Maintenance", "Out of Service"].index(bus["status"]) if bus["status"] in ["Running", "Available", "Maintenance", "Out of Service"] else 0)
                if st.form_submit_button("💾 Update Bus", type="primary"):
                    if avail > cap:
                        st.error("Available seats cannot be greater than capacity.")
                    else:
                        bus.update({"registration": reg.strip().upper(), "route_no": route.strip().upper(), "driver": drv.strip(), "capacity": int(cap), "available": int(avail), "status": stat})
                        st.success(f"Bus {selected_id} updated successfully.")

    elif action == "Delete Bus":
        if st.session_state.managed_buses:
            selected_id = st.selectbox("Select Bus ID to Delete", [b["bus_id"] for b in st.session_state.managed_buses])
            if st.button("🗑️ Delete Bus", type="secondary"):
                st.session_state.managed_buses = [b for b in st.session_state.managed_buses if b["bus_id"] != selected_id]
                st.success(f"Bus {selected_id} deleted successfully.")
                st.rerun()

    st.markdown("---")
    st.markdown("#### 🚌 Bus Status Report")
    if st.session_state.managed_buses:
        report_rows = []
        for b in st.session_state.managed_buses:
            route = next((r for r in st.session_state.managed_routes if r["route_no"] == b["route_no"]), None)
            passengers = int(b["capacity"]) - int(b["available"])
            report_rows.append({"Bus ID": b["bus_id"], "Route": b["route_no"], "Source": route["source"] if route else "-", "Destination": route["destination"] if route else "-", "Capacity": b["capacity"], "Passengers": passengers, "Available Seats": b["available"], "Status": b["status"]})
        st.dataframe(pd.DataFrame(report_rows), hide_index=True, use_container_width=True)

# -----------------------------------------------------------------------------
# ROUTE MANAGEMENT - Add / Stops / Update / Search
# -----------------------------------------------------------------------------
with tab_route:
    st.subheader("🗺️ Route Management")
    st.caption("Add routes, add stops, update routes and search routes.")
    route_action = st.radio("Select Operation", ["Add Route", "Add Stops", "Update Route", "Search Route", "View Routes"], horizontal=True, key="route_action")

    if route_action == "Add Route":
        with st.form("add_route_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            rno = c1.text_input("Route Number", placeholder="R30")
            source = c2.text_input("Source", placeholder="Erode")
            destination = c3.text_input("Destination", placeholder="Coimbatore")
            stops_text = st.text_input("Stops (comma separated)", placeholder="Erode, Perundurai, Tiruppur, Coimbatore")
            if st.form_submit_button("➕ Add Route", type="primary"):
                if any(r["route_no"].upper() == rno.strip().upper() for r in st.session_state.managed_routes):
                    st.error("Route number already exists.")
                elif not rno.strip() or not source.strip() or not destination.strip():
                    st.error("Please fill Route Number, Source and Destination.")
                else:
                    stops = [x.strip() for x in stops_text.split(",") if x.strip()]
                    if not stops or stops[0].lower() != source.strip().lower(): stops.insert(0, source.strip())
                    if stops[-1].lower() != destination.strip().lower(): stops.append(destination.strip())
                    st.session_state.managed_routes.append({"route_no": rno.strip().upper(), "source": source.strip(), "destination": destination.strip(), "stops": stops})
                    st.success(f"Route {rno.strip().upper()} added successfully.")

    elif route_action == "Add Stops":
        if st.session_state.managed_routes:
            rno = st.selectbox("Select Route", [r["route_no"] for r in st.session_state.managed_routes])
            route = next(r for r in st.session_state.managed_routes if r["route_no"] == rno)
            st.write("Current stops:", " → ".join(route["stops"]))
            new_stops = st.text_input("Add stop(s), comma separated")
            if st.button("➕ Add Stop(s)"):
                additions = [x.strip() for x in new_stops.split(",") if x.strip()]
                for stop in additions:
                    if stop.lower() not in [x.lower() for x in route["stops"]]:
                        route["stops"].insert(max(1, len(route["stops"])-1), stop)
                st.success("Stop list updated.")

    elif route_action == "Update Route":
        if st.session_state.managed_routes:
            rno = st.selectbox("Select Route", [r["route_no"] for r in st.session_state.managed_routes])
            route = next(r for r in st.session_state.managed_routes if r["route_no"] == rno)
            with st.form("update_route_form"):
                c1, c2, c3 = st.columns(3)
                src = c1.text_input("Source", value=route["source"])
                dst = c2.text_input("Destination", value=route["destination"])
                stops = c3.text_input("Stops (comma separated)", value=", ".join(route["stops"]))
                if st.form_submit_button("💾 Update Route", type="primary"):
                    route["source"] = src.strip(); route["destination"] = dst.strip(); route["stops"] = [x.strip() for x in stops.split(",") if x.strip()]
                    st.success(f"Route {rno} updated successfully.")

    elif route_action == "Search Route":
        q = st.text_input("Search by Route Number, Source, Destination or Stop")
        if q.strip():
            ql = q.lower().strip()
            found = [r for r in st.session_state.managed_routes if ql in r["route_no"].lower() or ql in r["source"].lower() or ql in r["destination"].lower() or any(ql in s.lower() for s in r["stops"])]
            if found:
                st.dataframe(pd.DataFrame([{"Route Number": r["route_no"], "Source": r["source"], "Destination": r["destination"], "Stops": " → ".join(r["stops"])} for r in found]), hide_index=True, use_container_width=True)
            else: st.warning("No matching route found.")

    elif route_action == "View Routes":
        st.dataframe(pd.DataFrame([{"Route Number": r["route_no"], "Source": r["source"], "Destination": r["destination"], "Stops": " → ".join(r["stops"])} for r in st.session_state.managed_routes]), hide_index=True, use_container_width=True)

# -----------------------------------------------------------------------------
# PASSENGER MANAGEMENT - Cancel Ticket and Passenger Details
# -----------------------------------------------------------------------------
with tab_passengers:
    st.subheader("🎫 Passenger Management")
    st.caption("Book tickets, cancel tickets, calculate fares and view passenger details.")
    p_action = st.radio("Select Operation", ["Book Ticket", "Cancel Ticket", "Calculate Fare", "View Passenger Details"], horizontal=True, key="p_action")

    if p_action == "Book Ticket":
        st.info("Use the full interactive seat-picker below. The booking form is available in the Bus Timings / booking workflow.")
        st.markdown("### Quick Passenger Booking")
        with st.form("quick_booking"):
            c1, c2 = st.columns(2)
            qname = c1.text_input("Passenger Name")
            qphone = c2.text_input("Phone Number")
            qfrom = c1.text_input("From")
            qto = c2.text_input("To")
            qfare = c1.number_input("Fare (₹)", min_value=0, value=100)
            if st.form_submit_button("🎫 Book Ticket", type="primary"):
                if not qname.strip() or not qphone.strip() or not qfrom.strip() or not qto.strip():
                    st.error("Please fill all passenger details.")
                else:
                    pnr = "SB" + str(random.randint(100000, 999999))
                    ticket = {"PNR": pnr, "ticket_no": "TKT" + str(random.randint(100000, 999999)), "passenger": qname.strip(), "phone": qphone.strip(), "From": qfrom.strip(), "To": qto.strip(), "Total_Paid": int(qfare), "Status": "Confirmed", "Booked_At": datetime.now().strftime("%d-%m-%Y %I:%M %p")}
                    st.session_state.booked_tickets.append(ticket)
                    st.success(f"Ticket booked successfully. PNR: {pnr}")

    elif p_action == "Cancel Ticket":
        active = [t for t in st.session_state.booked_tickets if t.get("Status", "Confirmed") != "Cancelled"]
        if not active:
            st.info("No active tickets available for cancellation.")
        else:
            options = [f'{t.get("PNR", "-")} — {t.get("passenger", "-")}' for t in active]
            chosen = st.selectbox("Select Ticket", options)
            idx = options.index(chosen)
            ticket = active[idx]
            if st.button("❌ Cancel Ticket", type="primary"):
                for t in st.session_state.booked_tickets:
                    if t.get("PNR") == ticket.get("PNR"):
                        t["Status"] = "Cancelled"
                        t["Cancelled_At"] = datetime.now().strftime("%d-%m-%Y %I:%M %p")
                st.success(f"Ticket {ticket.get('PNR')} cancelled successfully.")
                st.rerun()

    elif p_action == "Calculate Fare":
        c1, c2, c3 = st.columns(3)
        src = c1.selectbox("From", ALL_LOCATIONS, key="pm_fare_src")
        dst_options = [x for x in ALL_LOCATIONS if x != src]
        dst = c2.selectbox("To", dst_options, key="pm_fare_dst")
        service = c3.selectbox("Service Type", list(OFFICIAL_FARE_RULES.keys()), key="pm_fare_service")
        female = st.checkbox("Women passenger scheme", key="pm_fare_female")
        if st.button("Calculate Fare", key="pm_calc_fare"):
            km = calculate_route_distance(src, dst)
            total, breakdown = compute_official_fare(src, dst, service, km, female)
            st.success(f"Estimated Fare: ₹{total}")
            st.dataframe(pd.DataFrame([{"Item": k, "Amount": f"₹{v}" if isinstance(v, (int,float)) else v} for k,v in breakdown.items()]), hide_index=True, use_container_width=True)

    elif p_action == "View Passenger Details":
        if st.session_state.booked_tickets:
            rows = [t for t in st.session_state.booked_tickets]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        else:
            st.info("No passenger bookings yet.")

# -----------------------------------------------------------------------------
# STATUS REPORT & BONUS ANALYTICS
# -----------------------------------------------------------------------------
with tab_reports:
    st.subheader("📊 Bus Status Report & Analytics")
    st.caption("Required status report plus bonus passenger-load and peak-hour analysis.")
    status_rows = []
    for b in st.session_state.managed_buses:
        route = next((r for r in st.session_state.managed_routes if r["route_no"] == b["route_no"]), None)
        status_rows.append({"Bus ID": b["bus_id"], "Route": b["route_no"], "Source": route["source"] if route else "-", "Destination": route["destination"] if route else "-", "Capacity": b["capacity"], "Passengers": b["capacity"] - b["available"], "Available Seats": b["available"], "Status": b["status"]})
    st.dataframe(pd.DataFrame(status_rows), hide_index=True, use_container_width=True)

    st.markdown("### 👥 Passenger Load Analysis")
    load_df = pd.DataFrame([{"Bus ID": b["bus_id"], "Capacity": b["capacity"], "Passengers": b["capacity"]-b["available"], "Load %": round(((b["capacity"]-b["available"])/b["capacity"])*100, 1) if b["capacity"] else 0} for b in st.session_state.managed_buses])
    if not load_df.empty:
        st.dataframe(load_df, hide_index=True, use_container_width=True)
        st.bar_chart(load_df.set_index("Bus ID")["Load %"])

    st.markdown("### ⏰ Peak-Hour Analysis")
    if st.session_state.booked_tickets:
        times = []
        for t in st.session_state.booked_tickets:
            raw = t.get("Booked_At", "")
            try:
                times.append(datetime.strptime(raw, "%d-%m-%Y %I:%M %p").hour)
            except Exception:
                pass
        if times:
            counts = pd.Series(times).value_counts().sort_index()
            peak_df = pd.DataFrame({"Hour": counts.index.astype(int), "Bookings": counts.values})
            st.dataframe(peak_df, hide_index=True, use_container_width=True)
            st.bar_chart(peak_df.set_index("Hour")["Bookings"])
            peak_hour = int(counts.idxmax())
            st.success(f"Peak booking hour: {peak_hour:02d}:00 - {peak_hour:02d}:59")
        else:
            st.info("No valid booking times available for peak-hour analysis.")
    else:
        st.info("Book tickets to generate peak-hour analysis.")

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
    ai_added_bk = [b for b in st.session_state.custom_ai_buses if b.get("from") == bk_src and b.get("to") == bk_dst]
    all_booking_buses = available_buses + ai_added_bk

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
                    "Booked_At": datetime.now().strftime("%d-%b-%Y %I:%M %p")
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
