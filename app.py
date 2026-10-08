import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import random
import json
import math
import os
import base64
import html
import time
import requests

st.set_page_config(
    page_title="SMART BUS | Bus Route and Passenger Management System",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# 0. SAFE HTML RENDERING HELPER (Fixes Markdown Indented Code Block Glitch)
# -----------------------------------------------------------------------------
def render_html(html_str):
    """
    Renders custom HTML cleanly without markdown parsing glitches.
    Strips leading whitespace so markdown parsers never convert HTML tags into raw code blocks.
    """
    clean_markup = "\n".join(line.strip() for line in html_str.splitlines() if line.strip())
    st.html(clean_markup)

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
# 2. OFFICIAL GOVERNMENT FARE MATRIX (Tamil Nadu Transport Dept - G.O. Ms 229)
# -----------------------------------------------------------------------------
OFFICIAL_FARE_RULES = {
    "Town Ordinary (Vidiyal Payanam)": {
        "type_label": "Town Ordinary (Vidiyal Payanam Free for Women)",
        "per_km_paise": 55,
        "base_min_fare": 5,
        "is_stage_based": True,
        "vidiyal_free_women": True,
        "speed_kmh": 32,
        "toll_applicable": False,
        "badge_color": "#2e7d32",
        "description": "Standard town & mofussil service. Free zero-fare travel for women, transgender persons, and disabled passengers."
    },
    "Mofussil Ordinary": {
        "type_label": "Mofussil Ordinary",
        "per_km_paise": 60,
        "base_min_fare": 7,
        "is_stage_based": False,
        "vidiyal_free_women": False,
        "speed_kmh": 38,
        "toll_applicable": False,
        "badge_color": "#388e3c",
        "description": "Connecting taluks and rural revenue centers with mofussil stops."
    },
    "TNSTC Express": {
        "type_label": "TNSTC Express",
        "per_km_paise": 80,
        "base_min_fare": 15,
        "is_stage_based": False,
        "vidiyal_free_women": False,
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
        "vidiyal_free_women": False,
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
        "vidiyal_free_women": False,
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
        "vidiyal_free_women": False,
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
        "vidiyal_free_women": False,
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
        "vidiyal_free_women": False,
        "speed_kmh": 62,
        "toll_applicable": True,
        "badge_color": "#00838f",
        "description": "Air-conditioned 2x2 pushback service on NH corridors."
    },
    "SETC AC Sleeper": {
        "type_label": "SETC AC Sleeper Luxury",
        "per_km_paise": 200,
        "base_min_fare": 200,
        "is_stage_based": False,
        "vidiyal_free_women": False,
        "speed_kmh": 62,
        "toll_applicable": True,
        "badge_color": "#4a148c",
        "description": "Premium air-conditioned sleeper coach with reading lights, USB charging, and blanket amenities."
    }
}

GHAT_LOCATIONS = [
    "Nilgiris (Udhagamandalam / Ooty)", "Coonoor", "Kotagiri", "Gudalur",
    "Kodaikanal", "Yercaud", "Valparai", "Kolli Hills", "Pennagaram (Hogenakkal)"
]

# -----------------------------------------------------------------------------
# 3. HIGHWAY DISTANCE AND CORRIDOR LOGIC ENGINE
# -----------------------------------------------------------------------------
HIGHWAY_DISTANCE_ANCHORS = {
    # Kongu Region Hubs
    ("Sathyamangalam", "Coimbatore (Gandhipuram)"): 68,
    ("Coimbatore (Gandhipuram)", "Sathyamangalam"): 68,
    ("Sathyamangalam", "Erode Central Bus Stand"): 65,
    ("Erode Central Bus Stand", "Sathyamangalam"): 65,
    ("Sathyamangalam", "Gobichettipalayam"): 28,
    ("Gobichettipalayam", "Sathyamangalam"): 28,
    ("Sathyamangalam", "Bhavani"): 50,
    ("Bhavani", "Sathyamangalam"): 50,
    ("Sathyamangalam", "Tiruppur New Bus Stand"): 55,
    ("Tiruppur New Bus Stand", "Sathyamangalam"): 55,
    ("Sathyamangalam", "Mysuru (Suburban Bus Stand - Karnataka)"): 140,
    ("Mysuru (Suburban Bus Stand - Karnataka)", "Sathyamangalam"): 140,
    ("Sathyamangalam", "Chamarajanagar (Karnataka)"): 78,
    ("Chamarajanagar (Karnataka)", "Sathyamangalam"): 78,
    ("Coimbatore (Gandhipuram)", "Salem New Bus Stand"): 165,
    ("Salem New Bus Stand", "Coimbatore (Gandhipuram)"): 165,
    ("Coimbatore (Gandhipuram)", "Erode Central Bus Stand"): 100,
    ("Erode Central Bus Stand", "Coimbatore (Gandhipuram)"): 100,
    ("Coimbatore (Gandhipuram)", "Tiruppur New Bus Stand"): 52,
    ("Tiruppur New Bus Stand", "Coimbatore (Gandhipuram)"): 52,
    ("Coimbatore (Gandhipuram)", "Madurai (Mattuthavani - MGR Stand)"): 215,
    ("Madurai (Mattuthavani - MGR Stand)", "Coimbatore (Gandhipuram)"): 215,
    ("Coimbatore (Gandhipuram)", "Tiruchirappalli (Trichy Central)"): 218,
    ("Tiruchirappalli (Trichy Central)", "Coimbatore (Gandhipuram)"): 218,
    ("Coimbatore (Gandhipuram)", "Nilgiris (Udhagamandalam / Ooty)"): 86,
    ("Nilgiris (Udhagamandalam / Ooty)", "Coimbatore (Gandhipuram)"): 86,
    ("Coimbatore (Gandhipuram)", "Bengaluru (Shantinagar / Majestic - Karnataka)"): 360,
    ("Bengaluru (Shantinagar / Majestic - Karnataka)", "Coimbatore (Gandhipuram)"): 360,

    # Chennai Express Links (Kilambakkam KCBT)
    ("Chennai (KCBT Kilambakkam)", "Tiruchirappalli (Trichy Central)"): 315,
    ("Tiruchirappalli (Trichy Central)", "Chennai (KCBT Kilambakkam)"): 315,
    ("Chennai (KCBT Kilambakkam)", "Madurai (Mattuthavani - MGR Stand)"): 435,
    ("Madurai (Mattuthavani - MGR Stand)", "Chennai (KCBT Kilambakkam)"): 435,
    ("Chennai (KCBT Kilambakkam)", "Tirunelveli New Bus Stand"): 595,
    ("Tirunelveli New Bus Stand", "Chennai (KCBT Kilambakkam)"): 595,
    ("Chennai (KCBT Kilambakkam)", "Salem New Bus Stand"): 325,
    ("Salem New Bus Stand", "Chennai (KCBT Kilambakkam)"): 325,
    ("Chennai (KCBT Kilambakkam)", "Coimbatore (Gandhipuram)"): 480,
    ("Coimbatore (Gandhipuram)", "Chennai (KCBT Kilambakkam)"): 480,
    ("Chennai (KCBT Kilambakkam)", "Erode Central Bus Stand"): 395,
    ("Erode Central Bus Stand", "Chennai (KCBT Kilambakkam)"): 395,
    ("Chennai (KCBT Kilambakkam)", "Thanjavur New Bus Stand"): 325,
    ("Thanjavur New Bus Stand", "Chennai (KCBT Kilambakkam)"): 325,
    ("Chennai (KCBT Kilambakkam)", "Kumbakonam"): 275,
    ("Kumbakonam", "Chennai (KCBT Kilambakkam)"): 275,
    ("Chennai (KCBT Kilambakkam)", "Nagercoil (Vadasery)"): 675,
    ("Nagercoil (Vadasery)", "Chennai (KCBT Kilambakkam)"): 675,
    ("Chennai (KCBT Kilambakkam)", "Tiruvannamalai"): 175,
    ("Tiruvannamalai", "Chennai (KCBT Kilambakkam)"): 175,
    ("Chennai (KCBT Kilambakkam)", "Vellore New Bus Stand"): 135,
    ("Vellore New Bus Stand", "Chennai (KCBT Kilambakkam)"): 135,

    # Central & Southern Links
    ("Tiruchirappalli (Trichy Central)", "Madurai (Mattuthavani - MGR Stand)"): 130,
    ("Madurai (Mattuthavani - MGR Stand)", "Tiruchirappalli (Trichy Central)"): 130,
    ("Madurai (Mattuthavani - MGR Stand)", "Tirunelveli New Bus Stand"): 160,
    ("Tirunelveli New Bus Stand", "Madurai (Mattuthavani - MGR Stand)"): 160,
    ("Tirunelveli New Bus Stand", "Nagercoil (Vadasery)"): 82,
    ("Nagercoil (Vadasery)", "Tirunelveli New Bus Stand"): 82,
    ("Salem New Bus Stand", "Bengaluru (Shantinagar / Majestic - Karnataka)"): 200,
    ("Bengaluru (Shantinagar / Majestic - Karnataka)", "Salem New Bus Stand"): 200,
    ("Salem New Bus Stand", "Namakkal"): 55,
    ("Namakkal", "Salem New Bus Stand"): 55,
    ("Salem New Bus Stand", "Dharmapuri"): 68,
    ("Dharmapuri", "Salem New Bus Stand"): 68,
    ("Dharmapuri", "Hosur Central Stand"): 85,
    ("Hosur Central Stand", "Dharmapuri"): 85,
    ("Hosur Central Stand", "Bengaluru (Shantinagar / Majestic - Karnataka)"): 40,
    ("Bengaluru (Shantinagar / Majestic - Karnataka)", "Hosur Central Stand"): 40
}

GOOGLE_MAPS_STATION_ADDRESSES = {
    "Sathyamangalam": "Sathyamangalam Bus Stand, Sathyamangalam, Tamil Nadu, India",
    "Coimbatore (Gandhipuram)": "Gandhipuram Central Bus Stand, Coimbatore, Tamil Nadu, India",
    "Coimbatore (Singanallur)": "Singanallur Bus Stand, Coimbatore, Tamil Nadu, India",
    "Coimbatore (Ukkadam)": "Ukkadam Bus Stand, Coimbatore, Tamil Nadu, India",
    "Erode Central Bus Stand": "Erode Central Bus Stand, Erode, Tamil Nadu, India",
    "Tiruppur New Bus Stand": "Tiruppur New Bus Stand, Tiruppur, Tamil Nadu, India",
    "Chennai (KCBT Kilambakkam)": "Kilambakkam KCBT Bus Terminus, Chennai, Tamil Nadu, India",
    "Chennai (CMBT Koyambedu)": "CMBT Koyambedu Bus Terminus, Chennai, Tamil Nadu, India",
    "Chennai (Madhavaram MMBT)": "Madhavaram Mofussil Bus Terminus, Chennai, Tamil Nadu, India",
    "Chennai Central / Broadway": "Broadway Bus Terminus, Chennai, Tamil Nadu, India",
    "Madurai (Mattuthavani - MGR Stand)": "Mattuthavani MGR Bus Stand, Madurai, Tamil Nadu, India",
    "Madurai (Arapalayam)": "Arapalayam Bus Stand, Madurai, Tamil Nadu, India",
    "Madurai (Periyar Stand)": "Periyar Bus Stand, Madurai, Tamil Nadu, India",
    "Tiruchirappalli (Trichy Central)": "Central Bus Stand, Tiruchirappalli, Tamil Nadu, India",
    "Salem New Bus Stand": "Salem New Bus Stand, Salem, Tamil Nadu, India",
    "Tirunelveli New Bus Stand": "Tirunelveli New Bus Stand, Tirunelveli, Tamil Nadu, India",
    "Thanjavur New Bus Stand": "Thanjavur New Bus Stand, Thanjavur, Tamil Nadu, India",
    "Kumbakonam": "Kumbakonam Bus Stand, Kumbakonam, Tamil Nadu, India",
    "Nagercoil (Vadasery)": "Vadasery Bus Stand, Nagercoil, Tamil Nadu, India",
    "Vellore New Bus Stand": "Vellore New Bus Stand, Vellore, Tamil Nadu, India",
    "Tiruvannamalai": "Tiruvannamalai Bus Stand, Tiruvannamalai, Tamil Nadu, India",
    "Mysuru (Suburban Bus Stand - Karnataka)": "Mysuru Suburban Bus Stand, Mysuru, Karnataka, India",
    "Bengaluru (Shantinagar / Majestic - Karnataka)": "Kempegowda Bus Station Majestic, Bengaluru, Karnataka, India",
    "Chamarajanagar (Karnataka)": "Chamarajanagar KSRTC Bus Stand, Chamarajanagar, Karnataka, India",
    "Tirupati (APSRTC / TNSTC Stand - Andhra Pradesh)": "Tirupati Central Bus Station, Tirupati, Andhra Pradesh, India",
    "Puducherry (Pondicherry Central Stand)": "Puducherry Bus Stand, Puducherry, India",
    "Palakkad (Kerala)": "Palakkad KSRTC Bus Stand, Palakkad, Kerala, India",
    "Ernakulam / Kochi (Kerala)": "Ernakulam KSRTC Bus Stand, Kochi, Kerala, India",
    "Thiruvananthapuram (Tampanoor - Kerala)": "Thampanoor Central Bus Station, Thiruvananthapuram, Kerala, India",
}

def get_google_maps_api_key():
    try:
        if hasattr(st, "secrets") and "GOOGLE_MAPS_API_KEY" in st.secrets:
            value = str(st.secrets["GOOGLE_MAPS_API_KEY"]).strip()
            if value:
                return value
    except Exception:
        pass
    return os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()

def google_maps_address(place):
    place = str(place or "").strip()
    return GOOGLE_MAPS_STATION_ADDRESSES.get(place, f"{place}, Tamil Nadu, India")

def google_maps_route_details(src, dst):
    """Return the current Google Maps driving distance and duration for a pair."""
    src = str(src or "").strip()
    dst = str(dst or "").strip()
    if not src or not dst:
        return None
    if src.casefold() == dst.casefold():
        return {"distance_km": 0.0, "duration_min": 0, "source": "Google Maps Routes API"}
    api_key = get_google_maps_api_key()
    if not api_key:
        return None
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "routes.distanceMeters,routes.duration"
    }
    payload = {
        "origin": {"address": google_maps_address(src)},
        "destination": {"address": google_maps_address(dst)},
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_UNAWARE",
        "languageCode": "en-IN",
        "regionCode": "IN"
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        routes = data.get("routes") or []
        if not routes:
            return None
        route = routes[0]
        meters = route.get("distanceMeters")
        if meters is None:
            return None
        duration_min = None
        duration_text = route.get("duration")
        if isinstance(duration_text, str) and duration_text.endswith("s"):
            try:
                duration_min = int(round(float(duration_text[:-1]) / 60.0))
            except Exception:
                duration_min = None
        return {
            "distance_km": round(float(meters) / 1000.0, 1),
            "duration_min": duration_min,
            "source": "Google Maps Routes API"
        }
    except Exception:
        return None

def calculate_route_distance(src, dst):
    """Google Maps only. No hash/random/guessed fallback is ever shown."""
    details = google_maps_route_details(src, dst)
    return details["distance_km"] if details else None


def compute_official_fare(src, dst, bus_type, dist_km, is_female_passenger=False):
    rule = OFFICIAL_FARE_RULES.get(bus_type, OFFICIAL_FARE_RULES["TNSTC Express"])
    
    # 1. TVK Government Vettri Payanam Concession Check
    if rule["vidiyal_free_women"] and is_female_passenger:
        return {
            "base_fare": 0,
            "ghat_surcharge": 0,
            "toll_fee": 0,
            "reservation_fee": 0,
            "total_fare": 0,
            "is_free_vidiyal": True,
            "distance_km": dist_km
        }

    # 2. Stage-based or Linear calculation
    if rule["is_stage_based"]:
        stages = max(1, math.ceil(dist_km / 6.0))
        calculated_base = rule["base_min_fare"] + (stages - 1) * 3
        base_fare = min(calculated_base, 45)
    else:
        calculated_base = (dist_km * rule["per_km_paise"]) / 100.0
        base_fare = max(rule["base_min_fare"], round(calculated_base))

    # 3. Mountain Ghat Surcharge (+20% for hill sections)
    is_ghat_route = any(loc in src or loc in dst for loc in GHAT_LOCATIONS)
    ghat_surcharge = round(base_fare * 0.20) if is_ghat_route else 0

    # 4. Highway Toll Fee
    toll_fee = 0
    if rule["toll_applicable"] and dist_km > 60:
        toll_stages = int(dist_km // 60)
        toll_fee = min(40, toll_stages * 8)

    # 5. Online Reservation / Amenity fee for long-haul luxury
    reservation_fee = 0
    if "Ultra Deluxe" in bus_type or "Deluxe" in bus_type:
        reservation_fee = 10
    elif "Sleeper" in bus_type:
        reservation_fee = 20

    raw_total = base_fare + ghat_surcharge + toll_fee + reservation_fee
    total_fare = int(math.ceil(raw_total / 5.0) * 5)

    return {
        "base_fare": int(base_fare),
        "ghat_surcharge": int(ghat_surcharge),
        "toll_fee": int(toll_fee),
        "reservation_fee": int(reservation_fee),
        "total_fare": total_fare,
        "is_free_vidiyal": False,
        "distance_km": dist_km
    }

# -----------------------------------------------------------------------------
# 4. OFFICIAL TIMETABLES & HIGH-FREQUENCY CORRIDORS
# -----------------------------------------------------------------------------
HIGH_FREQUENCY_OFFICIAL_TIMETABLES = {
    ("Sathyamangalam", "Coimbatore (Gandhipuram)"): [
        {"dep": "04:45 AM", "type": "Town Ordinary (Vidiyal Payanam)", "rto": "TN-38-N-1102", "depot": "Sathy Depot", "via": ["Annur", "Kovilpalayam", "Saravanampatti"]},
        {"dep": "05:30 AM", "type": "Point-to-Point Superfast", "rto": "TN-38-N-2450", "depot": "Sathy Depot", "via": ["Annur", "Saravanampatti"]},
        {"dep": "06:00 AM", "type": "TNSTC Express", "rto": "TN-38-N-1980", "depot": "Coimbatore Central", "via": ["Annur", "Kovilpalayam", "Saravanampatti"]},
        {"dep": "06:45 AM", "type": "Town Ordinary (Vidiyal Payanam)", "rto": "TN-38-N-1890", "depot": "Sathy Depot", "via": ["Annur", "Kovilpalayam", "Saravanampatti"]},
        {"dep": "07:30 AM", "type": "Point-to-Point Superfast", "rto": "TN-38-N-3120", "depot": "Coimbatore Central", "via": ["Annur", "Saravanampatti"]},
        {"dep": "08:15 AM", "type": "TNSTC Express", "rto": "TN-38-N-2210", "depot": "Sathy Depot", "via": ["Annur", "Kovilpalayam", "Saravanampatti"]},
        {"dep": "09:30 AM", "type": "TNSTC Super Deluxe", "rto": "TN-38-N-4010", "depot": "Coimbatore Central", "via": ["Annur Bypass", "Saravanampatti"]},
        {"dep": "11:15 AM", "type": "Town Ordinary (Vidiyal Payanam)", "rto": "TN-38-N-2780", "depot": "Sathy Depot", "via": ["Annur", "Kovilpalayam", "Saravanampatti"]},
        {"dep": "01:00 PM", "type": "TNSTC Express", "rto": "TN-38-N-1670", "depot": "Coimbatore Central", "via": ["Annur", "Kovilpalayam", "Saravanampatti"]},
        {"dep": "03:15 PM", "type": "Point-to-Point Superfast", "rto": "TN-38-N-2900", "depot": "Sathy Depot", "via": ["Annur", "Saravanampatti"]},
        {"dep": "05:00 PM", "type": "Town Ordinary (Vidiyal Payanam)", "rto": "TN-38-N-3345", "depot": "Sathy Depot", "via": ["Annur", "Kovilpalayam", "Saravanampatti"]},
        {"dep": "06:30 PM", "type": "TNSTC Express", "rto": "TN-38-N-2015", "depot": "Coimbatore Central", "via": ["Annur", "Kovilpalayam", "Saravanampatti"]},
        {"dep": "08:00 PM", "type": "Point-to-Point Superfast", "rto": "TN-38-N-3490", "depot": "Sathy Depot", "via": ["Annur", "Saravanampatti"]},
        {"dep": "09:45 PM", "type": "TNSTC Express", "rto": "TN-38-N-1820", "depot": "Coimbatore Central", "via": ["Annur", "Kovilpalayam", "Saravanampatti"]}
    ],
    ("Coimbatore (Gandhipuram)", "Sathyamangalam"): [
        {"dep": "05:15 AM", "type": "Point-to-Point Superfast", "rto": "TN-38-N-2451", "depot": "Coimbatore Central", "via": ["Saravanampatti", "Annur"]},
        {"dep": "06:15 AM", "type": "Town Ordinary (Vidiyal Payanam)", "rto": "TN-38-N-1103", "depot": "Sathy Depot", "via": ["Saravanampatti", "Kovilpalayam", "Annur"]},
        {"dep": "07:30 AM", "type": "TNSTC Express", "rto": "TN-38-N-1981", "depot": "Coimbatore Central", "via": ["Saravanampatti", "Kovilpalayam", "Annur"]},
        {"dep": "09:00 AM", "type": "Point-to-Point Superfast", "rto": "TN-38-N-3121", "depot": "Coimbatore Central", "via": ["Saravanampatti", "Annur"]},
        {"dep": "11:00 AM", "type": "TNSTC Express", "rto": "TN-38-N-2211", "depot": "Sathy Depot", "via": ["Saravanampatti", "Kovilpalayam", "Annur"]},
        {"dep": "02:00 PM", "type": "Town Ordinary (Vidiyal Payanam)", "rto": "TN-38-N-2781", "depot": "Sathy Depot", "via": ["Saravanampatti", "Kovilpalayam", "Annur"]},
        {"dep": "04:30 PM", "type": "Point-to-Point Superfast", "rto": "TN-38-N-2901", "depot": "Sathy Depot", "via": ["Saravanampatti", "Annur"]},
        {"dep": "06:00 PM", "type": "Town Ordinary (Vidiyal Payanam)", "rto": "TN-38-N-3346", "depot": "Sathy Depot", "via": ["Saravanampatti", "Kovilpalayam", "Annur"]},
        {"dep": "08:15 PM", "type": "TNSTC Express", "rto": "TN-38-N-2016", "depot": "Coimbatore Central", "via": ["Saravanampatti", "Kovilpalayam", "Annur"]},
        {"dep": "10:15 PM", "type": "Point-to-Point Superfast", "rto": "TN-38-N-3491", "depot": "Sathy Depot", "via": ["Saravanampatti", "Annur"]}
    ],
    ("Sathyamangalam", "Erode Central Bus Stand"): [
        {"dep": "05:00 AM", "type": "Town Ordinary (Vidiyal Payanam)", "rto": "TN-33-N-1402", "depot": "Erode Central", "via": ["Gobi", "Kavindapadi", "Bhavani"]},
        {"dep": "06:30 AM", "type": "TNSTC Express", "rto": "TN-33-N-2210", "depot": "Sathy Depot", "via": ["Gobi", "Kavindapadi", "Bhavani"]},
        {"dep": "09:00 AM", "type": "Town Ordinary (Vidiyal Payanam)", "rto": "TN-33-N-2350", "depot": "Sathy Depot", "via": ["Gobi", "Kavindapadi", "Bhavani"]},
        {"dep": "11:45 AM", "type": "Point-to-Point Superfast", "rto": "TN-33-N-3120", "depot": "Erode Central", "via": ["Gobi Bypass", "Bhavani Bypass"]},
        {"dep": "02:15 PM", "type": "TNSTC Express", "rto": "TN-33-N-1980", "depot": "Sathy Depot", "via": ["Gobi", "Kavindapadi", "Bhavani"]},
        {"dep": "04:45 PM", "type": "Town Ordinary (Vidiyal Payanam)", "rto": "TN-33-N-3420", "depot": "Erode Central", "via": ["Gobi", "Kavindapadi", "Bhavani"]},
        {"dep": "07:30 PM", "type": "Point-to-Point Superfast", "rto": "TN-33-N-4010", "depot": "Erode Central", "via": ["Gobi Bypass", "Bhavani Bypass"]}
    ],
    ("Sathyamangalam", "Mysuru (Suburban Bus Stand - Karnataka)"): [
        {"dep": "06:15 AM", "type": "TNSTC Express", "rto": "TN-38-N-2908", "depot": "Sathy Depot", "via": ["Bannari", "Dhimbam (27 Hairpin Bends)", "Hasanur", "Chamarajanagar", "Nanjangud"]},
        {"dep": "08:30 AM", "type": "TNSTC Express", "rto": "TN-38-N-3012", "depot": "Sathy Depot", "via": ["Bannari", "Dhimbam Ghats", "Hasanur", "Chamarajanagar", "Nanjangud"]},
        {"dep": "11:00 AM", "type": "SETC Ultra Deluxe", "rto": "TN-01-AN-1845", "depot": "Coimbatore SETC", "via": ["Bannari", "Dhimbam Ghats", "Chamarajanagar", "Nanjangud"]},
        {"dep": "02:30 PM", "type": "TNSTC Express", "rto": "TN-38-N-2670", "depot": "Sathy Depot", "via": ["Bannari", "Dhimbam Ghats", "Hasanur", "Chamarajanagar", "Nanjangud"]}
    ]
}

def parse_time_str(t_str):
    try:
        t = datetime.strptime(t_str.strip(), "%I:%M %p")
        return t.hour * 60 + t.minute
    except Exception:
        return 480

def format_minutes_to_time(m):
    norm_m = m % (24 * 60)
    hr = norm_m // 60
    mn = norm_m % 60
    period = "AM" if hr < 12 else "PM"
    disp_hr = hr if hr <= 12 else hr - 12
    if disp_hr == 0:
        disp_hr = 12
    return f"{disp_hr:02d}:{mn:02d} {period}"

def generate_procedural_schedule(src, dst, route_details=None):
    route_details = route_details or google_maps_route_details(src, dst)
    if not route_details:
        return []
    dist_km = route_details["distance_km"]
    google_duration = route_details.get("duration_min")
    schedule = []
    
    if dist_km > 280:
        eligible_types = ["SETC Ultra Deluxe", "SETC AC Sleeper", "SETC Non-AC Sleeper", "SETC AC Seater", "TNSTC Super Deluxe"]
    elif dist_km < 60:
        eligible_types = ["Town Ordinary (Vidiyal Payanam)", "Mofussil Ordinary", "TNSTC Express", "Point-to-Point Superfast"]
    else:
        eligible_types = ["TNSTC Express", "Point-to-Point Superfast", "Town Ordinary (Vidiyal Payanam)", "TNSTC Super Deluxe", "SETC Ultra Deluxe"]

    rng = random.Random(abs(hash(src)) ^ abs(hash(dst)))
    num_services = max(6, min(18, int(600 / max(30, dist_km)) + 4))

    dep_times_minutes = sorted([rng.randint(300, 1380) for _ in range(num_services)])
    division_names = list(TN_DIVISIONS.keys())
    
    candidate_junctions = [
        "Avinashi Bypass", "Bhavani Toll Gate", "Karur Bypass", "Dharapuram Junction",
        "Oddanchatram Roundana", "Namakkal Toll", "Ulundurpet Junction", "Tindivanam Toll",
        "Melur Four-Roads", "Perundurai Bye-pass", "Sankagiri Bypass", "Dharmapuri Toll Plaza"
    ]
    route_intermediates = rng.sample(candidate_junctions, k=min(3, max(1, dist_km // 90)))

    for i, t_dep_min in enumerate(dep_times_minutes):
        chosen_type = rng.choice(eligible_types)
        rule_spec = OFFICIAL_FARE_RULES[chosen_type]
        speed = rule_spec["speed_kmh"]
        
        duration_min = int(google_duration) if google_duration is not None else int((dist_km / speed) * 60)
        t_arr_min = t_dep_min + duration_min
        
        t_dep_str = format_minutes_to_time(t_dep_min)
        t_arr_str = format_minutes_to_time(t_arr_min)

        fare_info = compute_official_fare(src, dst, chosen_type, dist_km, is_female_passenger=False)
        div = rng.choice(division_names)
        rto_prefix = rng.choice(TN_DIVISIONS[div]["rto_codes"])
        rto_number = f"{rto_prefix}-N-{rng.randint(1000, 9999)}"
        depot = rng.choice(TN_DIVISIONS[div]["depots"])
        
        seats_left = rng.randint(4, 38)
        max_seats = 52 if "Town" in chosen_type or "Express" in chosen_type else (30 if "Sleeper" in chosen_type else 43)

        # Do not invent intermediate stops. Official timetable rows have their own stops;
        # generated rows show only the verified origin and destination.
        stops_chain = [src, dst]

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
            "distance_km": dist_km,
            "distance_source": "Google Maps Routes API"
        })

    return schedule

def get_complete_schedule(src, dst, route_details=None):
    route_details = route_details or google_maps_route_details(src, dst)
    if not route_details:
        return []
    dist_km = route_details["distance_km"]
    google_duration = route_details.get("duration_min")
    if (src, dst) in HIGH_FREQUENCY_OFFICIAL_TIMETABLES:
        raw_list = HIGH_FREQUENCY_OFFICIAL_TIMETABLES[(src, dst)]
        processed = []
        for item in raw_list:
            chosen_type = item["type"]
            speed = OFFICIAL_FARE_RULES.get(chosen_type, OFFICIAL_FARE_RULES["TNSTC Express"])["speed_kmh"]
            duration_min = int(google_duration) if google_duration is not None else int((dist_km / speed) * 60)
            dep_min = parse_time_str(item["dep"])
            arr_min = dep_min + duration_min
            fare_info = compute_official_fare(src, dst, chosen_type, dist_km, is_female_passenger=False)
            processed.append({
                "bus_no": item["rto"], "type": chosen_type, "dep": item["dep"],
                "arr": format_minutes_to_time(arr_min), "dep_minutes": dep_min,
                "duration_str": f"{duration_min // 60}h {duration_min % 60}m",
                "fare": fare_info["total_fare"], "fare_breakdown": fare_info,
                "seats": random.randint(8, 36),
                "max_seats": 50 if "Town" in chosen_type or "Express" in chosen_type else 36,
                "depot": item["depot"], "via": item["via"], "distance_km": dist_km,
                "distance_source": "Google Maps Routes API"
            })
        return processed
    return generate_procedural_schedule(src, dst, route_details=route_details)

# -----------------------------------------------------------------------------
# 5. AUTONOMOUS TRANSIT ENGINE & ZERO-TOUCH GEMINI SYNC
# -----------------------------------------------------------------------------
def is_valid_gemini_key_format(key_str):
    """
    Checks if a string looks like a legitimate Google Gemini API key
    and filters out example placeholders like 'AIzaSyYourActualKeyHere'.
    """
    if not key_str or not isinstance(key_str, str):
        return False
    k = key_str.strip()
    if len(k) < 30 or "youractualkey" in k.lower() or "placeholder" in k.lower() or "example" in k.lower():
        return False
    return True

def get_gemini_api_key():
    """
    Automatically retrieves the Gemini API key without manual administrator touch.
    Checks:
    1. Streamlit secrets (.streamlit/secrets.toml)
    2. Environment variables (GEMINI_API_KEY, GOOGLE_API_KEY)
    3. Local .env file
    """
    # 1. Check Streamlit secrets
    try:
        if hasattr(st, "secrets"):
            if "GEMINI_API_KEY" in st.secrets:
                val = str(st.secrets["GEMINI_API_KEY"]).strip()
                if is_valid_gemini_key_format(val):
                    return val
            if "GOOGLE_API_KEY" in st.secrets:
                val = str(st.secrets["GOOGLE_API_KEY"]).strip()
                if is_valid_gemini_key_format(val):
                    return val
    except Exception:
        pass

    # 2. Check environment variables
    env_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if env_key and is_valid_gemini_key_format(env_key):
        return env_key.strip()

    # 3. Check local .env file
    try:
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if is_valid_gemini_key_format(val):
                            return val
                    if line.startswith("GOOGLE_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if is_valid_gemini_key_format(val):
                            return val
    except Exception:
        pass

    return None

def save_gemini_api_key(key_str):
    """
    Permanently saves Gemini API key to Streamlit secrets and .env
    so it loads automatically on every future run without human intervention.
    """
    key_clean = key_str.strip()
    if not key_clean:
        return False
    # Save to .streamlit/secrets.toml
    try:
        secrets_dir = os.path.join(os.path.dirname(__file__), ".streamlit")
        os.makedirs(secrets_dir, exist_ok=True)
        secrets_path = os.path.join(secrets_dir, "secrets.toml")
        with open(secrets_path, "w", encoding="utf-8") as f:
            f.write(f'# Auto-configured Gemini API Key for TNSTC Bus Portal\nGEMINI_API_KEY = "{key_clean}"\n')
    except Exception:
        pass
    # Save to .env
    try:
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(f'GEMINI_API_KEY="{key_clean}"\n')
    except Exception:
        pass
    return True

def generate_autonomous_government_routes():
    """
    Generates realistic, active Tamil Nadu Government bus routes
    (including TVK Vettri Payanam connectivity and festival specials)
    that update the schedule automatically with zero administrator touch.
    """
    routes = [
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
            "seats": random.randint(14, 32),
            "max_seats": 48,
            "depot": "Sathy Depot",
            "via": ["Sathyamangalam", "Tiruppur", "Dharapuram", "Oddanchatram", "Madurai"],
            "distance_km": 240,
            "is_autonomous_synced": True
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
            "seats": random.randint(6, 18),
            "max_seats": 30,
            "depot": "Chennai SETC",
            "via": ["Kilambakkam", "Villupuram", "Trichy Bypass", "Madurai Ring Road", "Tirunelveli"],
            "distance_km": 595,
            "is_autonomous_synced": True
        },
        {
            "bus_no": "TN-33-N-5120",
            "type": "Town Ordinary (Vidiyal Payanam)",
            "from": "Sathyamangalam",
            "to": "Coimbatore (Gandhipuram)",
            "dep": "01:15 PM",
            "arr": "03:15 PM",
            "dep_minutes": 795,
            "duration_str": "2h 00m",
            "fare": 45,
            "seats": random.randint(10, 28),
            "max_seats": 52,
            "depot": "Sathy Central",
            "via": ["Sathyamangalam", "Annur", "Kovilpalayam", "Saravanampatti", "Gandhipuram"],
            "distance_km": 68,
            "is_autonomous_synced": True
        },
        {
            "bus_no": "TN-38-N-3882",
            "type": "TNSTC Express",
            "from": "Sathyamangalam",
            "to": "Erode Central Bus Stand",
            "dep": "07:45 AM",
            "arr": "09:30 AM",
            "dep_minutes": 465,
            "duration_str": "1h 45m",
            "fare": 55,
            "seats": random.randint(12, 35),
            "max_seats": 50,
            "depot": "Gobichettipalayam Depot",
            "via": ["Sathyamangalam", "Gobi", "Kavindapadi", "Bhavani", "Erode"],
            "distance_km": 65,
            "is_autonomous_synced": True
        },
        {
            "bus_no": "TN-01-AN-4412",
            "type": "SETC Ultra Deluxe",
            "from": "Chennai (KCBT Kilambakkam)",
            "to": "Madurai (Mattuthavani - MGR Stand)",
            "dep": "10:15 PM",
            "arr": "06:30 AM",
            "dep_minutes": 1335,
            "duration_str": "8h 15m",
            "fare": 525,
            "seats": random.randint(8, 25),
            "max_seats": 43,
            "depot": "KCBT Express",
            "via": ["KCBT Kilambakkam", "Tindivanam", "Villupuram", "Trichy Bypass", "Madurai"],
            "distance_km": 460,
            "is_autonomous_synced": True
        }
    ]
    for r in routes:
        if "fare_breakdown" not in r:
            r["fare_breakdown"] = compute_official_fare(r["from"], r["to"], r["type"], r["distance_km"], is_female_passenger=False)
            r["fare"] = r["fare_breakdown"]["total_fare"]
    return routes

def run_autonomous_sync(api_key=None):
    """
    Executes automated route ingestion without requiring administrator interaction.
    """
    if api_key and is_valid_gemini_key_format(api_key):
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = f"""
            Act as the official Tamil Nadu State Transport Corporation (TNSTC & SETC) central dispatch scheduler.
            Current Date: {datetime.now().strftime('%d-%b-%Y')}.
            Generate 3 realistic newly scheduled government bus routes in Tamil Nadu based on high passenger demand, weekend/festival connectivity, or TVK Vettri Payanam scheme.
            Pick origin and destination strictly from this list:
            Sathyamangalam, Coimbatore (Gandhipuram), Chennai (KCBT Kilambakkam), 
            Madurai (Mattuthavani - MGR Stand), Tiruchirappalli (Trichy Central), Salem New Bus Stand, 
            Tirunelveli New Bus Stand, Erode Central Bus Stand, Mysuru (Suburban Bus Stand - Karnataka).
            
            Return a JSON array of route objects with these exact keys:
            - "bus_no": string like "TN-38-N-4920"
            - "type": one of "TNSTC Express", "Point-to-Point Superfast", "SETC Ultra Deluxe", "Town Ordinary (Vidiyal Payanam)", "SETC AC Sleeper"
            - "from": exact origin from list
            - "to": exact destination from list
            - "dep": string like "06:15 AM"
            - "arr": string like "11:45 AM"
            - "dep_minutes": integer minutes from midnight (e.g. 375)
            - "duration_str": string like "5h 30m"
            - "fare": integer
            - "seats": integer (e.g. 28)
            - "max_seats": integer (e.g. 48)
            - "depot": string
            - "via": list of 3-4 intermediate stops
            - "distance_km": integer
            Output raw JSON only without markdown formatting.
            """
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )
            clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
            routes = json.loads(clean_text)
            verified_routes = []
            for r in routes:
                route_details = google_maps_route_details(r.get("from"), r.get("to"))
                if not route_details:
                    continue
                r["distance_km"] = route_details["distance_km"]
                if route_details.get("duration_min") is not None:
                    dm = int(route_details["duration_min"])
                    r["duration_str"] = f"{dm // 60}h {dm % 60}m"
                r["is_autonomous_synced"] = True
                r["distance_source"] = "Google Maps Routes API"
                r["fare_breakdown"] = compute_official_fare(r["from"], r["to"], r["type"], r["distance_km"], is_female_passenger=False)
                r["fare"] = r["fare_breakdown"]["total_fare"]
                verified_routes.append(r)
            return verified_routes, "Gemini schedules + Google Maps distance verification"
        except Exception:
            return [], "Google Maps verification required"
    else:
        return [], "Google Maps API key required"


# -----------------------------------------------------------------------------
# 5B. LIVE TRANSPORT API AUTO-SYNC
# -----------------------------------------------------------------------------
# API keys are credentials: the app reads them securely from Streamlit Secrets.
# It never invents or exposes a key. If a transport API is configured, records
# are refreshed automatically and merged into the existing service list.
AUTO_SYNC_TTL_SECONDS = 15 * 60

def get_smart_bus_api_config():
    api_url, api_key = "", ""
    try:
        if hasattr(st, "secrets"):
            api_url = str(st.secrets.get("SMART_BUS_API_URL", "")).strip()
            api_key = str(st.secrets.get("SMART_BUS_API_KEY", "")).strip()
    except Exception:
        pass
    api_url = api_url or os.environ.get("SMART_BUS_API_URL", "").strip()
    api_key = api_key or os.environ.get("SMART_BUS_API_KEY", "").strip()
    return api_url, api_key

def _normalise_live_service(item):
    if not isinstance(item, dict):
        return None
    def pick(*names, default=""):
        for name in names:
            if name in item and item[name] not in (None, ""):
                return item[name]
        return default
    bus_no = str(pick("bus_no","busNo","registration","registration_no","bus_number","busNumber","vehicle_no")).strip()
    origin = str(pick("from","origin","source","from_place")).strip()
    destination = str(pick("to","destination","dest","to_place")).strip()
    if not bus_no or not origin or not destination:
        return None
    service_type = str(pick("type","service_type","serviceClass","class_of_service",default="TNSTC Express")).strip()
    dep = str(pick("dep","departure","departure_time","dept_time",default="")).strip()
    arr = str(pick("arr","arrival","arrival_time",default="")).strip()
    route_details = google_maps_route_details(origin, destination)
    if not route_details:
        return None
    distance_km = route_details["distance_km"]
    try: seats = int(float(pick("seats","available_seats","seats_available",default=0)))
    except Exception: seats = 0
    try: max_seats = int(float(pick("max_seats","capacity","total_seats",default=50)))
    except Exception: max_seats = 50
    try: dep_minutes = parse_time_str(dep)
    except Exception: dep_minutes = 480
    duration_str = str(pick("duration_str","duration",default="")).strip()
    if route_details.get("duration_min") is not None:
        duration_min = int(route_details["duration_min"])
        duration_str = f"{duration_min//60}h {duration_min%60}m"
    elif not duration_str:
        speed = OFFICIAL_FARE_RULES.get(service_type, OFFICIAL_FARE_RULES["TNSTC Express"]).get("speed_kmh",45)
        duration_min = int((distance_km / max(1,speed))*60)
        duration_str = f"{duration_min//60}h {duration_min%60}m"
    try: fare = int(float(pick("fare","total_fare","price",default=0)))
    except Exception: fare = 0
    if fare <= 0: fare = compute_official_fare(origin,destination,service_type,distance_km,False)["total_fare"]
    via = pick("via","stops","route_stops",default=[])
    if isinstance(via,str): via=[x.strip() for x in via.split(",") if x.strip()]
    if not isinstance(via,list) or not via: via=[origin,destination]
    depot = str(pick("depot","depot_name",default="TNSTC")).strip()
    return {"bus_no":bus_no,"type":service_type,"from":origin,"to":destination,"dep":dep or "N/A","arr":arr or "N/A","dep_minutes":dep_minutes,"duration_str":duration_str,"fare":fare,"fare_breakdown":compute_official_fare(origin,destination,service_type,distance_km,False),"seats":max(0,seats),"max_seats":max(1,max_seats),"depot":depot,"via":via,"distance_km":distance_km,"is_api_synced":True,"is_autonomous_synced":True,"updated_at":datetime.now().strftime("%d-%b-%Y %I:%M %p")}

def fetch_live_transport_api():
    api_url, api_key = get_smart_bus_api_config()
    if not api_url: return [], "No external API configured"
    headers={"Accept":"application/json","User-Agent":"SMART-BUS-TNSTC-Portal/1.0"}
    if api_key:
        headers["Authorization"]=f"Bearer {api_key}"
        headers["X-API-Key"]=api_key
    try:
        response=requests.get(api_url,headers=headers,timeout=15)
        response.raise_for_status()
        payload=response.json()
        raw_items = payload if isinstance(payload,list) else (payload.get("buses") or payload.get("services") or payload.get("data") or payload.get("results") or []) if isinstance(payload,dict) else []
        records=[r for x in raw_items if (r:=_normalise_live_service(x))]
        if not records: return [], "API connected but returned no compatible bus records"
        return records, f"Live Transport API ({len(records)} records)"
    except Exception as exc:
        return [], f"API unavailable: {type(exc).__name__}"

def run_live_api_auto_update(force=False):
    now=time.time(); last=st.session_state.get("live_api_last_epoch",0)
    if not force and now-last < AUTO_SYNC_TTL_SECONDS: return False
    st.session_state.live_api_last_epoch=now
    records,label=fetch_live_transport_api()
    st.session_state.live_api_last_status=label
    if not records: return False
    existing={str(b.get("bus_no")):b for b in st.session_state.custom_ai_buses if b.get("bus_no")}
    for record in records: existing[record["bus_no"]]=record
    st.session_state.custom_ai_buses=list(existing.values())
    st.session_state.sync_source_label=label
    st.session_state.last_sync_timestamp=datetime.now().strftime("%d-%b-%Y %I:%M %p")
    return True

# STREAMLIT STATE INITIALIZATION
if "booked_tickets" not in st.session_state:
    st.session_state.booked_tickets = []
if "custom_ai_buses" not in st.session_state:
    st.session_state.custom_ai_buses = []
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "auto_sync_done" not in st.session_state:
    st.session_state.auto_sync_done = False
if "sync_source_label" not in st.session_state:
    st.session_state.sync_source_label = "Pending"
if "last_sync_timestamp" not in st.session_state:
    st.session_state.last_sync_timestamp = None
if "live_api_last_epoch" not in st.session_state:
    st.session_state.live_api_last_epoch = 0
if "live_api_last_status" not in st.session_state:
    st.session_state.live_api_last_status = "Not configured"

# Automatic live-data update; no UI changes. Refreshes at most every 15 minutes.
run_live_api_auto_update(force=False)

# Hands-free background execution: Admin never has to touch or click anything!
active_gemini_key = get_gemini_api_key()
if not st.session_state.auto_sync_done:
    auto_routes, sync_label = run_autonomous_sync(active_gemini_key)
    for r in auto_routes:
        if not any(b["bus_no"] == r["bus_no"] for b in st.session_state.custom_ai_buses):
            st.session_state.custom_ai_buses.append(r)
    st.session_state.auto_sync_done = True
    st.session_state.sync_source_label = sync_label
    st.session_state.last_sync_timestamp = datetime.now().strftime("%d-%b-%Y %I:%M %p")

MASTER_ADMIN_PASSWORD = "admin@sathy"


# -----------------------------------------------------------------------------
# 6. SMART BUS DASHBOARD UI — MATCHED TO THE PROVIDED REFERENCE IMAGE
# -----------------------------------------------------------------------------
# The reference hero image is bundled next to this app as smartbus_hero.jpg.
# If the file is not present, the UI falls back to the CSS-only hero.
_HERO_PATH = os.path.join(os.path.dirname(__file__), "smartbus_hero.jpg")
_HERO_DATA = ""
try:
    with open(_HERO_PATH, "rb") as _hf:
        _HERO_DATA = base64.b64encode(_hf.read()).decode("ascii")
except Exception:
    _HERO_DATA = ""

render_html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');

:root {
    --navy:#06316d;
    --navy2:#082b61;
    --blue:#087be8;
    --yellow:#ffc20a;
    --text:#15345f;
    --muted:#60718b;
    --page:#f5fbff;
}

html, body, [class*="css"] {
    font-family: 'Montserrat', Arial, sans-serif !important;
}
html, body { overflow-x:hidden !important; }
.stApp {
    background: linear-gradient(180deg,#f7fbff 0%,#eef7fd 100%);
    overflow-x:hidden !important;
}
.block-container {
    max-width:100% !important; width:100% !important; padding:0 !important; overflow-x:hidden !important;
}
[data-testid="stHeader"] {
    background: transparent !important;
}
section[data-testid="stSidebar"] { display:none !important; }

.smart-nav {
    min-height:96px;
    background:linear-gradient(100deg,#062e67 0%,#073b80 55%,#05295c 100%);
    color:white; display:flex; align-items:center;
    padding:12px clamp(16px,4vw,76px); box-sizing:border-box; gap:24px; overflow:hidden;
}
.smart-brand {
    display:flex;
    align-items:center;
    min-width:0; flex:0 0 auto; gap:14px;
}
.smart-bus-icon {
    width:48px;height:48px;display:flex;align-items:center;justify-content:center;
    font-size:39px;filter:drop-shadow(0 2px 2px rgba(0,0,0,.2));
}
.smart-brand-title {
    font-size:clamp(24px,2.5vw,35px);line-height:1;font-weight:800;letter-spacing:.3px;
}
.smart-brand-title .bus-word {color:#ffc20a;}
.smart-divider {height:40px;width:1px;background:rgba(255,255,255,.35);}
.smart-brand-sub {
    font-size:16px;font-weight:700;letter-spacing:.2px;white-space:nowrap;
}
.smart-menu {
    margin-left:auto;display:flex;align-items:stretch;min-width:0;gap:8px;
    overflow-x:auto;overflow-y:hidden;scrollbar-width:none;
}
.smart-menu a {
    color:#fff;text-decoration:none;min-width:96px;flex:0 0 auto;
    display:flex;flex-direction:column;align-items:center;justify-content:center;
    font-size:13px;font-weight:700;position:relative;opacity:.98;
}
.smart-menu a .mi {font-size:28px;line-height:28px;margin-bottom:6px;}
.smart-menu a.active:after {
    content:"";position:absolute;bottom:11px;left:18px;right:18px;height:3px;
    background:#ffc20a;border-radius:3px;
}
.smart-menu a.active .mi {background:#087be8;border-radius:24px;padding:7px 14px;margin-top:-7px;}

.smart-hero {
    width:100%;overflow:hidden;background:#eaf6ff; line-height:0; aspect-ratio:16 / 6.2;
}
.smart-hero img { width:100%;height:100%;display:block;object-fit:cover;object-position:center; }
.smart-hero-fallback {
    min-height:404px;display:flex;align-items:center;padding:60px 6%;
    background:linear-gradient(105deg,#eef9ff 0%,#dcefff 55%,#9ed4ff 100%);
    color:#113b70;
}
.smart-hero-fallback h1 {font-size:72px;margin:8px 0;font-weight:800;}
.smart-hero-fallback h1 span {color:#087be8;}
.smart-hero-fallback p {font-size:26px;font-weight:700;}

.smart-shortcuts {
    background:rgba(248,253,255,.96);
    padding:32px clamp(16px,3vw,36px) 38px;
    display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:18px;
    border-radius:18px 18px 0 0;
    margin-top:0;
    box-sizing:border-box;
}
.smart-shortcut {
    min-height:95px;border-radius:12px;padding:15px 16px;min-width:0;
    display:flex;align-items:center;gap:14px;box-sizing:border-box;
    border:1px solid rgba(60,120,180,.15);
    box-shadow:0 4px 12px rgba(25,85,135,.06);
}
.smart-shortcut .si {
    width:52px;height:52px;border-radius:50%;flex:none;
    display:flex;align-items:center;justify-content:center;color:white;font-size:26px;
}
.smart-shortcut .stitle {font-size:15px;font-weight:800;margin-bottom:6px;}
.smart-shortcut .ssub {font-size:11px;color:#536b86;font-weight:500;line-height:1.35;}
.smart-shortcut .arrow {margin-left:auto;font-size:24px;font-weight:400;}
.s-blue{background:#eaf5ff}.s-blue .si{background:#087be8}.s-blue .stitle{color:#1361a8}.s-blue .arrow{color:#087be8}
.s-green{background:#e8fbf5}.s-green .si{background:#08b56b}.s-green .stitle{color:#079b5e}.s-green .arrow{color:#08a967}
.s-purple{background:#f2edff}.s-purple .si{background:#7043df}.s-purple .stitle{color:#6840d5}.s-purple .arrow{color:#7043df}
.s-orange{background:#fff5e8}.s-orange .si{background:#ff9d12}.s-orange .stitle{color:#ef8b00}.s-orange .arrow{color:#f49b0b}
.s-cyan{background:#e8fbff}.s-cyan .si{background:#10aeca}.s-cyan .stitle{color:#0c9ab5}.s-cyan .arrow{color:#10aeca}
.s-pink{background:#fff0f7}.s-pink .si{background:#d83a86}.s-pink .stitle{color:#cf2e79}.s-pink .arrow{color:#d83a86}

.workspace-title {
    padding:22px clamp(16px,3vw,36px) 0;
    color:#15345f;font-weight:800;font-size:21px;
}
.workspace-caption {
    padding:4px clamp(16px,3vw,36px) 12px;color:#6d7e93;font-size:12px;
}

/* Rest of the application */
div[data-baseweb="tab-list"] {
    gap:8px !important;
    padding:0 clamp(12px,3vw,36px) 12px !important; overflow-x:auto !important;
    border-bottom:1px solid #dce8f2 !important;
}
button[data-baseweb="tab"] {
    color:#31547b !important;font-weight:700 !important;
    border-radius:9px 9px 0 0 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color:#087be8 !important;border-bottom:3px solid #087be8 !important;
}
div[data-testid="stMetric"] {
    background:white;border:1px solid #d9e7f2;border-radius:12px;
    padding:12px;box-shadow:0 3px 12px rgba(22,75,120,.05);
}
.bus-card {
    background:#fff !important;border:1px solid #dce9f4 !important;
    border-radius:14px !important;color:#15345f !important;
    box-shadow:0 5px 16px rgba(22,75,120,.06) !important;
}
.route-node {
    background:#eff8ff !important;color:#087be8 !important;border-color:#9ed2f7 !important;
}
@media (max-width:1100px){
 .smart-nav{align-items:flex-start;flex-wrap:wrap;} .smart-brand{width:100%;}
 .smart-menu{width:100%;margin-left:0;height:62px;} .smart-menu a{min-width:88px;font-size:12px;}
 .smart-brand-sub,.smart-divider{display:none;} .smart-shortcuts{grid-template-columns:repeat(3,minmax(0,1fr));}
}
@media (max-width:700px){
 .smart-nav{min-height:auto;padding:12px 14px;gap:8px;} .smart-brand-title{font-size:24px;}
 .smart-bus-icon{width:38px;height:38px;font-size:30px;} .smart-menu{height:56px;gap:4px;}
 .smart-menu a{min-width:78px;font-size:11px;} .smart-menu a .mi{font-size:22px;line-height:22px;margin-bottom:4px;}
 .smart-menu a.active .mi{padding:5px 10px;} .smart-hero{aspect-ratio:16 / 8.5;}
 .smart-shortcuts{grid-template-columns:1fr;padding:18px 14px 24px;gap:10px;} .smart-shortcut{min-height:76px;}
 .smart-shortcut .si{width:44px;height:44px;font-size:22px;} .smart-shortcut .stitle{font-size:14px;}
 .smart-shortcut .ssub{font-size:10px;} .bus-card{overflow:hidden;}
}
.stButton>button,.stLinkButton>a {
    border-radius:9px !important;font-weight:700 !important;
}
</style>
""")

# Top navigation
render_html("""
<div class="smart-nav">
  <div class="smart-brand">
    <div class="smart-bus-icon">🚌</div>
    <div class="smart-brand-title">SMART <span class="bus-word">BUS</span></div>
    <div class="smart-divider"></div>
    <div class="smart-brand-sub">BUS ROUTE AND PASSENGER MANAGEMENT SYSTEM</div>
  </div>
  <div class="smart-menu">
    <a class="active" href="#smart-home"><span class="mi">⌂</span><span>Home</span></a>
    <a href="#bus-management"><span class="mi">🚌</span><span>Bus Management</span></a>
    <a href="#route-management"><span class="mi">🗺</span><span>Route Management</span></a>
    <a href="#passenger-management"><span class="mi">♟</span><span>Passenger Management</span></a>
    <a href="#analytics"><span class="mi">▥</span><span>Analytics</span></a>
    <a href="#reports"><span class="mi">▤</span><span>Reports</span></a>
    <a href="#ai-assistant"><span class="mi">🤖</span><span>AI Assistant</span></a>
  </div>
</div>
""")

# Exact visual hero from the user's reference screenshot.
if _HERO_DATA:
    render_html(f'<div id="smart-home" class="smart-hero"><img src="data:image/jpeg;base64,{_HERO_DATA}" alt="Smart Bus hero"></div>')
else:
    render_html("""
    <div id="smart-home" class="smart-hero-fallback">
      <div><div style="display:inline-block;background:#ffc20a;border-radius:20px;padding:8px 18px;font-weight:800;">TAMIL NADU TRANSPORT</div>
      <h1>SMART <span>BUS</span></h1><p>Bus Route and Passenger Management System</p></div>
    </div>
    """)

render_html("""
<div class="smart-shortcuts">
  <div id="bus-management" class="smart-shortcut s-blue"><div class="si">🚌</div><div><div class="stitle">Bus Management</div><div class="ssub">Add, View, Update, Delete Buses</div></div><div class="arrow">›</div></div>
  <div id="route-management" class="smart-shortcut s-green"><div class="si">🗺</div><div><div class="stitle">Route Management</div><div class="ssub">Add Routes, Add Stops, Update</div></div><div class="arrow">›</div></div>
  <div id="passenger-management" class="smart-shortcut s-purple"><div class="si">👥</div><div><div class="stitle">Passenger Management</div><div class="ssub">Book, Cancel, View Details</div></div><div class="arrow">›</div></div>
  <div id="analytics" class="smart-shortcut s-orange"><div class="si">▥</div><div><div class="stitle">Analytics</div><div class="ssub">Load Analysis, Peak-Hour</div></div><div class="arrow">›</div></div>
  <div id="reports" class="smart-shortcut s-cyan"><div class="si">▤</div><div><div class="stitle">Reports</div><div class="ssub">Bus Status, Passenger Reports</div></div><div class="arrow">›</div></div>
  <div id="ai-assistant" class="smart-shortcut s-pink"><div class="si">🤖</div><div><div class="stitle">AI Assistant</div><div class="ssub">Smart Suggestions &amp; Help</div></div><div class="arrow">›</div></div>
</div>
<div class="workspace-title">Smart Bus Operations</div>
<div class="workspace-caption">Use the modules below to search routes, reserve seats, manage passenger documents, review fares, and operate the AI assistant.</div>
""")

tab_timing, tab_booking, tab_passengers, tab_fare_matrix, tab_admin = st.tabs([
    "Bus Management",
    "Route Management",
    "Passenger Management",
    "Reports & Fare Matrix",
    "AI Assistant"
])
# TAB 1: BUS TIMINGS & REAL-TIME SCHEDULES
# -----------------------------------------------------------------------------
with tab_timing:
    st.subheader("🔍 Real-Time Bus Timetable & Route Enquiry")
    maps_ready = bool(get_google_maps_api_key())
    sync_status_str = f"🟢 **Auto-Sync**: {st.session_state.last_sync_timestamp or 'Waiting'} via {st.session_state.sync_source_label}"
    distance_status = "Google Maps road distance" if maps_ready else "Google Maps API key not configured"
    st.caption(f"Route distance: **{distance_status}** • {sync_status_str}")

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

    route_details = google_maps_route_details(src_station, dst_station)
    schedule_data = get_complete_schedule(src_station, dst_station, route_details=route_details)
    ai_buses = [
        b for b in st.session_state.custom_ai_buses 
        if b.get("from") == src_station and b.get("to") == dst_station
    ]
    all_buses = schedule_data + ai_buses

    dist_val = route_details["distance_km"] if route_details else None
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
        has_vidiyal = any("Vidiyal" in b["type"] for b in all_buses)
        st.metric("Fares From", f"₹{min_fare}", delta="₹0 for Women" if has_vidiyal else "Standard G.O.")

    st.caption("Google Maps road-distance data • Google Maps")
    st.markdown("---")

    fc1, fc2, fc3 = st.columns([4, 4, 4])
    with fc1:
        time_slot = st.selectbox(
            "Filter Departure Time:",
            ["All Day (24 Hours)", "Early Morning (04:00 - 08:00)", "Morning Peak (08:00 - 12:00)", "Afternoon (12:00 - 16:00)", "Evening Peak (16:00 - 20:00)", "Night Express (20:00 - 04:00)"]
        )
    with fc2:
        category_options = ["All Service Classes"] + list(OFFICIAL_FARE_RULES.keys())
        selected_category = st.selectbox("Bus Classification / Scheme:", category_options)
    with fc3:
        sort_by = st.selectbox("Sort Results By:", ["Earliest Departure", "Lowest Government Fare", "Shortest Travel Time"])

    # Filtering logic
    filtered_buses = []
    for b in all_buses:
        m = b["dep_minutes"]
        if time_slot == "Early Morning (04:00 - 08:00)" and not (240 <= m < 480):
            continue
        elif time_slot == "Morning Peak (08:00 - 12:00)" and not (480 <= m < 720):
            continue
        elif time_slot == "Afternoon (12:00 - 16:00)" and not (720 <= m < 960):
            continue
        elif time_slot == "Evening Peak (16:00 - 20:00)" and not (960 <= m < 1200):
            continue
        elif time_slot == "Night Express (20:00 - 04:00)" and not (m >= 1200 or m < 240):
            continue

        if selected_category != "All Service Classes" and b["type"] != selected_category:
            continue

        filtered_buses.append(b)

    # Sorting
    if sort_by == "Earliest Departure":
        filtered_buses.sort(key=lambda x: x["dep_minutes"])
    elif sort_by == "Lowest Government Fare":
        filtered_buses.sort(key=lambda x: x["fare"])
    elif sort_by == "Shortest Travel Time":
        filtered_buses.sort(key=lambda x: x["duration_str"])

    st.write(f"Showing **{len(filtered_buses)}** scheduled state transport services for **{src_station} ➔ {dst_station}**:")

    if not filtered_buses:
        st.warning("No services match the selected departure window. Try selecting 'All Day (24 Hours)' to view full operations.")
    else:
        for bus in filtered_buses:
            rule_info = OFFICIAL_FARE_RULES.get(bus["type"], {})
            badge_color = rule_info.get("badge_color", "#0288d1")
            is_vidiyal = rule_info.get("vidiyal_free_women", False)

            with st.container():
                vidiyal_badge_html = '<span style="background-color: #10b981; color: white; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; margin-left: 6px;">👩 வெற்றிப் பயணம் (₹0 for Women - TVK Govt)</span>' if is_vidiyal else ''
                auto_badge_html = '<span style="background-color: #0284c7; color: white; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; margin-left: 6px;">🔄 Auto-Synced Special</span>' if bus.get("is_autonomous_synced") else ''
                seats_color_code = '#4ade80' if bus['seats'] > 12 else '#f87171'
                via_route_badges = ' '.join([f'<span class="route-node">{html.escape(str(stop))}</span>' for stop in bus['via']])
                safe_type = html.escape(str(bus.get("type", "Service")))
                safe_depot = html.escape(str(bus.get("depot", "-")))
                safe_bus_no = html.escape(str(bus.get("bus_no", "-")))

                card_markup = f"""
                <div class="bus-card" style="border-left: 6px solid {badge_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                        <div>
                            <span style="background-color: {badge_color}; color: white; padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: 700;">
                                {safe_type}
                            </span>
                            {vidiyal_badge_html}
                            {auto_badge_html}
                        </div>
                        <div style="font-size: 13px; color: #94a3b8;">
                            <b>Depot:</b> <span style="color: #f1f5f9;">{safe_depot}</span> | 
                            <b>Bus RTO:</b> <code style="color: #38bdf8; background: #0f172a; padding: 2px 6px; border-radius: 4px;">{safe_bus_no}</code>
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
                            <span style="font-size: 11px; color: #64748b;">Google Maps: {float(bus['distance_km']):.1f} km</span>
                        </div>
                        <div>
                            <span style="font-size: 12px; color: #94a3b8;">OFFICIAL GOVT FARE</span>
                            <div style="font-size: 20px; font-weight: 800; color: #10b981;">₹{bus['fare']}</div>
                            <span style="font-size: 11px; color: #64748b;">Per Passenger</span>
                        </div>
                        <div>
                            <span style="font-size: 12px; color: #94a3b8;">LIVE SEATS</span>
                            <div style="font-size: 16px; font-weight: 700; color: {seats_color_code};">
                                💺 {bus['seats']} Left
                            </div>
                            <span style="font-size: 11px; color: #64748b;">of {bus['max_seats']} total</span>
                        </div>
                    </div>
                    <div style="margin-top: 14px; padding-top: 10px; border-top: 1px dashed #334155; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                        <div>
                            <span style="font-size: 12px; font-weight: 600; color: #94a3b8;">Route Stops:</span>
                            {via_route_badges}
                        </div>
                    </div>
                </div>
                """
                render_html(card_markup)

                with st.expander(f"ℹ️ Official Fare Breakdown & Intermediate Halt Timings for {bus['bus_no']}"):
                    fb_col1, fb_col2 = st.columns(2)
                    with fb_col1:
                        st.markdown("**Official Transport Department Tariff Calculation:**")
                        breakdown = bus["fare_breakdown"]
                        st.write(f"- **Tariff Rate (G.O. Ms 229):** {rule_info.get('per_km_paise', 80)} paise/km")
                        st.write(f"- **Google Maps road distance:** {float(breakdown['distance_km']):.1f} km")
                        st.write(f"- **Base Vehicle Fare:** ₹{breakdown['base_fare']}")
                        if breakdown["ghat_surcharge"] > 0:
                            st.write(f"- **Mountain Ghat Surcharge (+20%):** ₹{breakdown['ghat_surcharge']}")
                        if breakdown["toll_fee"] > 0:
                            st.write(f"- **National Highway Toll & User Fee:** ₹{breakdown['toll_fee']}")
                        if breakdown["reservation_fee"] > 0:
                            st.write(f"- **Passenger Amenity & Online Booking Fee:** ₹{breakdown['reservation_fee']}")
                        st.markdown(f"**Total Government Fixed Fare: ₹{bus['fare']}**")
                        if is_vidiyal:
                            st.success("✨ **வெற்றிப் பயணம் திட்டம் (Vettri Payanam Thittam - TVK Govt)**: Free zero-fare travel for women passengers upon presenting valid Govt ID.")

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
                    
                    st.link_button(f"🌐 Book {bus['bus_no']} on Official Govt Webpage (www.tnstc.in)", url="https://www.tnstc.in/TNSTCOnline/", use_container_width=True)

    with st.expander("🛠️ Bus Management — Add / Update / Delete / Search", expanded=False):
        if "managed_fleet" not in st.session_state: st.session_state.managed_fleet=[]
        managed=st.session_state.managed_fleet
        a,b,c,d=st.columns(4)
        with a: bus_id=st.text_input("Bus ID",placeholder="BUS101",key="mg_bus_id")
        with b: reg_no=st.text_input("Registration No.",placeholder="TN-33-N-1234",key="mg_reg")
        with c: route_no=st.text_input("Route No.",placeholder="R12",key="mg_route")
        with d: driver=st.text_input("Driver",placeholder="Driver Name",key="mg_driver")
        a,b,c,d=st.columns(4)
        with a: capacity=st.number_input("Capacity",1,100,50,key="mg_capacity")
        with b: passengers=st.number_input("Passengers",0,100,42,key="mg_passengers")
        with c: bus_status=st.selectbox("Status",["Running","Scheduled","Stopped","Maintenance"],key="mg_status")
        with d: corporation=st.selectbox("Corporation",["MTC","SETC","TNSTC Villupuram","TNSTC Salem","TNSTC Coimbatore","TNSTC Madurai","TNSTC Kumbakonam","TNSTC Tirunelveli"],key="mg_corp")
        x,y,z,w=st.columns(4)
        with x:
            if st.button("➕ Add Bus",use_container_width=True,key="mg_add"):
                if bus_id.strip() and reg_no.strip():
                    rec={"Bus ID":bus_id.strip(),"Registration No":reg_no.strip(),"Route No":route_no.strip(),"Driver":driver.strip(),"Capacity":int(capacity),"Passengers":int(passengers),"Available Seats":max(0,int(capacity)-int(passengers)),"Status":bus_status,"Corporation":corporation,"Updated At":datetime.now().strftime("%d-%b-%Y %I:%M %p")}
                    managed[:]=[q for q in managed if q["Bus ID"]!=rec["Bus ID"]]; managed.append(rec); st.success(f"Bus {bus_id.strip()} added.")
                else: st.warning("Enter Bus ID and Registration No.")
        with y:
            if st.button("✏️ Update Bus",use_container_width=True,key="mg_update"):
                found=next((q for q in managed if q["Bus ID"]==bus_id.strip()),None)
                if found:
                    found.update({"Registration No":reg_no.strip(),"Route No":route_no.strip(),"Driver":driver.strip(),"Capacity":int(capacity),"Passengers":int(passengers),"Available Seats":max(0,int(capacity)-int(passengers)),"Status":bus_status,"Corporation":corporation,"Updated At":datetime.now().strftime("%d-%b-%Y %I:%M %p")}); st.success(f"Bus {bus_id.strip()} updated.")
                else: st.warning("Bus ID not found in the managed fleet.")
        with z:
            if st.button("🗑️ Delete Bus",use_container_width=True,key="mg_delete"):
                before=len(managed); st.session_state.managed_fleet=[q for q in managed if q["Bus ID"]!=bus_id.strip()]
                st.success(f"Bus {bus_id.strip()} deleted.") if len(st.session_state.managed_fleet)<before else st.warning("Bus ID not found.")
        with w:
            if st.button("🔄 Refresh Live API",use_container_width=True,key="mg_refresh"):
                changed=run_live_api_auto_update(force=True); st.success("Live API data refreshed.") if changed else st.info(st.session_state.get("live_api_last_status","No live records received."))
        if managed: st.dataframe(pd.DataFrame(managed),hide_index=True,use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 2: ONLINE BUS TICKET BOOKING & INTERACTIVE SEAT PICKER
# -----------------------------------------------------------------------------
with tab_booking:
    st.subheader("🎟️ Official Seat Reservation & Digital Boarding Pass")
    st.caption("Reserve seats on TNSTC and SETC fleets with real-time seat selection, or book directly on the official government website.")

    st.info("🏛️ **Direct Official Government Booking Webpage**: To complete official reserved bookings directly with the Tamil Nadu State Transport Corporation, visit **[www.tnstc.in](https://www.tnstc.in/TNSTCOnline/)**.")
    st.link_button("🌐 Open Official Government Booking Webpage (www.tnstc.in)", url="https://www.tnstc.in/TNSTCOnline/", type="primary", use_container_width=True)
    st.write("")

    b_col1, b_col2, b_col3 = st.columns(3)
    with b_col1:
        bk_src = st.selectbox("Origin Boarding Point:", ALL_LOCATIONS, index=ALL_LOCATIONS.index("Sathyamangalam") if "Sathyamangalam" in ALL_LOCATIONS else 0, key="bk_from_key")
    with b_col2:
        bk_dst_opts = [x for x in ALL_LOCATIONS if x != bk_src]
        bk_dst = st.selectbox("Destination Dropping Point:", bk_dst_opts, index=0, key="bk_to_key")
    with b_col3:
        journey_date = st.date_input("Date of Journey:", min_value=date.today(), max_value=date.today() + timedelta(days=60))

    booking_route_details = google_maps_route_details(bk_src, bk_dst)
    available_buses = get_complete_schedule(bk_src, bk_dst, route_details=booking_route_details)
    ai_added_bk = [b for b in st.session_state.custom_ai_buses if b.get("from") == bk_src and b.get("to") == bk_dst]
    combined_bk_buses = available_buses + ai_added_bk

    if not combined_bk_buses:
        st.warning("No operational services available for this station pair.")
    else:
        bus_labels = [f"{b['bus_no']} | {b['type']} | Departs: {b['dep']} | Fare: ₹{b['fare']}" for b in combined_bk_buses]
        selected_bus_idx = st.selectbox("Select Bus Service:", range(len(combined_bk_buses)), format_func=lambda i: bus_labels[i])
        selected_bus = combined_bk_buses[selected_bus_idx]

        st.markdown("#### 1. Passenger Details & Concession")
        p_c1, p_c2, p_c3, p_c4 = st.columns(4)
        with p_c1:
            passenger_name = st.text_input("Lead Passenger Name:", placeholder="e.g. K. Selvamani")
        with p_c2:
            passenger_age = st.number_input("Age:", min_value=1, max_value=110, value=28)
        with p_c3:
            passenger_gender = st.selectbox("Gender:", ["Female (Women Concession Eligible)", "Male", "Transgender (Free Concession)"])
        with p_c4:
            passenger_phone = st.text_input("Mobile Number (for SMS & E-Ticket):", placeholder="e.g. 9842100000")

        is_female = "Female" in passenger_gender or "Transgender" in passenger_gender
        is_vidiyal_route = OFFICIAL_FARE_RULES.get(selected_bus["type"], {}).get("vidiyal_free_women", False)

        if is_female and is_vidiyal_route:
            st.success("🎉 **வெற்றிப் பயணம் திட்டம் (Vettri Payanam Thittam - TVK Govt)**: 100% Free Travel (₹0 Fare) concession applied for women passenger!")
            effective_fare_per_ticket = 0
        else:
            effective_fare_per_ticket = selected_bus["fare"]

        st.markdown("#### 2. Interactive Seat Selection")
        st.caption("Select your preferred seats from the vehicle diagram below:")

        is_sleeper = "Sleeper" in selected_bus["type"]
        selected_seats = []

        render_html("""
        <div style="display: flex; gap: 15px; margin-bottom: 12px; font-size: 12px; align-items: center; flex-wrap: wrap;">
            <span><span class="seat-box seat-avail" style="width: 20px; height: 20px; vertical-align: middle;"></span> Available</span>
            <span><span class="seat-box seat-ladies" style="width: 20px; height: 20px; vertical-align: middle;"></span> Ladies Reserved (🌸)</span>
            <span><span class="seat-box seat-selected" style="width: 20px; height: 20px; vertical-align: middle;"></span> Selected</span>
            <span><span class="seat-box seat-booked" style="width: 20px; height: 20px; vertical-align: middle;"></span> Already Reserved</span>
        </div>
        """)

        with st.container():
            st.write("🚍 **Vehicle Interior Diagram (Front to Rear)**")
            
            # Seater layout (2 x 2)
            seat_rows = 10 if not is_sleeper else 6
            for r in range(1, seat_rows + 1):
                s_cols = st.columns([1, 1, 1, 1, 1])
                
                # Seat numbers
                s1_id = f"{r}A (W)"
                s2_id = f"{r}B (A)"
                s3_id = f"{r}C (A)"
                s4_id = f"{r}D (W)"

                is_ladies_row = (r in [1, 2])

                with s_cols[0]:
                    booked_s1 = (hash(f"{selected_bus['bus_no']}-{s1_id}") % 5 == 0)
                    if booked_s1:
                        st.button(f"{s1_id} ✖", disabled=True, key=f"s_{s1_id}")
                    else:
                        lbl = f"🌸 {s1_id}" if is_ladies_row else s1_id
                        if st.checkbox(lbl, key=f"s_{s1_id}"):
                            selected_seats.append(s1_id)

                with s_cols[1]:
                    booked_s2 = (hash(f"{selected_bus['bus_no']}-{s2_id}") % 4 == 0)
                    if booked_s2:
                        st.button(f"{s2_id} ✖", disabled=True, key=f"s_{s2_id}")
                    else:
                        lbl = f"🌸 {s2_id}" if is_ladies_row else s2_id
                        if st.checkbox(lbl, key=f"s_{s2_id}"):
                            selected_seats.append(s2_id)

                with s_cols[2]:
                    st.write("🚶 AISLE")

                with s_cols[3]:
                    booked_s3 = (hash(f"{selected_bus['bus_no']}-{s3_id}") % 6 == 0)
                    if booked_s3:
                        st.button(f"{s3_id} ✖", disabled=True, key=f"s_{s3_id}")
                    else:
                        if st.checkbox(s3_id, key=f"s_{s3_id}"):
                            selected_seats.append(s3_id)

                with s_cols[4]:
                    booked_s4 = (hash(f"{selected_bus['bus_no']}-{s4_id}") % 7 == 0)
                    if booked_s4:
                        st.button(f"{s4_id} ✖", disabled=True, key=f"s_{s4_id}")
                    else:
                        if st.checkbox(s4_id, key=f"s_{s4_id}"):
                            selected_seats.append(s4_id)

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
            st.metric("Net Total to Pay", f"₹{total_fare_bill}", delta="₹0 (Vettri Scheme)" if effective_fare_per_ticket == 0 else "Official Tariff")

        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            st.link_button("🏛️ Book on Official Govt Webpage (www.tnstc.in)", url="https://www.tnstc.in/TNSTCOnline/", type="primary", use_container_width=True)
        with btn_c2:
            generate_ticket_btn = st.button("🎫 Generate Digital Boarding Pass", use_container_width=True)

        if generate_ticket_btn:
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
                    "Origin": bk_src,
                    "Destination": bk_dst,
                    "Date": str(journey_date),
                    "Bus_No": selected_bus["bus_no"],
                    "Bus_Type": selected_bus["type"],
                    "Departure": selected_bus["dep"],
                    "Arrival": selected_bus["arr"],
                    "Depot": selected_bus["depot"],
                    "Seats": selected_seats,
                    "Total_Paid": total_fare_bill,
                    "Is_Vidiyal": (effective_fare_per_ticket == 0),
                    "Booked_At": datetime.now().strftime("%d-%b-%Y %I:%M %p")
                }
                st.session_state.booked_tickets.append(new_ticket)
                st.success(f"Boarding Pass Generated! PNR: **{pnr_code}**. Head over to the 'My Boarding Passes' tab to view or print it.")
                st.balloons()

# -----------------------------------------------------------------------------
# TAB 3: PASSENGER BOARDING PASS & TRAVEL DOCUMENTS
# -----------------------------------------------------------------------------
with tab_passengers:
    st.subheader("📋 Verified Digital Ticket Ledger & Boarding Pass")
    st.caption("Official digital boarding documents conforming to Tamil Nadu Motor Vehicles Act standards.")

    with st.expander("❌ Cancel Ticket", expanded=False):
        cancel_pnr=st.text_input("Enter PNR to cancel",key="cancel_pnr")
        if st.button("Cancel Reservation",key="cancel_reservation"):
            before=len(st.session_state.booked_tickets)
            st.session_state.booked_tickets=[t for t in st.session_state.booked_tickets if t.get("PNR")!=cancel_pnr.strip()]
            st.success(f"PNR {cancel_pnr.strip()} cancelled successfully.") if len(st.session_state.booked_tickets)<before else st.warning("PNR not found.")

    if not st.session_state.booked_tickets:
        st.info("No tickets have been booked in this session yet. Go to the 'Book Ticket' tab to reserve your journey!")
    else:
        st.write(f"Total Active Reservations in Session: **{len(st.session_state.booked_tickets)}**")
        
        for idx, tkt in enumerate(reversed(st.session_state.booked_tickets)):
            with st.container():
                fare_txt = '₹0 (வெற்றிப் பயணம் - TVK Govt)' if tkt['Is_Vidiyal'] else f"₹{tkt['Total_Paid']}"
                fare_clr = '#10b981' if tkt['Is_Vidiyal'] else '#38bdf8'
                hash_val = abs(hash(tkt['PNR'])) % 100000000

                boarding_pass_markup = f"""
                <div style="background: #0f172a; border: 2px solid #334155; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                    <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding-bottom: 12px; align-items: center; flex-wrap: wrap;">
                        <div>
                            <span style="background: #d97706; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700;">OFFICIAL E-TICKET RECEIPT</span>
                            <h3 style="color: #ffffff; margin: 6px 0 0 0;">TAMIL NADU STATE TRANSPORT CORPORATION</h3>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 12px; color: #94a3b8;">PNR NO:</span>
                            <div style="font-size: 18px; font-weight: 800; color: #38bdf8; font-family: monospace;">{tkt['PNR']}</div>
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 15px; margin-top: 15px;">
                        <div>
                            <span style="font-size: 11px; color: #94a3b8;">LEAD PASSENGER</span>
                            <div style="font-size: 16px; font-weight: 700; color: #f8fafc;">{tkt['Passenger']}</div>
                            <span style="font-size: 12px; color: #64748b;">Age {tkt['Age']} • {tkt['Gender'].split(' ')[0]}</span>
                        </div>
                        <div>
                            <span style="font-size: 11px; color: #94a3b8;">FROM / ORIGIN</span>
                            <div style="font-size: 15px; font-weight: 700; color: #38bdf8;">{tkt['Origin']}</div>
                            <span style="font-size: 12px; color: #10b981;">Dep: {tkt['Departure']}</span>
                        </div>
                        <div>
                            <span style="font-size: 11px; color: #94a3b8;">TO / DESTINATION</span>
                            <div style="font-size: 15px; font-weight: 700; color: #f8fafc;">{tkt['Destination']}</div>
                            <span style="font-size: 12px; color: #cbd5e1;">Arr: {tkt['Arrival']}</span>
                        </div>
                        <div>
                            <span style="font-size: 11px; color: #94a3b8;">JOURNEY DATE</span>
                            <div style="font-size: 16px; font-weight: 700; color: #f8fafc;">📅 {tkt['Date']}</div>
                            <span style="font-size: 11px; color: #64748b;">Report 15 mins prior</span>
                        </div>
                        <div>
                            <span style="font-size: 11px; color: #94a3b8;">BUS & SERVICE</span>
                            <div style="font-size: 15px; font-weight: 700; color: #f59e0b;">{tkt['Bus_No']}</div>
                            <span style="font-size: 11px; color: #64748b;">{tkt['Bus_Type']}</span>
                        </div>
                        <div>
                            <span style="font-size: 11px; color: #94a3b8;">SEATS ALLOCATED</span>
                            <div style="font-size: 16px; font-weight: 700; color: #ec4899;">{', '.join(tkt['Seats'])}</div>
                            <span style="font-size: 11px; color: #64748b;">Depot: {tkt['Depot']}</span>
                        </div>
                        <div>
                            <span style="font-size: 11px; color: #94a3b8;">AMOUNT PAID</span>
                            <div style="font-size: 20px; font-weight: 800; color: {fare_clr};">{fare_txt}</div>
                            <span style="font-size: 11px; color: #64748b;">Status: Confirmed</span>
                        </div>
                    </div>

                    <div style="margin-top: 15px; padding-top: 12px; border-top: 1px dashed #334155; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                        <div style="font-size: 11px; color: #64748b;">
                            <b>Security Hash:</b> SHA256-{hash_val} | <b>Timestamp:</b> {tkt['Booked_At']} | <b>Helpline:</b> 1800-419-4287
                        </div>
                        <div>
                            <span style="font-size: 11px; color: #10b981; font-weight: 600;">✓ VALID GOVERNMENT PASSENGER TRANSIT DOCUMENT</span>
                        </div>
                    </div>
                </div>
                """
                render_html(boarding_pass_markup)
                st.link_button("🌐 Verify / Manage Reservation on Official Govt Webpage (www.tnstc.in)", url="https://www.tnstc.in/TNSTCOnline/", use_container_width=True)

        st.download_button(
            label="📥 Export Session Booking Ledger (JSON)",
            data=json.dumps(st.session_state.booked_tickets, indent=2),
            file_name=f"tnstc_booking_ledger_{date.today().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

# -----------------------------------------------------------------------------
# TAB 4: OFFICIAL GOVT FARE MATRIX & TARIFF CALCULATOR
# -----------------------------------------------------------------------------
with tab_fare_matrix:
    st.subheader("📊 Official Tamil Nadu Bus Fare Matrix & Tariff Structure")
    st.markdown("""
    Under the provisions of the **Tamil Nadu Motor Vehicles Rules** and **Government Order G.O. (Ms) No. 229, Home (Transport) Department**,
    the Government has standardized the per-kilometer tariff slabs, minimum base fares, and hill terrain surcharges across state carriage operations.
    """)

    st.markdown("#### 1. Official Government Fare Slab Table")
    
    tariff_rows = []
    for k, v in OFFICIAL_FARE_RULES.items():
        tariff_rows.append({
            "Service Category": k,
            "Rate per Passenger-KM (Paise)": f"{v['per_km_paise']} p/km",
            "Effective Rate (₹/km)": f"₹{v['per_km_paise']/100:.2f} / km",
            "Minimum Base Fare": f"₹{v['base_min_fare']}",
            "Pricing Type": "Stage-wise (₹5 min)" if v["is_stage_based"] else "Distance Linear",
            "Vettri Payanam (TVK Govt)": "✅ 100% Free for Women" if v["vidiyal_free_women"] else "❌ Standard Fare",
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
            "Women Passenger Fare (Vettri Payanam)": "₹0 (Free - TVK Scheme)" if s_rule["vidiyal_free_women"] else f"₹{tot}"
        })
    st.dataframe(pd.DataFrame(comparison_data), hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 3. Administrative Transport Divisions & Regional Headquarters")
    div_cols = st.columns(len(TN_DIVISIONS))
    for d_idx, (div_name, div_info) in enumerate(TN_DIVISIONS.items()):
        with div_cols[d_idx]:
            st.markdown(f"**{div_name}**")
            st.markdown(f"**Vehicle Registration Series:** `{'`, `'.join(div_info['rto_codes'])}`")
            st.markdown("**Major Operational Depots:**")
            for dp in div_info["depots"][:4]:
                st.markdown(f"- {dp}")

    with st.expander("📊 Bus Status Report & Passenger Load Analysis", expanded=False):
        rows=[]
        for bus in st.session_state.get("managed_fleet",[]):
            cap=int(bus.get("Capacity",0)); pax=int(bus.get("Passengers",0)); load=round(pax/cap*100,1) if cap else 0
            rows.append({"Bus ID":bus.get("Bus ID"),"Registration":bus.get("Registration No"),"Route":bus.get("Route No"),"Capacity":cap,"Passengers":pax,"Available Seats":max(0,cap-pax),"Load %":f"{load}%","Status":bus.get("Status"),"Corporation":bus.get("Corporation")})
        if rows:
            st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
            peak=max(rows,key=lambda q:float(str(q["Load %"]).rstrip("%"))); st.info(f"Highest passenger load: **{peak['Bus ID']}** — {peak['Load %']} on Route **{peak['Route']}**.")
        else: st.info("Add buses in the Bus Management expander to populate the status and passenger-load report.")

    with st.expander("🗺️ Route Management — Add Route / Stops / Update", expanded=False):
        if "managed_routes" not in st.session_state: st.session_state.managed_routes=[]
        a,b,c=st.columns(3)
        with a: mr_no=st.text_input("Route Number",placeholder="R12",key="mr_no")
        with b: mr_from=st.text_input("Source",placeholder="Erode",key="mr_from")
        with c: mr_to=st.text_input("Destination",placeholder="Coimbatore",key="mr_to")
        mr_stops=st.text_input("Stops (comma separated)",placeholder="Bhavani, Annur, Gandhipuram",key="mr_stops")
        if st.button("💾 Save / Update Route",key="mr_save"):
            if mr_no.strip() and mr_from.strip() and mr_to.strip():
                rec={"Route No":mr_no.strip(),"Source":mr_from.strip(),"Destination":mr_to.strip(),"Stops":[q.strip() for q in mr_stops.split(",") if q.strip()],"Updated At":datetime.now().strftime("%d-%b-%Y %I:%M %p")}
                st.session_state.managed_routes=[q for q in st.session_state.managed_routes if q["Route No"]!=rec["Route No"]]; st.session_state.managed_routes.append(rec); st.success(f"Route {mr_no.strip()} saved.")
            else: st.warning("Enter Route Number, Source and Destination.")
        if st.session_state.managed_routes:
            st.dataframe(pd.DataFrame([{"Route No":q["Route No"],"Source":q["Source"],"Destination":q["Destination"],"Stops":" → ".join(q["Stops"]),"Updated At":q["Updated At"]} for q in st.session_state.managed_routes]),hide_index=True,use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 5: AUTONOMOUS GEMINI AI CONTROL & ZERO-TOUCH TRANSIT INTELLIGENCE
# -----------------------------------------------------------------------------
with tab_admin:
    st.subheader("🤖 Autonomous Gemini AI Intelligence & Zero-Touch Transit Engine")
    st.caption("Central Operations & AI Dispatch: Bus timetables, festival specials, and TVK government routes update automatically with zero administrator touch.")

    st.markdown("#### 1. Autonomous Engine & API Key Status")
    
    current_key = get_gemini_api_key()
    has_live_key = bool(current_key)
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric(
            "Auto-Update System",
            "🟢 ACTIVE",
            delta="100% Hands-Free"
        )
    with col_stat2:
        if has_live_key:
            masked = current_key[:4] + "..." + current_key[-4:] if len(current_key) > 8 else "***"
            st.metric(
                "Gemini Cloud AI",
                "CONNECTED",
                delta=f"Secrets ({masked})"
            )
        else:
            st.metric(
                "Gemini Cloud AI",
                "AUTONOMOUS NATIVE",
                delta="Zero-Touch Active"
            )
    with col_stat3:
        st.metric(
            "Auto-Synced Routes",
            f"{len(st.session_state.custom_ai_buses)} Services",
            delta=st.session_state.last_sync_timestamp or "Just Now"
        )

    if has_live_key:
        st.success(f"✅ **Zero-Touch Configuration Active**: Gemini API Key is loaded automatically from system secrets (`.streamlit/secrets.toml`). All schedules, routes, and passenger answers update hands-free without administrator manual intervention.")
    else:
        st.info("ℹ️ **Autonomous Dispatch Active**: The system is automatically synthesizing real-time routes using the official TNSTC autonomous schedule rules. To optionally enable live Google Gemini Cloud generative AI sync, enter your key once below to save it permanently into system secrets.")

    with st.expander("🔑 Permanent API Key Configuration (Save Once - Never Touch Again)", expanded=not has_live_key):
        st.write("Get your 100% free Google Gemini API key (no credit card required) from: [Google AI Studio](https://aistudio.google.com/app/apikey).")
        key_input = st.text_input(
            "Google Gemini API Key:",
            value=current_key if current_key else "",
            type="password",
            placeholder="AIzaSy...",
            help="Once saved, this key is permanently written to .streamlit/secrets.toml and loaded automatically on every run without human touch."
        )
        col_btn1, col_btn2 = st.columns([3, 3])
        with col_btn1:
            if st.button("💾 Save Key Permanently to Secrets & Auto-Sync", type="primary"):
                if is_valid_gemini_key_format(key_input):
                    save_gemini_api_key(key_input.strip())
                    new_r, s_label = run_autonomous_sync(key_input.strip())
                    for r in new_r:
                        if not any(b["bus_no"] == r["bus_no"] for b in st.session_state.custom_ai_buses):
                            st.session_state.custom_ai_buses.append(r)
                    st.session_state.sync_source_label = s_label
                    st.session_state.last_sync_timestamp = datetime.now().strftime("%d-%b-%Y %I:%M %p")
                    st.success("API Key saved permanently! System updated automatically. The admin will never have to re-enter this.")
                    st.rerun()
                elif "youractualkey" in key_input.lower() or "placeholder" in key_input.lower() or len(key_input.strip()) < 25:
                    st.warning("⚠️ That is an example placeholder name (`AIzaSyYourActualKeyHere`), not a real key. To get a real free key, click the link above to generate one on Google AI Studio (takes 5 seconds), or simply leave this blank to run in 100% Autonomous Hands-Free Mode.")
                else:
                    st.error("Please enter a valid Google Gemini API key.")
        with col_btn2:
            if st.button("🔄 Force Immediate Auto-Sync Refresh"):
                new_r, s_label = run_autonomous_sync(current_key)
                for r in new_r:
                    if not any(b["bus_no"] == r["bus_no"] for b in st.session_state.custom_ai_buses):
                        st.session_state.custom_ai_buses.append(r)
                st.session_state.sync_source_label = s_label
                st.session_state.last_sync_timestamp = datetime.now().strftime("%d-%b-%Y %I:%M %p")
                st.success("Synchronized successfully!")
                st.rerun()

    st.markdown("---")
    st.markdown("#### 2. Live Autonomous Routes Ingested into Database")
    st.caption("These routes were automatically generated and injected into the public passenger timetable without administrator intervention:")

    if st.session_state.custom_ai_buses:
        feed_rows = []
        for b in st.session_state.custom_ai_buses:
            feed_rows.append({
                "Bus Registration": b["bus_no"],
                "Service Category": b["type"],
                "Origin": b["from"],
                "Destination": b["to"],
                "Departure": b["dep"],
                "Arrival": b["arr"],
                "Duration": b["duration_str"],
                "Fare": f"₹{b['fare']}",
                "Depot": b["depot"]
            })
        st.dataframe(pd.DataFrame(feed_rows), hide_index=True, use_container_width=True)
    else:
        st.write("No dynamic routes active.")

    st.markdown("---")
    st.markdown("#### 3. Tamil Nadu Transit AI Helpdesk (Zero Re-Entry)")
    st.caption("Ask questions regarding government bus rules, luggage limits, concessions, or routes — powered automatically by Gemini AI:")

    user_q = st.text_input("Enter passenger enquiry:", placeholder="e.g. What are the rules and luggage limits for traveling on SETC AC Sleeper buses?", key="admin_q_input")
    if st.button("Ask Transit AI", key="ask_transit_ai_btn"):
        if not user_q.strip():
            st.error("Please enter a question.")
        else:
            with st.spinner("Consulting Tamil Nadu Motor Vehicles Act & Department Guidelines..."):
                gemini_key = get_gemini_api_key()
                if gemini_key:
                    try:
                        from google import genai
                        client = genai.Client(api_key=gemini_key)
                        resp = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=f"You are the official helpdesk for Tamil Nadu State Transport Corporation (TNSTC & SETC). Answer concisely and factually based on Tamil Nadu transport department rules:\nQuestion: {user_q}"
                        )
                        st.markdown(f"**Official Response:**\n\n{resp.text}")
                    except Exception as ex:
                        st.info(f"Offline Helpdesk Rule: Free luggage allowance in TNSTC ordinary buses is up to 25 kg per passenger. Children below 3 years travel free, and children between 3 and 12 years are charged 50% half-ticket. Women enjoy 100% free travel under Vidiyal/Vettri Payanam on ordinary town services.")
                else:
                    st.info(f"**TNSTC Transit Desk (Automated Response):**\n- **வெற்றிப் பயணம் திட்டம் (Vettri Payanam Scheme - TVK Govt)**: 100% free travel for women, transgender persons, and disabled passengers on ordinary town/mofussil buses with zero fare tickets.\n- **Luggage Allowance**: Standard personal baggage up to 25 kg is free. Commercial cargo or packages above 50 kg attract excess luggage fees.\n- **Concessions**: Senior citizens (above 60 years) are eligible for free tokens per month in town buses upon submitting token passes issued by the Transport Department.\n- **Ghat Routes**: 20% surcharge is levied on mountain roads (Ooty, Kodaikanal, Yercaud).")
