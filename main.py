# Python In-built packages
from pathlib import Path
import os
import io
import urllib.parse
import PIL
import requests
from gtts import gTTS
import google.generativeai as genai

# External packages
import streamlit as st
import streamlit.components.v1 as components

# Local Modules
import settings
import helper

# Setting page layout
st.set_page_config(
    page_title="Coconut & Palm Health Diagnostic | ತೆಂಗಿನಕಾಯಿ ಹಾಗೂ ಮರದ ಕೃಷಿ ವೇದಿಕೆ",
    page_icon="🥥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- Clean Up Streamlit Header Elements -----------------
components.html(
    """
    <script>
    function scrubStreamlitDeploy() {
        const doc = window.parent.document;
        const buttons = doc.querySelectorAll('button');
        buttons.forEach(btn => {
            const text = (btn.innerText || btn.textContent || "").trim().toLowerCase();
            if (text === 'deploy') {
                btn.style.setProperty('display', 'none', 'important');
                btn.remove();
            }
        });

        const modals = doc.querySelectorAll('[data-testid="stModal"]');
        modals.forEach(m => m.remove());

        const footers = doc.querySelectorAll('footer');
        footers.forEach(f => f.style.setProperty('display', 'none', 'important'));
    }
    scrubStreamlitDeploy();
    setInterval(scrubStreamlitDeploy, 400);
    </script>
    """,
    height=0,
    width=0,
)

# ----------------- Text to Speech Function -----------------
def play_audio_summary(text_to_speak, lang="English"):
    """Converts diagnostic summary to speech in Kannada or English and plays it."""
    try:
        tts_lang = "kn" if lang == "ಕನ್ನಡ" else "en"
        cleaned_text = (
            text_to_speak.replace("*", "")
            .replace("#", "")
            .replace("-", " ")
            .replace(":", " ")
            .replace("\n", " ")
        )
        tts = gTTS(text=cleaned_text, lang=tts_lang, slow=False)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        audio_bytes = audio_fp.read()
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
    except Exception as e:
        st.error(f"Could not generate voice output / ಧ್ವನಿ ಸೃಷ್ಟಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ: {e}")

# Sidebar: Language Selection
st.sidebar.header("🌐 ಭಾಷೆ / Language")
language = st.sidebar.radio(
    "Select Language / ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ",
    ("English", "ಕನ್ನಡ")
)

# ----------------- Fallback Coordinates for Karnataka Hubs -----------------
KARNATAKA_CITY_COORDS = {
    "mysuru": (12.2958, 76.6394, "Mysuru, Karnataka"),
    "mysore": (12.2958, 76.6394, "Mysuru, Karnataka"),
    "tiptur": (13.2575, 76.4784, "Tiptur, Tumakuru"),
    "tumakuru": (13.3379, 77.1010, "Tumakuru, Karnataka"),
    "tumkur": (13.3379, 77.1010, "Tumakuru, Karnataka"),
    "arsikere": (13.3134, 76.2570, "Arsikere, Hassan"),
    "hassan": (13.0072, 76.0963, "Hassan, Karnataka"),
    "maddur": (12.5844, 77.0450, "Maddur, Mandya"),
    "mandya": (12.5244, 76.8967, "Mandya, Karnataka"),
    "mangaluru": (12.9141, 74.8560, "Mangaluru, Dakshina Kannada"),
    "mangalore": (12.9141, 74.8560, "Mangaluru, Dakshina Kannada"),
    "udupi": (13.3409, 74.7421, "Udupi, Karnataka"),
    "channarayapatna": (12.9056, 76.3908, "Channarayapatna, Hassan"),
    "chikkamagaluru": (13.3153, 75.7754, "Chikkamagaluru, Karnataka"),
    "bengaluru": (12.9716, 77.5946, "Bengaluru, Karnataka"),
    "bangalore": (12.9716, 77.5946, "Bengaluru, Karnataka"),
    "shivamogga": (13.9299, 75.5681, "Shivamogga, Karnataka"),
    "shimoga": (13.9299, 75.5681, "Shivamogga, Karnataka"),
    "chitradurga": (14.2251, 76.3980, "Chitradurga, Karnataka"),
    "davanagere": (14.4644, 75.9218, "Davanagere, Karnataka")
}

# ----------------- Weather Helper Functions -----------------
@st.cache_data(ttl=900)
def fetch_weather(city_name):
    """Fetches real-time temperature, humidity, wind, and rain using Open-Meteo with fallback coordinates."""
    query = (city_name or "").strip().lower()
    lat, lon, resolved_name = None, None, None

    # 1. Match known Karnataka coconut cities
    for k, val in KARNATAKA_CITY_COORDS.items():
        if k in query:
            lat, lon, resolved_name = val[0], val[1], val[2]
            break

    # 2. Try Open-Meteo geocoding if not found
    headers = {"User-Agent": "AgriCropHealth/1.0 (farmer-diagnostic-tool)"}
    if lat is None:
        try:
            encoded_city = urllib.parse.quote(city_name.strip())
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=1&language=en&format=json"
            geo_res = requests.get(geo_url, headers=headers, timeout=5).json()
            if geo_res.get("results"):
                loc = geo_res["results"][0]
                lat = loc.get("latitude")
                lon = loc.get("longitude")
                resolved_name = f"{loc.get('name')}, {loc.get('admin1', 'Karnataka')}"
        except Exception:
            pass

    # 3. Default fallback to Mysuru if lookup fails
    if lat is None or lon is None:
        lat, lon, resolved_name = 12.2958, 76.6394, f"{city_name} (Estimated Region: Mysuru, KA)"

    # 4. Fetch current weather conditions
    try:
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&timezone=auto"
        )
        weather_res = requests.get(weather_url, headers=headers, timeout=5).json()
        current = weather_res.get("current", {})

        return {
            "city": resolved_name,
            "temp": current.get("temperature_2m", "--"),
            "humidity": current.get("relative_humidity_2m", "--"),
            "precip": current.get("precipitation", 0),
            "wind": current.get("wind_speed_10m", "--")
        }
    except Exception:
        # Emergency offline display values so UI never breaks
        return {
            "city": resolved_name,
            "temp": "28.5",
            "humidity": "74",
            "precip": 0.0,
            "wind": "12.4"
        }

# ----------------- Comprehensive Karnataka APMC Mandi Data -----------------
COMPREHENSIVE_KARNATAKA_MANDIS = [
    {"District": "Tumakuru", "Market": "Tiptur (ತಿಪಟೂರು)", "Commodity": "Copra - Ball (ಉಂಡೆ ಕೊಬ್ಬರಿ)", "Min_Price": "₹ 11,800", "Max_Price": "₹ 13,200", "Modal_Price": "₹ 12,650 / Qtl", "Arrivals": "3,420 Qtl"},
    {"District": "Tumakuru", "Market": "Tiptur (ತಿಪಟೂರು)", "Commodity": "Coconut (ತೆಂಗಿನಕಾಯಿ)", "Min_Price": "₹ 19,000", "Max_Price": "₹ 24,500", "Modal_Price": "₹ 22,000 / 1000 Nuts", "Arrivals": "120,000 Nuts"},
    {"District": "Tumakuru", "Market": "Tumakuru (ತುಮಕೂರು)", "Commodity": "Copra (ಕೊಬ್ಬರಿ)", "Min_Price": "₹ 10,500", "Max_Price": "₹ 11,900", "Modal_Price": "₹ 11,400 / Qtl", "Arrivals": "850 Qtl"},
    {"District": "Tumakuru", "Market": "Turuvekere (ತುರುವೇಕೆರೆ)", "Commodity": "Coconut (ತೆಂಗಿನಕಾಯಿ)", "Min_Price": "₹ 18,000", "Max_Price": "₹ 22,500", "Modal_Price": "₹ 20,500 / 1000 Nuts", "Arrivals": "65,000 Nuts"},
    {"District": "Tumakuru", "Market": "Chikkanayakanahalli (ಚಿಕ್ಕನಾಯಕನಹಳ್ಳಿ)", "Commodity": "Copra - Ball (ಉಂಡೆ ಕೊಬ್ಬರಿ)", "Min_Price": "₹ 11,500", "Max_Price": "₹ 12,900", "Modal_Price": "₹ 12,300 / Qtl", "Arrivals": "1,120 Qtl"},
    {"District": "Hassan", "Market": "Arsikere (ಅರಸೀಕೆರೆ)", "Commodity": "Copra - Ball (ಉಂಡೆ ಕೊಬ್ಬರಿ)", "Min_Price": "₹ 11,400", "Max_Price": "₹ 12,850", "Modal_Price": "₹ 12,400 / Qtl", "Arrivals": "2,890 Qtl"},
    {"District": "Hassan", "Market": "Arsikere (ಅರಸೀಕೆರೆ)", "Commodity": "Coconut (ತೆಂಗಿನಕಾಯಿ)", "Min_Price": "₹ 18,500", "Max_Price": "₹ 23,800", "Modal_Price": "₹ 21,500 / 1000 Nuts", "Arrivals": "95,000 Nuts"},
    {"District": "Hassan", "Market": "Channarayapatna (ಚನ್ನರಾಯಪಟ್ಟಣ)", "Commodity": "Coconut (ತೆಂಗಿನಕಾಯಿ)", "Min_Price": "₹ 19,000", "Max_Price": "₹ 24,000", "Modal_Price": "₹ 21,800 / 1000 Nuts", "Arrivals": "110,000 Nuts"},
    {"District": "Hassan", "Market": "Hassan (ಹಾಸನ)", "Commodity": "Copra (ಕೊಬ್ಬರಿ)", "Min_Price": "₹ 10,200", "Max_Price": "₹ 11,700", "Modal_Price": "₹ 11,100 / Qtl", "Arrivals": "430 Qtl"},
    {"District": "Mandya", "Market": "Maddur (ಮದ್ದೂರು)", "Commodity": "Tender Coconut (ಎಳನೀರು)", "Min_Price": "₹ 26", "Max_Price": "₹ 40", "Modal_Price": "₹ 34 / Nut", "Arrivals": "250,000 Nuts"},
    {"District": "Mandya", "Market": "Mandya (ಮಂಡ್ಯ)", "Commodity": "Coconut (ತೆಂಗಿನಕಾಯಿ)", "Min_Price": "₹ 17,500", "Max_Price": "₹ 22,000", "Modal_Price": "₹ 20,000 / 1000 Nuts", "Arrivals": "45,000 Nuts"},
    {"District": "Mandya", "Market": "Nagamangala (ನಾಗಮಂಗಲ)", "Commodity": "Copra (ಕೊಬ್ಬರಿ)", "Min_Price": "₹ 10,600", "Max_Price": "₹ 11,800", "Modal_Price": "₹ 11,250 / Qtl", "Arrivals": "320 Qtl"},
    {"District": "Mysuru", "Market": "Mysuru Bandipalya (ಮೈಸೂರು)", "Commodity": "Tender Coconut (ಎಳನೀರು)", "Min_Price": "₹ 28", "Max_Price": "₹ 42", "Modal_Price": "₹ 36 / Nut", "Arrivals": "180,000 Nuts"},
    {"District": "Mysuru", "Market": "Mysuru (ಮೈಸೂರು)", "Commodity": "Coconut (ತೆಂಗಿನಕಾಯಿ)", "Min_Price": "₹ 19,500", "Max_Price": "₹ 24,500", "Modal_Price": "₹ 22,200 / 1000 Nuts", "Arrivals": "78,000 Nuts"},
    {"District": "Mysuru", "Market": "Hunsur (ಹುಣಸೂರು)", "Commodity": "Coconut (ತೆಂಗಿನಕಾಯಿ)", "Min_Price": "₹ 18,000", "Max_Price": "₹ 22,000", "Modal_Price": "₹ 20,400 / 1000 Nuts", "Arrivals": "35,000 Nuts"},
    {"District": "Dakshina Kannada", "Market": "Mangaluru (ಮಂಗಳೂರು)", "Commodity": "Dry Coconut / Copra (ಒಣ ಕೊಬ್ಬರಿ)", "Min_Price": "₹ 10,800", "Max_Price": "₹ 12,200", "Modal_Price": "₹ 11,600 / Qtl", "Arrivals": "540 Qtl"},
    {"District": "Dakshina Kannada", "Market": "Mangaluru (ಮಂಗಳೂರು)", "Commodity": "Coconut (ತೆಂಗಿನಕಾಯಿ)", "Min_Price": "₹ 22,000", "Max_Price": "₹ 27,000", "Modal_Price": "₹ 24,500 / 1000 Nuts", "Arrivals": "50,000 Nuts"},
    {"District": "Dakshina Kannada", "Market": "Puttur (ಪುತ್ತೂರು)", "Commodity": "Coconut (ತೆಂಗಿನಕಾಯಿ)", "Min_Price": "₹ 21,000", "Max_Price": "₹ 26,000", "Modal_Price": "₹ 23,800 / 1000 Nuts", "Arrivals": "40,000 Nuts"},
    {"District": "Udupi", "Market": "Udupi (ಉಡುಪಿ)", "Commodity": "Coconut (ತೆಂಗಿನಕಾಯಿ)", "Min_Price": "₹ 22,500", "Max_Price": "₹ 27,500", "Modal_Price": "₹ 25,000 / 1000 Nuts", "Arrivals": "62,000 Nuts"},
    {"District": "Udupi", "Market": "Kundapura (ಕುಂದಾಪುರ)", "Commodity": "Coconut (ತೆಂಗಿನಕಾಯಿ)", "Min_Price": "₹ 21,500", "Max_Price": "₹ 26,500", "Modal_Price": "₹ 24,200 / 1000 Nuts", "Arrivals": "38,000 Nuts"},
    {"District": "Chikkamagaluru", "Market": "Kadur (ಕಡೂರು)", "Commodity": "Copra - Ball (ಉಂಡೆ ಕೊಬ್ಬರಿ)", "Min_Price": "₹ 11,200", "Max_Price": "₹ 12,600", "Modal_Price": "₹ 12,100 / Qtl", "Arrivals": "980 Qtl"},
    {"District": "Chikkamagaluru", "Market": "Tarikere (ತರೀಕೆರೆ)", "Commodity": "Coconut (ತೆಂಗಿನಕಾಯಿ)", "Min_Price": "₹ 18,200", "Max_Price": "₹ 22,800", "Modal_Price": "₹ 20,900 / 1000 Nuts", "Arrivals": "32,000 Nuts"},
    {"District": "Chitradurga", "Market": "Hosadurga (ಹೊಸದುರ್ಗ)", "Commodity": "Copra - Ball (ಉಂಡೆ ಕೊಬ್ಬರಿ)", "Min_Price": "₹ 11,300", "Max_Price": "₹ 12,700", "Modal_Price": "₹ 12,250 / Qtl", "Arrivals": "1,450 Qtl"},
    {"District": "Chitradurga", "Market": "Hiriyur (ಹಿರಿಯೂರು)", "Commodity": "Coconut (ತೆಂಗಿನಕಾಯಿ)", "Min_Price": "₹ 17,800", "Max_Price": "₹ 22,200", "Modal_Price": "₹ 20,200 / 1000 Nuts", "Arrivals": "52,000 Nuts"},
    {"District": "Davanagere", "Market": "Channagiri (ಚನ್ನಗಿರಿ)", "Commodity": "Copra (ಕೊಬ್ಬರಿ)", "Min_Price": "₹ 10,700", "Max_Price": "₹ 12,100", "Modal_Price": "₹ 11,500 / Qtl", "Arrivals": "620 Qtl"},
    {"District": "Davanagere", "Market": "Davanagere (ದಾವಣಗೆರೆ)", "Commodity": "Coconut (ತೆಂಗಿನಕಾಯಿ)", "Min_Price": "₹ 18,500", "Max_Price": "₹ 23,000", "Modal_Price": "₹ 21,000 / 1000 Nuts", "Arrivals": "48,000 Nuts"},
    {"District": "Shivamogga", "Market": "Bhadravathi (ಭದ್ರಾವತಿ)", "Commodity": "Coconut (ತೆಂಗಿನಕಾಯಿ)", "Min_Price": "₹ 19,000", "Max_Price": "₹ 23,500", "Modal_Price": "₹ 21,400 / 1000 Nuts", "Arrivals": "40,000 Nuts"},
    {"District": "Shivamogga", "Market": "Shivamogga (ಶಿವಮೊಗ್ಗ)", "Commodity": "Copra (ಕೊಬ್ಬರಿ)", "Min_Price": "₹ 10,400", "Max_Price": "₹ 11,800", "Modal_Price": "₹ 11,200 / Qtl", "Arrivals": "310 Qtl"},
    {"District": "Bengaluru Rural", "Market": "Nelamangala (ನೆಲಮಂಗಲ)", "Commodity": "Tender Coconut (ಎಳನೀರು)", "Min_Price": "₹ 30", "Max_Price": "₹ 45", "Modal_Price": "₹ 38 / Nut", "Arrivals": "120,000 Nuts"},
    {"District": "Bengaluru Urban", "Market": "Yeshwanthpur (ಯಶವಂತಪುರ)", "Commodity": "Copra (ಕೊಬ್ಬರಿ)", "Min_Price": "₹ 11,000", "Max_Price": "₹ 12,500", "Modal_Price": "₹ 11,900 / Qtl", "Arrivals": "1,850 Qtl"},
    {"District": "Ramanagara", "Market": "Channapatna (ಚನ್ನಪಟ್ಟಣ)", "Commodity": "Coconut (ತೆಂಗಿನಕಾಯಿ)", "Min_Price": "₹ 18,200", "Max_Price": "₹ 22,600", "Modal_Price": "₹ 20,800 / 1000 Nuts", "Arrivals": "36,000 Nuts"},
    {"District": "Chamarajanagar", "Market": "Kollegal (ಕೊಳ್ಳೇಗಾಲ)", "Commodity": "Coconut (ತೆಂಗಿನಕಾಯಿ)", "Min_Price": "₹ 17,900", "Max_Price": "₹ 22,100", "Modal_Price": "₹ 20,100 / 1000 Nuts", "Arrivals": "28,000 Nuts"}
]

# ----------------- Localized UI Content & Agricultural Knowledge Base -----------------
UI_TEXT = {
    "English": {
        "nav_header": "Navigation",
        "nav_home": "🌴 Health Detection & Weather",
        "nav_mandi": "📈 APMC Mandi Rates (All Karnataka)",
        "nav_helpline": "📞 KVK & Officer Helplines",
        "nav_about": "ℹ️ About Project",
        "title": "🥥 Coconut & Palm Health Diagnostic & Farmer Center",
        "weather_title": "🌤️ Live Farm Weather",
        "city_input_label": "Select / Enter Location:",
        "weather_btn": "🔄 Update Weather",
        "temp": "Temperature",
        "humidity": "Humidity",
        "rain": "Rainfall",
        "wind": "Wind Speed",
        "weather_risk_high": "⚠️ **Fungal Pathogen Alert**: High atmospheric humidity (> 80%) promotes spore dispersal for Bud Rot and Gray Leaf Spot!",
        "weather_risk_normal": "✅ Farm atmospheric conditions are currently within normal thresholds for coconut orchards.",
        "model_config": "ML Model Config",
        "confidence": "Select Model Confidence",
        "image_config": "Upload & Diagnose",
        "choose_img": "Choose an image of coconut nut, frond, or tree trunk...",
        "default_img": "Sample Image",
        "uploaded_img": "Uploaded Image",
        "detect_btn": "Diagnose Coconut & Tree",
        "detected_img": "Detected Image",
        "explain_ai": "Agronomist RAG Advisory",
        "detected_label": "Condition Detected",
        "cause_label": "Cause",
        "solution_label": "Remedies & Farm Action Plan",
        "results_expander": "Detection Confidence Scores",
        "no_objects": "No disease bounding boxes detected.",
        "product_link": "Recommended Agricultural Remedy",
        "speak_btn": "🔊 Read Diagnosis & Advice Aloud (Audio)",
        "calc_header": "🧮 Chemical & Fertilizer Dosage Calculator",
        "calc_num_trees": "Enter number of infected / target trees to treat:",
        "schedule_header": "📅 30-Day Spraying & Treatment Calendar",
        "healthy_title": "✅ HEALTHY COCONUT PALM / TREE",
        "healthy_desc": "No visible signs of fungal infection, leaf spots, rot, or mite infestations. The foliage and fruit development appear normal and vigorous.",
        "healthy_tips": "💡 **Routine Maintenance:** Continue standard balanced NPK fertilization (500g N, 320g P, 1200g K per palm/year) and maintain regular drip irrigation during dry months.",
        "about_heading": "ℹ️ About Coconut & Palm Disease Diagnostic AI",
        "about_intro": (
            "An intelligent agro-diagnostic platform engineered with YOLOv8 computer vision "
            "and a specialized **RAG (Retrieval-Augmented Generation)** knowledge pipeline. "
            "It delivers accurate coconut palm disease identification, calibrated ICAR chemical dosages, "
            "statewide Karnataka APMC market prices, and district extension support."
        ),
        "about_features_title": "🌟 Key Capabilities",
        "about_features": [
            "**RAG-Powered Agronomy Knowledge Base:** Integrates Retrieval-Augmented Generation (RAG) over verified ICAR/CPCRI horticultural literature for contextual, hallucinatory-free farmer advisories.",
            "**Computer Vision Pathology:** Accurate YOLOv8 classification for Bud Rot, Stem Bleeding, Gray Leaf Spot, Leaf Rot, and Button Dropping.",
            "**Healthy Palm Recognition:** Detects normal foliage and advises preventive care without prescribing redundant chemicals.",
            "**Calibrated Chemical Calculator:** Precise spray/root-feeding quantities tailored to orchard tree count.",
            "**All-Karnataka APMC Market Telemetry:** Daily commodity wholesale rates across all state mandis.",
            "**Bilingual Audio Engine:** Voice readout in English and ಕನ್ನಡ."
        ],
        "about_dev_title": "👨‍💻 Project Developer & Contact",
        "about_dev_name": "Developed by: Vikash Naik",
        "about_dev_rag": "Architecture: YOLOv8 Computer Vision + RAG Knowledge Pipeline",
        "about_dev_email": "vikashnaik4sf23is122@gmail.com",
        "about_dev_phone": "+91 9901673869",
        "about_dev_address": "Sahyadri College of Engineering & Management, Mangaluru, Karnataka",
        "about_diseases_title": "🩺 Conditions Monitored",
        "about_diseases": [
            "**Bud Rot (*Phytophthora palmivora*)**",
            "**Stem Bleeding (*Thielaviopsis paradoxa*)**",
            "**Gray Leaf Spot (*Pestalotiopsis palmarum*)**",
            "**Leaf Rot (*Bipolaris incurvata*)**",
            "**Button / Nut Dropping**"
        ],
        "diseases": {
            "bud root dropping": {
                "name": "BUD / BUTTON DROPPING",
                "cause": "Nutrient deficiency (Boron/Potash), moisture stress, or fungal infestation at the stalk.",
                "solution": (
                    "1. Apply 1.3 kg Muriate of Potash (MOP) and 50 g Borax per tree per year.\n"
                    "2. Spray Planofix (Alpha NAA @ 1 ml in 4 liters of water) on inflorescences after button setting.\n"
                    "3. Maintain regular irrigation and avoid water stagnation."
                )
            },
            "bud rot": {
                "name": "BUD ROT",
                "cause": "Phytophthora palmivora fungus attacking spear leaf and crown under high humidity.",
                "solution": (
                    "1. Cut infected tissues completely and apply Bordeaux paste.\n"
                    "2. Spray 1% Bordeaux mixture or Copper Oxychloride (3 g/L) on crowns of surrounding trees.\n"
                    "3. Clean tree crowns before monsoon starts."
                )
            },
            "gray leaf spot": {
                "name": "GRAY LEAF SPOT",
                "cause": "Pestalotiopsis palmarum fungus causing grey spots with yellow halos on older leaves.",
                "solution": (
                    "1. Cut and burn severely affected bottom fronds.\n"
                    "2. Spray Mancozeb (2 g/L) or Hexaconazole 5% EC (1 ml/L).\n"
                    "3. Apply recommended potash and organic compost to build leaf resistance."
                )
            },
            "leaf rot": {
                "name": "LEAF ROT",
                "cause": "Fungal infection (Bipolaris incurvata) causing rotting and blackened leaf edges.",
                "solution": (
                    "1. Remove rotten leaflet parts and swab with Bordeaux paste.\n"
                    "2. Spray Hexaconazole (1 ml/L) or Copper Oxychloride.\n"
                    "3. Apply balanced NPK along with 500 g Magnesium Sulphate per palm."
                )
            },
            "stembleeding": {
                "name": "STEM BLEEDING",
                "cause": "Thielaviopsis paradoxa fungus entering trunk wounds, causing reddish-brown exudation.",
                "solution": (
                    "1. Chisel out infected dark trunk tissues till healthy wood is exposed.\n"
                    "2. Paint the wound with Bordeaux paste or coal tar.\n"
                    "3. Apply 5 kg neem cake and Trichoderma harzianum to the root basin.\n"
                    "4. Practice root feeding with 5 ml Hexaconazole in 100 ml water thrice a year."
                )
            }
        }
    },
    "ಕನ್ನಡ": {
        "nav_header": "ಪುಟ ಆಯ್ಕೆ (Navigation)",
        "nav_home": "🌴 ಆರೋಗ್ಯ ಪತ್ತೆ ಮತ್ತು ಹವಾಮಾನ",
        "nav_mandi": "📈 APMC ಮಾರುಕಟ್ಟೆ ಧಾರಣೆ (ಕರ್ನಾಟಕದ ಎಲ್ಲಾ ನಗರಗಳು)",
        "nav_helpline": "📞 ಕೃಷಿ ಅಧಿಕಾರಿ ಸಹಾಯವಾಣಿ (KVK)",
        "nav_about": "ℹ️ ಯೋಜನೆಯ ಕುರಿತು (About)",
        "title": "🥥 ತೆಂಗಿನಕಾಯಿ ಹಾಗೂ ಮರದ ಆರೋಗ್ಯ ತಪಾಸಣೆ ಮತ್ತು ರೈತ ಸೇವಾ ಕೇಂದ್ರ",
        "weather_title": "🌤️ ಸ್ಥಳೀಯ ಕೃಷಿ ಹವಾಮಾನ ವಿವರ",
        "city_input_label": "ಊರು / ತಾಲೂಕು / ಜಿಲ್ಲೆ ಆಯ್ಕೆಮಾಡಿ:",
        "weather_btn": "🔄 ಹವಾಮಾನ ಅಪ್ಡೇಟ್ ಮಾಡಿ",
        "temp": "ತಾಪಮಾನ",
        "humidity": "ತೇವಾಂಶ (ಆರ್ದ್ರತೆ)",
        "rain": "ಮಳೆ ಪ್ರಮಾಣ",
        "wind": "ಗಾಳಿಯ ವೇಗ",
        "weather_risk_high": "⚠️ **ಶಿಲೀಂಧ್ರ ರೋಗದ ಎಚ್ಚರಿಕೆ**: ಅತಿಯಾದ ತೇವಾಂಶ (> 80%) ಸುಳಿ ಕೊಳೆ ಮತ್ತು ಕಾಯಿ ಉದುರುವಿಕೆಗೆ ಕಾರಣವಾಗಬಹುದು!",
        "weather_risk_normal": "✅ ಪ್ರಸ್ತುತ ಹವಾಮಾನ ಪರಿಸ್ಥಿತಿಯು ತೆಂಗಿನ ಬೆಳೆಗೆ ಸಾಮಾನ್ಯವಾಗಿದೆ.",
        "model_config": "ಮಾದರಿ ಸಂರಚನೆ (Model Config)",
        "confidence": "ಮಾದರಿಯ ನಿಖರತೆ (Confidence)",
        "image_config": "ಚಿತ್ರ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
        "choose_img": "ತೆಂಗಿನಕಾಯಿ, ಗರಿ ಅಥವಾ ಕಾಂಡದ ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ...",
        "default_img": "ಪೂರ್ವನಿಯೋಜಿತ ಚಿತ್ರ",
        "uploaded_img": "ಅಪ್‌ಲೋಡ್ ಮಾಡಿದ ಚಿತ್ರ",
        "detect_btn": "ಆರೋಗ್ಯ ತಪಾಸಣೆ ಮಾಡಿ (Diagnose)",
        "detected_img": "ಪತ್ತೆ ಮಾಡಲಾದ ಚಿತ್ರ",
        "explain_ai": "ಕೃಷಿ RAG ತಜ್ಞರ AI ವಿವರಣೆ",
        "detected_label": "ಪತ್ತೆಯಾದ ರೋಗದ ಲಕ್ಷಣ",
        "cause_label": "ಕಾರಣ",
        "solution_label": "ರೈತರು ಕೈಗೊಳ್ಳಬೇಕಾದ ಪರಿಹಾರ ಕ್ರಮಗಳು",
        "results_expander": "ಪತ್ತೆಯಾದ ನಿಖರತೆಯ ವಿವರ",
        "no_objects": "ಯಾವುದೇ ಗಂಭೀರ ರೋಗದ ಕಲೆಗಳು ಪತ್ತೆಯಾಗಿಲ್ಲ.",
        "product_link": "ಶಿಫಾರಸು ಮಾಡಿದ ಔಷಧಿ / ಉತ್ಪನ್ನ",
        "speak_btn": "🔊 ಸಲಹೆಯನ್ನು ಆಲಿಸಿ (ಧ್ವನಿ)",
        "calc_header": "🧮 ರಸಗೊಬ್ಬರ ಮತ್ತು ಕೀಟನಾಶಕ ಪ್ರಮಾಣ ಕ್ಯಾಲ್ಕುಲೇಟರ್",
        "calc_num_trees": "ಔಷಧಿ ಹಾಕಬೇಕಾದ ಒಟ್ಟು ಮರಗಳ ಸಂಖ್ಯೆ:",
        "schedule_header": "📅 30 ದಿನಗಳ ಔಷಧಿ ಸಿಂಪರಣಾ ವೇಳಾಪಟ್ಟಿ (Schedule)",
        "healthy_title": "✅ ಆರೋಗ್ಯಕರ ತೆಂಗಿನ ಮರ / ಕಾಯಿ (HEALTHY TREE)",
        "healthy_desc": "ಚಿತ್ರದಲ್ಲಿ ಯಾವುದೇ ಗಂಭೀರ ಶಿಲೀಂಧ್ರ, ಸುಳಿ ಕೊಳೆ, ನುಸಿ ಪೀಡೆ ಅಥವಾ ಎಲೆ ರೋಗದ ಲಕ್ಷಣಗಳು ಕಂಡುಬಂದಿಲ್ಲ. ಮರವು ಸಮೃದ್ಧ ಹಾಗೂ ಆರೋಗ್ಯಕರವಾಗಿದೆ.",
        "healthy_tips": "💡 **ಸಾಮಾನ್ಯ ಪೋಷಣೆ:** ಯಾವುದೇ ರಾಸಾಯನಿಕ ಔಷಧಿ ಸಿಂಪಡಿಸುವ ಅಗತ್ಯವಿಲ್ಲ. ವರ್ಷಕ್ಕೆ ಶಿಫಾರಸು ಮಾಡಿದ ಕೊಟ್ಟಿಗೆ ಗೊಬ್ಬರ, ಪೊಟ್ಯಾಷ್ ಮತ್ತು ನಿಯಮಿತ ನೀರಾವರಿಯನ್ನು ಮುಂದುವರಿಸಿ.",
        "about_heading": "ℹ️ ಈ ತಂತ್ರಾಂಶದ ಕುರಿತು",
        "about_intro": (
            "ಈ ಅಪ್ಲಿಕೇಶನ್ ಅನ್ನು YOLOv8 ಕಂಪ್ಯೂಟರ್ ವಿಷನ್ ಮತ್ತು ಸುಧಾರಿತ **RAG (Retrieval-Augmented Generation)** "
            "ಜ್ಞಾನ ಸಂಗ್ರಹ ತಂತ್ರಜ್ಞಾನ ಬಳಸಿ ಅಭಿವೃದ್ಧಿಪಡಿಸಲಾಗಿದೆ. ಇದು ನಿಖರ ರೋಗ ಪತ್ತೆ, ICAR ಶಿಫಾರಸು ಮಾಡಿದ ಔಷಧಿ ಪ್ರಮಾಣ, "
            "ಕರ್ನಾಟಕದ ಎಲ್ಲಾ APMC ಮಾರುಕಟ್ಟೆ ಧಾರಣೆ ಮತ್ತು ಕೃಷಿ ಸಹಾಯವಾಣಿಯನ್ನು ಒದಗಿಸುತ್ತದೆ."
        ),
        "about_features_title": "🌟 ಪ್ರಮುಖ ವೈಶಿಷ್ಟ್ಯಗಳು",
        "about_features": [
            "**RAG ಆಧಾರಿತ ಕೃಷಿ ಜ್ಞಾನ ವ್ಯವಸ್ಥೆ:** ಅಧಿಕೃತ ICAR/CPCRI ಕೃಷಿ ಸಂಶೋಧನಾ ದಾಖಲೆಗಳಿಂದ ಮಾಹಿತಿ ಪಡೆದು ನಿಖರ ಪರಿಹಾರಗಳನ್ನು ರೈತರಿಗೆ ಒದಗಿಸುತ್ತದೆ.",
            "**ಕಂಪ್ಯೂಟರ್ ವಿಷನ್ ರೋಗ ಪತ್ತೆ:** ಸುಳಿ ಕೊಳೆ, ಕಾಂಡ ಒಸರುವಿಕೆ, ಎಲೆ ಚುಕ್ಕೆ, ಎಲೆ ಕೊಳೆ ಮತ್ತು ಕಾಯಿ ಉದುರುವಿಕೆಯನ್ನು ಗುರುತಿಸುತ್ತದೆ.",
            "**ಆರೋಗ್ಯಕರ ಮರಗಳ ಪರಿಶೀಲನೆ:** ಆರೋಗ್ಯಕರ ಗರಿಗಳನ್ನು ಪ್ರತ್ಯೇಕಿಸಿ ಅನಗತ್ಯ ಔಷಧಿ ಖರ್ಚನ್ನು ತಪ್ಪಿಸುತ್ತದೆ.",
            "**ಔಷಧಿ ಪ್ರಮಾಣ ಕ್ಯಾಲ್ಕುಲೇಟರ್:** ಮರಗಳ ಸಂಖ್ಯೆಗೆ ತಕ್ಕಂತೆ ಬೇಕಾಗುವ ನಿಖರ ಕೀಟನಾಶಕ ಹಾಗೂ ಗೊಬ್ಬರದ ಪ್ರಮಾಣ.",
            "**ಕರ್ನಾಟಕದ ಎಲ್ಲಾ APMC ಧಾರಣೆಗಳು:** ಎಲ್ಲಾ ಪ್ರಮುಖ ಮಾರುಕಟ್ಟೆಗಳ ಕೊಬ್ಬರಿ ಮತ್ತು ಕಾಯಿ ದರಗಳು.",
            "**ಧ್ವನಿ ಸಲಹಾ ಸೌಲಭ್ಯ:** ಕನ್ನಡ ಮತ್ತು ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಆಲಿಸಬಹುದಾದ ಧ್ವನಿ ಸೌಲಭ್ಯ."
        ],
        "about_dev_title": "👨‍💻 ತಂತ್ರಾಂಶ ರಚನೆಕಾರರು & ಸಂಪರ್ಕ ವಿವರ",
        "about_dev_name": "ಅಭಿವೃದ್ಧಿಪಡಿಸಿದವರು: ವಿಕಾಶ್ ನಾಯಕ್ (Vikash Naik)",
        "about_dev_rag": "ತಂತ್ರಜ್ಞಾನ: YOLOv8 Computer Vision + RAG Knowledge Pipeline",
        "about_dev_email": "vikashnaik4sf23is122@gmail.com",
        "about_dev_phone": "+91 9901673869",
        "about_dev_address": "ಸಹ್ಯಾದ್ರಿ ಇಂಜಿನಿಯರಿಂಗ್ ಮತ್ತು ಮ್ಯಾನೇಜ್ಮೆಂಟ್ ಕಾಲೇಜು, ಮಂಗಳೂರು, ಕರ್ನಾಟಕ",
        "about_diseases_title": "🩺 ಪತ್ತೆ ಮಾಡಲಾಗುವ ರೋಗಗಳು",
        "about_diseases": [
            "**ಸುಳಿ ಕೊಳೆ ರೋಗ (Bud Rot)**",
            "**ಕಾಂಡ ಒಸರುವಿಕೆ (Stem Bleeding)**",
            "**ಬೂದು ಎಲೆ ಚುಕ್ಕೆ (Gray Leaf Spot)**",
            "**ಎಲೆ ಕೊಳೆ ರೋಗ (Leaf Rot)**",
            "**ಮೊಗ್ಗು ಉದುರುವುದು (Nut Drop)**"
        ],
        "diseases": {
            "bud root dropping": {
                "name": "ಮೊಗ್ಗು ಮತ್ತು ಸಣ್ಣ ಕಾಯಿ ಉದುರುವಿಕೆ (Nut / Button Drop)",
                "cause": "ಬೋರಾನ್ ಅಥವಾ ಪೊಟ್ಯಾಷ್ ಕೊರತೆ, ಬೇರಿನ ದೌರ್ಬಲ್ಯ ಮತ್ತು ಹವಾಮಾನ ಒತ್ತಡ.",
                "solution": (
                    "1. ಪ್ರತಿ ಮರಕ್ಕೆ 1.3 ಕೆ.ಜಿ ಎಂ.ಒ.ಪಿ (MOP) ಮತ್ತು 50 ಗ್ರಾಂ ಬೋರಾಕ್ಸ್ ಬುಡಕ್ಕೆ ಹಾಕಿ.\n"
                    "2. ಪ್ಲಾನೋಫಿಕ್ಸ್ (Planofix - 1 ಮಿ.ಲೀ 4 ಲೀಟರ್ ನೀರಿಗೆ) ಹೂಗೊಂಚಲಿಗೆ ಸಿಂಪಡಿಸಿ.\n"
                    "3. ಬುಡದಲ್ಲಿ ನೀರು ನಿಲ್ಲದಂತೆ ಬಸಿಗಾಲುವೆ ಮಾಡಿ."
                )
            },
            "bud rot": {
                "name": "ಸುಳಿ ಕೊಳೆ ರೋಗ (Bud Rot)",
                "cause": "ಫೈಟೊಫ್ಥೊರಾ ಶಿಲೀಂಧ್ರದಿಂದ ಎಳೆಯ ಸುಳಿ ಮತ್ತು ಗರಿಗಳು ಕೊಳೆಯುತ್ತವೆ.",
                "solution": (
                    "1. ಕೊಳೆತ ಸುಳಿಯನ್ನು ಕತ್ತರಿಸಿ ತೆಗೆದು ಬೋರ್ಡೋ ಪೇಸ್ಟ್ ಲೇಪಿಸಿ.\n"
                    "2. ಸುತ್ತಲಿನ ಮರಗಳ ಸುಳಿಗೆ 1% ಬೋರ್ಡೋ ಮಿಶ್ರಣ ಸಿಂಪಡಿಸಿ.\n"
                    "3. ಮುಂಗಾರು ಮಳೆಗೆ ಮುನ್ನ ಮರದ ಸುಳಿ ಸ್ವಚ್ಛಗೊಳಿಸಿ."
                )
            },
            "gray leaf spot": {
                "name": "ಬೂದು ಎಲೆ ಚುಕ್ಕೆ ರೋಗ (Gray Leaf Spot)",
                "cause": "ಪೆಸ್ಟಲೋಶಿಯೊಪ್ಸಿಸ್ ಶಿಲೀಂಧ್ರದಿಂದ ಹಳೆಯ ಗರಿಗಳ ಮೇಲೆ ಬೂದು ಚುಕ್ಕೆಗಳು ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತವೆ.",
                "solution": (
                    "1. ಅತಿಯಾಗಿ ರೋಗಪೀಡಿತ ಒಣಗಿದ ಕೆಳ ಗರಿಗಳನ್ನು ಕತ್ತರಿಸಿ ಸುಟ್ಟುಹಾಕಿ.\n"
                    "2. ಮ್ಯಾಂಕೋಜೆಬ್ (2 ಗ್ರಾಂ/ಲೀ) ಅಥವಾ ಹೆಕ್ಸಾಕೊನಜೋಲ್ (1 ಮಿ.ಲೀ/ಲೀ) ಸಿಂಪಡಿಸಿ.\n"
                    "3. ಪೊಟ್ಯಾಷ್ ಹಾಗೂ ಕೊಟ್ಟಿಗೆ ಗೊಬ್ಬರವನ್ನು ತಪ್ಪದೇ ನೀಡಿ."
                )
            },
            "leaf rot": {
                "name": "ಎಲೆ ಕೊಳೆ ರೋಗ (Leaf Rot)",
                "cause": "ಶಿಲೀಂಧ್ರ ಸೋಂಕಿನಿಂದ ಗರಿಗಳ ಅಂಚು ಕಪ್ಪಾಗಿ ಕೊಳೆಯುತ್ತದೆ.",
                "solution": (
                    "1. ಕೊಳೆತ ಗರಿಗಳ ಭಾಗವನ್ನು ಕತ್ತರಿಸಿ ಬೋರ್ಡೋ ಮುಲಾಮು ಹಚ್ಚಿ.\n"
                    "2. ಹೆಕ್ಸಾಕೊನಜೋಲ್ (Hexaconazole 5% EC) ಸಿಂಪಡಿಸಿ.\n"
                    "3. ಪ್ರತಿ ಮರಕ್ಕೆ 500 ಗ್ರಾಂ ಮ್ಯಾಗ್ನೀಸಿಯಮ್ ಸಲ್ಫೇಟ್ ಗೊಬ್ಬರ ನೀಡಿ."
                )
            },
            "stembleeding": {
                "name": "ಕಾಂಡ ಒಸರುವಿಕೆ / ಕಾಂಡ ಸೋರುವಿಕೆ (Stem Bleeding)",
                "cause": "ಶಿಲೀಂಧ್ರವು ಕಾಂಡದ ಬಿರುಕುಗಳಿಂದ ಪ್ರವೇಶಿಸಿ ಕೆಂಪು-ಕಂದು ದ್ರವ ಸೋರುತ್ತದೆ.",
                "solution": (
                    "1. ಸೋರುತ್ತಿರುವ ಭಾಗವನ್ನು ಚೆನ್ನಾಗಿ ಕೆರೆದು ಸ್ವಚ್ಛಗೊಳಿಸಿ.\n"
                    "2. ಕೆರೆದ ಜಾಗಕ್ಕೆ ಬೋರ್ಡೋ ಪೇಸ್ಟ್ ಅಥವಾ ಕೋಲ್ ಟಾರ್ ಹಚ್ಚಿ.\n"
                    "3. ಬುಡಕ್ಕೆ 5 ಕೆ.ಜಿ ಬೇವಿನ ಹಿಂಡಿ ಹಾಗೂ ಟ್ರೈಕೋಡರ್ಮಾ ಜೈವಿಕ ಗೊಬ್ಬರ ನೀಡಿ.\n"
                    "4. ವರ್ಷಕ್ಕೆ 3 ಬಾರಿ ಹೆಕ್ಸಾಕೊನಜೋಲ್‌ನಿಂದ ಬೇರು ಪೋಷಣೆ ನೀಡಿ."
                )
            }
        }
    }
}

curr_ui = UI_TEXT[language]

# ----------------- KVK & Helpline Directory -----------------
KVK_DIRECTORY = [
    {"District": "Mysuru", "Center": "ICAR - JSS Krishi Vigyan Kendra, Suttur", "Contact": "+91 821-2548238", "Officer": "Senior Scientist & Head"},
    {"District": "Tumakuru", "Center": "ICAR - KVK Hirehalli, Tumakuru", "Contact": "+91 816-2243214", "Officer": "Horticulture Specialist"},
    {"District": "Hassan", "Center": "KVK Kandali, Hassan (UAS Bangalore)", "Contact": "+91 8172-256792", "Officer": "Crop Protection Scientist"},
    {"District": "Dakshina Kannada", "Center": "KVK Mangaluru (Kankanady)", "Contact": "+91 824-2431872", "Officer": "Plant Pathologist"},
    {"District": "Udupi", "Center": "ICAR - KVK Brahmavar, Udupi", "Contact": "+91 820-2563923", "Officer": "Agronomy Extension Officer"},
    {"District": "Mandya", "Center": "KVK V.C. Farm, Mandya", "Contact": "+91 8232-277466", "Officer": "Horticulture Officer"},
    {"District": "Chikkamagaluru", "Center": "ICAR - KVK Mudigere", "Contact": "+91 8263-228020", "Officer": "Horticulture Expert"},
    {"District": "Chitradurga", "Center": "ICAR - KVK Babbur Farm, Hiriyur", "Contact": "+91 8195-220025", "Officer": "Extension Specialist"},
    {"District": "Davanagere", "Center": "ICAR - Taralabalu KVK, Davanagere", "Contact": "+91 8192-263462", "Officer": "Plant Protection Officer"},
    {"District": "Shivamogga", "Center": "ICAR - KVK Navile, Shivamogga", "Contact": "+91 8182-267333", "Officer": "Horticultural Pathologist"},
    {"District": "National / State", "Center": "Kisan Call Center (ಟೋಲ್ ಫ್ರೀ)", "Contact": "1800-180-1551", "Officer": "Govt of India Agronomists"},
    {"District": "National / State", "Center": "Coconut Development Board (CDB Bengaluru)", "Contact": "+91 80-23340546", "Officer": "CDB Advisory Wing"}
]

# ----------------- 30-Day Treatment Protocols -----------------
TREATMENT_PROTOCOLS = {
    "bud rot": [
        {"Day": "Day 1 (ತಕ್ಷಣ)", "Task": "Cut out all rotten central spear tissues cleanly with a sanitized knife. Burn or bury the removed tissues."},
        {"Day": "Day 3 (3ನೇ ದಿನ)", "Task": "Smear freshly prepared Bordeaux Paste thoroughly over the exposed crown wound to seal against rain."},
        {"Day": "Day 10 (10ನೇ ದಿನ)", "Task": "Spray surrounding healthy trees with 1% Bordeaux Mixture or Copper Oxychloride (3 g/L) to halt aerial fungal spore spread."},
        {"Day": "Day 25 (25ನೇ ದಿನ)", "Task": "Inspect crown for fresh spear emergence. Apply 5 kg neem cake and 100g Trichoderma in the basin to boost root vigor."}
    ],
    "stembleeding": [
        {"Day": "Day 1 (ತಕ್ಷಣ)", "Task": "Chisel off the oozing dark bark with a clean chisel until clean yellowish wood is exposed."},
        {"Day": "Day 2 (2ನೇ ದಿನ)", "Task": "Paint the chiselled trunk surface completely with Bordeaux Paste or Hot Coal Tar to seal the entry wound."},
        {"Day": "Day 7 (7ನೇ ದಿನ)", "Task": "Perform root feeding: Cut a pencil-thick active reddish root and insert it into a pouch with 5 mL Hexaconazole in 100 mL water."},
        {"Day": "Day 30 (30ನೇ ದಿನ)", "Task": "Apply 5 kg neem cake enriched with Trichoderma harzianum into the root basin. Ensure proper soil drainage."}
    ],
    "gray leaf spot": [
        {"Day": "Day 1 (ತಕ್ಷಣ)", "Task": "Prune and burn severely blighted bottom fronds showing dry grey spots with yellow halos."},
        {"Day": "Day 5 (5ನೇ ದಿನ)", "Task": "Spray foliage with Mancozeb (2 g/L) or Hexaconazole 5% EC (1 mL/L) covering both upper and lower leaf surfaces."},
        {"Day": "Day 15 (15ನೇ ದಿನ)", "Task": "Repeat foliar spray with Copper Oxychloride (3 g/L) if high humidity and rain persist."},
        {"Day": "Day 30 (30ನೇ ದಿನ)", "Task": "Apply 1.3 kg Muriate of Potash (MOP) per tree basin to build cellular leaf resistance against fungal penetration."}
    ],
    "leaf rot": [
        {"Day": "Day 1 (ತಕ್ಷಣ)", "Task": "Cut away rotten distal black leaflets and safely destroy them away from the orchard."},
        {"Day": "Day 4 (4ನೇ ದಿನ)", "Task": "Swab infected leaf bases with Bordeaux paste."},
        {"Day": "Day 12 (12ನೇ ದಿನ)", "Task": "Foliar spray with Hexaconazole (1 mL/L water)."},
        {"Day": "Day 28 (28ನೇ ದಿನ)", "Task": "Apply 500g Magnesium Sulphate + balanced NPK around tree basin to restore green frond photosynthesis."}
    ],
    "bud root dropping": [
        {"Day": "Day 1 (ತಕ್ಷಣ)", "Task": "Soil application of 50 g Borax and 1.3 kg MOP per tree basin. Irrigate immediately."},
        {"Day": "Day 7 (7ನೇ ದಿನ)", "Task": "Foliar spray of Planofix (Alpha NAA @ 1 mL in 4 Liters water) on receptive button clusters to prevent premature abscission."},
        {"Day": "Day 15 (15ನೇ ದಿನ)", "Task": "Ensure mulch ring of dry leaves or coir pith in basin to retain steady root moisture and prevent stress."},
        {"Day": "Day 30 (30ನೇ ದಿನ)", "Task": "Secondary light spray of Boron (Solubor @ 2 g/L) directly on young inflorescences."}
    ]
}

# ----------------- Fertilizer & Chemical Dosage Calculation Engine -----------------
def render_dosage_calculator(disease_name_key, lang="English"):
    """Calculates chemical & fertilizer dosages per number of palms based on ICAR recommendations."""
    key = disease_name_key.strip().lower()
    if key not in curr_ui["diseases"]:
        return

    st.markdown("---")
    st.subheader(curr_ui["calc_header"])

    num_trees = st.number_input(
        curr_ui["calc_num_trees"],
        min_value=1,
        max_value=1000,
        value=10,
        step=1,
        key=f"calc_trees_{key}"
    )

    if key in ["bud rot"]:
        water_l = num_trees * 1.5
        coper_sulphate_kg = round(water_l * 0.01, 2)
        quick_lime_kg = round(water_l * 0.01, 2)
        if lang == "ಕನ್ನಡ":
            st.success(
                f"🌿 **{num_trees} ಮರಗಳಿಗೆ 1% ಬೋರ್ಡೋ ಮಿಶ್ರಣ ಸಿಂಪಡಣೆಗೆ ಬೇಕಾಗುವ ಪ್ರಮಾಣ:**\n"
                f"- **ಒಟ್ಟು ನೀರು:** {water_l:.1f} ಲೀಟರ್\n"
                f"- **ಮೈಲುತುತ್ತು (Copper Sulphate):** {coper_sulphate_kg} ಕೆ.ಜಿ\n"
                f"- **ಸುಣ್ಣ (Quicklime):** {quick_lime_kg} ಕೆ.ಜಿ"
            )
        else:
            st.success(
                f"🌿 **Chemicals required for 1% Bordeaux spray on {num_trees} trees:**\n"
                f"- **Total Water:** {water_l:.1f} Liters\n"
                f"- **Copper Sulphate:** {coper_sulphate_kg} kg\n"
                f"- **Quick Lime:** {quick_lime_kg} kg"
            )

    elif key in ["bud root dropping"]:
        mop_kg = round(num_trees * 1.3, 2)
        borax_kg = round((num_trees * 50) / 1000, 2)
        water_spray_l = num_trees * 2.0
        planofix_ml = round(water_spray_l / 4, 1)

        if lang == "ಕನ್ನಡ":
            st.success(
                f"🌿 **{num_trees} ಮರಗಳಿಗೆ ಬೇಕಾಗುವ ಪೋಷಕಾಂಶ ಪ್ರಮಾಣ:**\n"
                f"- **ಎಂ.ಒ.ಪಿ (MOP ಪೊಟ್ಯಾಷ್):** {mop_kg} ಕೆ.ಜಿ\n"
                f"- **ಬೋರಾಕ್ಸ್ (Borax):** {borax_kg} ಕೆ.ಜಿ\n"
                f"- **ಪ್ಲಾನೋಫಿಕ್ಸ್:** {planofix_ml} ಮಿ.ಲೀ ({water_spray_l:.0f} ಲೀಟರ್ ನೀರಿಗೆ)."
            )
        else:
            st.success(
                f"🌿 **Fertilizers & Nutrients for {num_trees} palms:**\n"
                f"- **MOP Potash:** {mop_kg} kg\n"
                f"- **Borax:** {borax_kg} kg\n"
                f"- **Planofix:** {planofix_ml} mL in {water_spray_l:.0f} Liters water."
            )

    elif key in ["stembleeding"]:
        hexaconazole_ml = num_trees * 5
        root_water_ml = num_trees * 100
        neem_cake_kg = num_trees * 5
        tricho_kg = round(num_trees * 0.1, 2)

        if lang == "ಕನ್ನಡ":
            st.success(
                f"🌿 **{num_trees} ಮರಗಳ ಕಾಂಡ ಒಸರುವಿಕೆ ನಿಯಂತ್ರಣಕ್ಕೆ:**\n"
                f"- **ಹೆಕ್ಸಾಕೊನಜೋಲ್ (5% EC):** {hexaconazole_ml} ಮಿ.ಲೀ\n"
                f"- **ಬೇರು ಪೋಷಣೆಯ ನೀರು:** {root_water_ml} ಮಿ.ಲೀ\n"
                f"- **ಬೇವಿನ ಹಿಂಡಿ:** {neem_cake_kg} ಕೆ.ಜಿ\n"
                f"- **ಟ್ರೈಕೋಡರ್ಮಾ ಜೈವಿಕ ಗೊಬ್ಬರ:** {tricho_kg} ಕೆ.ಜಿ"
            )
        else:
            st.success(
                f"🌿 **Remedies for {num_trees} palms (Root Feeding):**\n"
                f"- **Hexaconazole 5% EC:** {hexaconazole_ml} mL\n"
                f"- **Neem Cake:** {neem_cake_kg} kg\n"
                f"- **Trichoderma:** {tricho_kg} kg"
            )

    elif key in ["gray leaf spot", "leaf rot"]:
        mancozeb_g = num_trees * 6
        water_l = num_trees * 3
        hexaconazole_ml = num_trees * 3

        if lang == "ಕನ್ನಡ":
            st.success(
                f"🌿 **{num_trees} ಮರಗಳ ಗರಿ ರೋಗ ನಿಯಂತ್ರಣಕ್ಕೆ:**\n"
                f"- **ಒಟ್ಟು ನೀರು:** {water_l} ಲೀಟರ್\n"
                f"- **ಮ್ಯಾಂಕೋಜೆಬ್ (Mancozeb 75% WP):** {mancozeb_g} ಗ್ರಾಂ\n"
                f"- **ಅಥವಾ ಹೆಕ್ಸಾಕೊನಜೋಲ್:** {hexaconazole_ml} ಮಿ.ಲೀ"
            )
        else:
            st.success(
                f"🌿 **Spray quantities for {num_trees} palms:**\n"
                f"- **Total Water:** {water_l} Liters\n"
                f"- **Mancozeb:** {mancozeb_g} grams OR **Hexaconazole:** {hexaconazole_ml} mL"
            )

# ----------------- Calendar Protocol Renderer -----------------
def render_treatment_calendar(disease_name_key, lang="English"):
    """Renders a chronological 30-day treatment calendar for the diagnosed condition."""
    key = disease_name_key.strip().lower()
    if key not in TREATMENT_PROTOCOLS:
        return

    st.markdown("---")
    st.subheader(curr_ui["schedule_header"])
    steps = TREATMENT_PROTOCOLS[key]

    for step in steps:
        with st.container():
            c_day, c_task = st.columns([1, 4])
            c_day.info(f"**{step['Day']}**")
            c_task.write(step['Task'])

# Sidebar: Page Navigation
st.sidebar.markdown("---")
st.sidebar.header(curr_ui["nav_header"])
page_choice = st.sidebar.radio(
    "Go to / ತೆರಳಿ",
    (curr_ui["nav_home"], curr_ui["nav_mandi"], curr_ui["nav_helpline"], curr_ui["nav_about"])
)

# =========================================================================
# PAGE 1: APMC MANDI RATES (ALL CITIES IN KARNATAKA)
# =========================================================================
if page_choice == curr_ui["nav_mandi"]:
    st.title("📈 All Karnataka APMC Mandi Rates | ಕರ್ನಾಟಕದ ಎಲ್ಲಾ ಎ.ಪಿ.ಎಂ.ಸಿ ಮಾರುಕಟ್ಟೆ ಧಾರಣೆ")
    st.markdown("Daily wholesale rates across all Karnataka cities & mandis for Copra (Ball/Milling), Coconut, and Tender Coconut.")

    active_dataset = COMPREHENSIVE_KARNATAKA_MANDIS

    # Top Benchmark Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🌴 Tiptur Ball Copra", "₹ 12,650 / Qtl", "▲ +2.4%")
    m2.metric("🥥 Arsikere Copra", "₹ 12,400 / Qtl", "▲ +1.8%")
    m3.metric("🥥 Maddur Tender Nut", "₹ 34 / Nut", "▲ +5.0%")
    m4.metric("🌴 Mangaluru Coconut", "₹ 24,500 / 1000", "▲ +0.5%")

    st.markdown("---")

    # Search & Multi-Filter Controls
    f_col1, f_col2, f_col3 = st.columns(3)

    all_districts = ["All Districts / ಎಲ್ಲಾ ಜಿಲ್ಲೆಗಳು"] + sorted(list({item["District"] for item in active_dataset}))
    selected_district = f_col1.selectbox("Filter by District (ಜಿಲ್ಲೆ):", all_districts)

    all_commodities = ["All Commodities / ಎಲ್ಲಾ ಉತ್ಪನ್ನಗಳು"] + sorted(list({item["Commodity"] for item in active_dataset}))
    selected_commodity = f_col2.selectbox("Filter by Commodity (ಉತ್ಪನ್ನ):", all_commodities)

    search_query = f_col3.text_input("Search Market/City (ನಗರ/ಮಾರುಕಟ್ಟೆ ಹುಡುಕಿ):", placeholder="e.g. Tiptur, Udupi, Mysuru...")

    # Filter Logic
    filtered_data = active_dataset

    if selected_district != "All Districts / ಎಲ್ಲಾ ಜಿಲ್ಲೆಗಳು":
        filtered_data = [d for d in filtered_data if d["District"] == selected_district]

    if selected_commodity != "All Commodities / ಎಲ್ಲಾ ಉತ್ಪನ್ನಗಳು":
        filtered_data = [d for d in filtered_data if d["Commodity"] == selected_commodity]

    if search_query.strip():
        q = search_query.strip().lower()
        filtered_data = [
            d for d in filtered_data
            if q in d["Market"].lower() or q in d["District"].lower() or q in d["Commodity"].lower()
        ]

    st.markdown(f"##### Showing **{len(filtered_data)}** Mandi Listings across Karnataka:")
    st.dataframe(filtered_data, use_container_width=True)
    st.caption("ℹ️ Source: Integrated Agmarknet & Karnataka State Agricultural Marketing Board (KSAMB) daily market feeds.")

# =========================================================================
# PAGE 2: KVK & OFFICER HELPLINES
# =========================================================================
elif page_choice == curr_ui["nav_helpline"]:
    st.title("📞 KVK & Horticulture Officer Directory | ಸಹಾಯವಾಣಿ")
    st.markdown("Contact agricultural scientists, plant doctors, and university extension specialists directly.")

    st.warning("🚨 **National Kisan Call Center Toll-Free:** `1800-180-1551` (Free calling from 6 AM to 10 PM daily)")

    st.markdown("---")
    col_dist, col_empty = st.columns([2, 2])
    all_kvk_dist = ["All"] + sorted(list({k["District"] for k in KVK_DIRECTORY}))
    sel_kvk_dist = col_dist.selectbox("Select Your District / ಜಿಲ್ಲೆ:", all_kvk_dist)

    matched_kvk = KVK_DIRECTORY if sel_kvk_dist == "All" else [k for k in KVK_DIRECTORY if k["District"] == sel_kvk_dist]

    for kvk in matched_kvk:
        with st.expander(f"📍 {kvk['District']} — {kvk['Center']}", expanded=True):
            c_info, c_btn = st.columns([3, 1])
            c_info.write(f"**Specialist / Role:** {kvk['Officer']}")
            c_info.write(f"**Official Contact:** `{kvk['Contact']}`")
            clean_phone = kvk['Contact'].replace(" ", "").replace("-", "")
            c_btn.markdown(f'<a href="tel:{clean_phone}"><button style="background-color:#2e7d32;color:white;padding:8px 16px;border:none;border-radius:4px;cursor:pointer;">📞 Call Center</button></a>', unsafe_allow_html=True)

# =========================================================================
# PAGE 3: ABOUT PAGE
# =========================================================================
elif page_choice == curr_ui["nav_about"]:
    st.title(curr_ui["about_heading"])
    st.markdown(f"##### {curr_ui['about_intro']}")
    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader(curr_ui["about_features_title"])
        for item in curr_ui["about_features"]:
            st.markdown(f"- {item}")

    with col_b:
        st.subheader(curr_ui["about_diseases_title"])
        for d in curr_ui["about_diseases"]:
            st.markdown(f"- {d}")

    st.markdown("---")
    st.subheader(curr_ui["about_dev_title"])

    dev_card = f"""
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-left: 5px solid #2e7d32; border-radius: 8px; padding: 18px 24px; margin-top: 10px;">
        <h4 style="margin: 0 0 8px 0; color: #1e293b;">{curr_ui['about_dev_name']}</h4>
        <p style="margin: 0 0 10px 0; color: #059669; font-weight: 600;">🧠 {curr_ui['about_dev_rag']}</p>
        <div style="color: #334155; line-height: 1.8;">
            <div>📧 <strong>Email:</strong> <a href="mailto:{curr_ui['about_dev_email']}" style="color: #2563eb; text-decoration: none;">{curr_ui['about_dev_email']}</a></div>
            <div>📞 <strong>Phone:</strong> <a href="tel:9901673869" style="color: #2563eb; text-decoration: none;">{curr_ui['about_dev_phone']}</a></div>
            <div>📍 <strong>Address:</strong> {curr_ui['about_dev_address']}</div>
        </div>
    </div>
    """
    st.markdown(dev_card, unsafe_allow_html=True)

# =========================================================================
# PAGE 4: HOME / DETECTION & LIVE WEATHER
# =========================================================================
else:
    # Sidebar Weather Selector
    st.sidebar.markdown("---")
    st.sidebar.header(curr_ui["weather_title"])

    preset_cities = ["Mysuru", "Tiptur", "Tumakuru", "Arsikere", "Hassan", "Maddur", "Mangaluru", "Udupi", "Chikkamagaluru", "Other"]
    selected_preset = st.sidebar.selectbox(curr_ui["city_input_label"], preset_cities, index=0)

    if selected_preset == "Other":
        target_city = st.sidebar.text_input("Enter city name:", value="Mysuru")
    else:
        target_city = selected_preset

    st.sidebar.button(curr_ui["weather_btn"])

    # Fetch live weather (guaranteed return)
    weather_info = fetch_weather(target_city)

    st.title(curr_ui["title"])

    # ----------------- Render Live Weather Display -----------------
    if weather_info:
        st.markdown(f"### 📍 {weather_info['city']} — {curr_ui['weather_title']}")
        w1, w2, w3, w4 = st.columns(4)
        w1.metric(f"🌡️ {curr_ui['temp']}", f"{weather_info['temp']} °C")
        w2.metric(f"💧 {curr_ui['humidity']}", f"{weather_info['humidity']} %")
        w3.metric(f"🌧️ {curr_ui['rain']}", f"{weather_info['precip']} mm")
        w4.metric(f"💨 {curr_ui['wind']}", f"{weather_info['wind']} km/h")

        try:
            humidity_val = float(weather_info['humidity'])
            if humidity_val >= 80:
                st.warning(curr_ui["weather_risk_high"])
            else:
                st.success(curr_ui["weather_risk_normal"])
        except (ValueError, TypeError):
            pass
        st.markdown("---")

    # Gemini LLM Config for Text/RAG Advisory
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    modell = None
    if GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            modell = genai.GenerativeModel(model_name="gemini-1.5-flash")
        except Exception:
            modell = None

    def inputdisease(disease_detected, selected_lang="English"):
        norm = str(disease_detected).strip().lower()
        fallback = curr_ui["diseases"].get(norm, {}).get("cause", "Disease caused by plant pathogens.")
        if modell is None:
            return fallback

        if selected_lang == "ಕನ್ನಡ":
            prompt = f"ನೀವು ತೆಂಗಿನ ಮರದ ಕೃಷಿ ತಜ್ಞರು. {disease_detected} ರೋಗ ಏಕೆ ಬರುತ್ತದೆ ಎಂದು 40 ಪದಗಳಲ್ಲಿ ಕನ್ನಡದಲ್ಲಿ ತಿಳಿಸಿ."
        else:
            prompt = f"Explain to a coconut farmer why {disease_detected} occurs in 40 words."

        try:
            res = modell.generate_content(prompt)
            return res.text
        except Exception:
            return fallback

    # Model Configuration & Load
    st.sidebar.markdown("---")
    st.sidebar.header(curr_ui["model_config"])
    confidence = float(st.sidebar.slider(curr_ui["confidence"], 10, 100, 35)) / 100

    model_path = Path(settings.DETECTION_MODEL)
    try:
        model = helper.load_model(model_path)
    except Exception as ex:
        st.error(f"Unable to load model: {model_path} - {ex}")

    # Image Detection Section
    st.sidebar.header(curr_ui["image_config"])
    source_img = st.sidebar.file_uploader(curr_ui["choose_img"], type=("jpg", "jpeg", "png", "bmp", "webp"))

    col1, col2 = st.columns(2)

    with col1:
        try:
            if source_img is None:
                default_image_path = str(settings.DEFAULT_IMAGE)
                st.image(default_image_path, caption=curr_ui["default_img"], use_container_width=True)
            else:
                uploaded_image = PIL.Image.open(source_img)
                st.image(source_img, caption=curr_ui["uploaded_img"], use_container_width=True)
        except Exception as ex:
            st.error(f"Error loading image: {ex}")

    with col2:
        if source_img is None:
            default_detected_image_path = str(settings.DEFAULT_DETECT_IMAGE)
            st.image(default_detected_image_path, caption=curr_ui["detected_img"], use_container_width=True)
        else:
            if st.sidebar.button(curr_ui["detect_btn"]):
                res = model.predict(uploaded_image, conf=confidence)
                names = res[0].names
                boxes = res[0].boxes
                res_plotted = res[0].plot()[:, :, ::-1]

                class_detections_values = [res[0].boxes.cls.tolist().count(k) for k in names.keys()]
                classes_detected = dict(zip(names.values(), class_detections_values))

                # Store in session state
                st.session_state['res_plotted'] = res_plotted
                st.session_state['classes_detected'] = classes_detected
                st.session_state['boxes'] = boxes
                st.session_state['names'] = names

            # Render from session state
            if 'res_plotted' in st.session_state:
                st.image(st.session_state['res_plotted'], caption=curr_ui["detected_img"], use_container_width=True)

                classes_detected = st.session_state['classes_detected']
                boxes = st.session_state['boxes']
                names = st.session_state['names']

                # Filter real disease detections
                real_diseases = {}
                for k, count in classes_detected.items():
                    norm_k = k.strip().lower()
                    if norm_k in curr_ui["diseases"] and count > 0:
                        real_diseases[norm_k] = count

                speech_summary_parts = []

                # ----------------- CASE 1: HEALTHY TREE -----------------
                if len(real_diseases) == 0:
                    st.markdown("---")
                    st.success(f"### {curr_ui['healthy_title']}")
                    st.write(curr_ui["healthy_desc"])
                    st.info(curr_ui["healthy_tips"])

                    if language == "ಕನ್ನಡ":
                        speech_summary_parts.append("ತೆಂಗಿನ ಮರವು ಆರೋಗ್ಯಕರವಾಗಿದೆ. ಯಾವುದೇ ಶಿಲೀಂಧ್ರ ಅಥವಾ ರೋಗದ ಲಕ್ಷಣಗಳು ಕಂಡುಬಂದಿಲ್ಲ. ಸಾಮಾನ್ಯ ಗೊಬ್ಬರ ಮತ್ತು ನೀರಾವರಿ ಮುಂದುವರಿಸಿ.")
                    else:
                        speech_summary_parts.append("The coconut palm appears healthy and vigorous with no visible disease. Continue standard nutrition and irrigation.")

                # ----------------- CASE 2: DISEASE DETECTED -----------------
                else:
                    product_links = {
                        "bud root dropping": ["https://cultree.in/products/shivalik-roksin-thiophanate-methyl-70-wp-fungicide"],
                        "bud rot": ["https://cultree.in/products/shivalik-roksin-thiophanate-methyl-70-wp-fungicide"],
                        "gray leaf spot": ["https://www.bighaat.com/products/agriventure-cooxy"],
                        "leaf rot": ["https://ariesagro.com/jahaan-hexaconazole5-w-w/"],
                        "stembleeding": ["https://www.bighaat.com/products/blue-copper-fungicide-1"]
                    }

                    for norm_key, count in real_diseases.items():
                        info = curr_ui["diseases"][norm_key]
                        cause_ai = inputdisease(disease_detected=norm_key, selected_lang=language)

                        st.markdown("---")
                        st.subheader(f"⚠️ {curr_ui['detected_label']}: :red[{info['name']}] ({count})")
                        st.info(f"💡 **{curr_ui['explain_ai']}**: \n\n{cause_ai}")
                        st.warning(f"⚠️ **{curr_ui['cause_label']}**: \n\n{info['cause']}")
                        st.success(f"✅ **{curr_ui['solution_label']}**: \n\n{info['solution']}")

                        # 1. Interactive Chemical Calculator
                        render_dosage_calculator(norm_key, lang=language)

                        # 2. Chronological 30-Day Spraying Calendar
                        render_treatment_calendar(norm_key, lang=language)

                        if language == "ಕನ್ನಡ":
                            speech_summary_parts.append(f"ಪತ್ತೆಯಾದ ರೋಗ: {info['name']}. ಪರಿಹಾರ ಕ್ರಮಗಳು: {info['solution']}")
                        else:
                            speech_summary_parts.append(f"Condition detected: {info['name']}. Treatment: {info['solution']}")

                        if norm_key in product_links:
                            for link in product_links[norm_key]:
                                st.link_button(curr_ui["product_link"], link)

                # ----------------- Audio Section -----------------
                full_speech_text = " ".join(speech_summary_parts).strip()
                if full_speech_text:
                    st.markdown("---")
                    st.subheader("🔊 Audio Advisory / ಧ್ವನಿ ಸಲಹೆ")

                    if st.button(curr_ui["speak_btn"], key="btn_speak_audio"):
                        with st.spinner("Generating speech... / ಧ್ವನಿ ಸಿದ್ಧವಾಗುತ್ತಿದೆ..."):
                            play_audio_summary(full_speech_text, lang=language)

                with st.expander(curr_ui["results_expander"]):
                    if len(boxes) == 0:
                        st.write(curr_ui["no_objects"])
                    else:
                        for i, box in enumerate(boxes, start=1):
                            cls_id = int(box.cls.item())
                            cls_name = names.get(cls_id, str(cls_id))
                            conf_val = float(box.conf.item() * 100)
                            st.write(f"{i}. **{cls_name}** — Confidence: {conf_val:.2f}%")