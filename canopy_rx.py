import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from geopy.geocoders import Nominatim

# --- 1. PAGE CONFIGURATION & THEME ---
st.set_page_config(
    page_title="CanopyRx Pro - Environmental Travel & Medicine Portal", 
    page_icon="🩺", 
    layout="wide"
)

# Premium Custom Styling (Restored)
st.markdown("""
<style>
    .free-badge {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
    }
    .normal-value-badge {
        background-color: #f0fdf4;
        color: #16a34a;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
    }
    .premium-badge {
        background-color: #fef3c7;
        color: #b45309;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
    }
    .premium-card {
        background-color: #fffbeb;
        border: 1px solid #fcd34d;
        border-left: 6px solid #d97706;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .prescription-item {
        margin-bottom: 10px;
        padding-left: 10px;
        border-left: 3px solid #0d8a72;
    }
    .premium-lock-box {
        background-color: #fcf8e3;
        border: 2px dashed #f0ad4e;
        padding: 30px;
        border-radius: 8px;
        text-align: center;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. INITIALIZE GLOBAL STATE ---
if "lat" not in st.session_state:
    st.session_state.lat = None
if "lon" not in st.session_state:
    st.session_state.lon = None
if "resolved_address" not in st.session_state:
    st.session_state.resolved_address = ""
if "engine_active" not in st.session_state:
    st.session_state.engine_active = False
if "user_tier" not in st.session_state:
    st.session_state.user_tier = "Free"

# --- 3. LIVE API DATA FETCH ENGINE ---
def fetch_environmental_data(latitude, longitude):
    data = {
        "temp": 27.0, "humidity": 70.0, "uv": 5.0,
        "pm25": 35.0, "pm10": 50.0, "no2": 20.0, "co": 380.0, "o3": 40.0
    }
    try:
        # Weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,uv_index"
        w_res = requests.get(weather_url, timeout=5).json()
        if "current" in w_res:
            data["temp"] = w_res["current"].get("temperature_2m", data["temp"])
            data["humidity"] = w_res["current"].get("relative_humidity_2m", data["humidity"])
            data["uv"] = w_res["current"].get("uv_index", data["uv"])

        # Air Quality
        aqi_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={latitude}&longitude={longitude}&current=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone"
        a_res = requests.get(aqi_url, timeout=5).json()
        if "current" in a_res:
            data["pm25"] = a_res["current"].get("pm2_5", data["pm25"])
            data["pm10"] = a_res["current"].get("pm10", data["pm10"])
            data["no2"] = a_res["current"].get("nitrogen_dioxide", data["no2"])
            data["co"] = a_res["current"].get("carbon_monoxide", data["co"])
            data["o3"] = a_res["current"].get("ozone", data["o3"])
    except Exception:
        pass
    return data

# --- 4. PORTAL BRANDING HEADER ---
st.markdown("# 🩺 CanopyRx: Environmental Medicine & Safe-Travel Portal")
st.markdown("##### *Smart-spatial diagnostics mapping local pathology risks, decoded micro-climate metrics, and premium personalized clinical defense plans.*")
st.write("---")

# --- 5. SIDEBAR CONTROLS ---
st.sidebar.markdown("### 🔐 User Access Level")
auth_mode = st.sidebar.radio("Select Account Tier:", ["Public Access (Free)", "Subscribed Patient (Premium)"])
st.session_state.user_tier = "Premium" if "Premium" in auth_mode else "Free"

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ Geographic Tracking")

# JavaScript Geolocation Injector Box
st.sidebar.markdown("#### 📍 Live Satellite Tracking")
js_geo_code = """
<div style="text-align: center;">
    <button onclick="getLocation()" style="
        width: 100%; 
        background-color: #ff4b4b; 
        color: white; 
        border: none; 
        padding: 10px; 
        border-radius: 8px; 
        cursor: pointer;
        font-weight: bold;
        font-size: 14px;
    ">📌 Detect My Live Location</button>
</div>

<script>
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition, showError);
    } else {
        alert("Geolocation is not supported by this browser.");
    }
}

function showPosition(position) {
    // Send coordinates via window messaging directly to the main Streamlit interface
    var coords = position.coords.latitude + "," + position.coords.longitude;
    window.parent.postMessage({
        type: 'streamlit:setComponentValue',
        value: coords
    }, '*');
}

function showError(error) {
    switch(error.code) {
        case error.PERMISSION_DENIED:
            alert("User denied the request for Geolocation. Check your site permissions lock in the URL bar.");
            break;
        case error.POSITION_UNAVAILABLE:
            alert("Location information is unavailable.");
            break;
        case error.TIMEOUT:
            alert("The request to get user location timed out.");
            break;
        case error.UNKNOWN_ERROR:
            alert("An unknown error occurred.");
            break;
    }
}
</script>
"""

import streamlit.components.v1 as components
# Render the button inside the sidebar
loc_receiver = components.html(js_geo_code, height=50)

# Check if browser returned location values via the component channel
if loc_receiver:
    try:
        raw_coords = str(loc_receiver)
        if "," in raw_coords:
            lat_val, lon_val = map(float, raw_coords.split(","))
            st.session_state.lat = lat_val
            st.session_state.lon = lon_val
            st.session_state.engine_active = True
    except Exception:
        pass

st.sidebar.markdown("---")

# Manual Fallback Input Fields
input_mode = st.sidebar.radio("Manual Location Overrides:", ["Search Address / Landmark", "Direct Coordinates"])
resolved_by_coords = False

if input_mode == "Search Address / Landmark":
    country_option = st.sidebar.selectbox("Region / Country:", ["India", "United States", "United Kingdom", "Global / Other"])
    search_query = st.sidebar.text_input("Enter City, Pincode, or Area Name:", placeholder="e.g., Kurla West Mumbai...")

    if st.sidebar.button("Search & Analyze Location", use_container_width=True):
        if search_query:
            try:
                geolocator = Nominatim(user_agent="canopy_rx_platform_engine")
                final_q = f"{search_query}, {country_option}" if country_option != "Global / Other" else search_query
                loc_data = geolocator.geocode(final_q, timeout=5)
                if loc_data:
                    st.session_state.lat = loc_data.latitude
                    st.session_state.lon = loc_data.longitude
                    st.session_state.resolved_address = loc_data.address
                    st.session_state.engine_active = True
                else:
                    st.sidebar.error("Location not found. Please try a different query.")
            except Exception:
                st.sidebar.warning("Geocoding service busy. Click search again.")
else:
    default_lat = float(st.session_state.lat) if st.session_state.lat else 19.0760
    default_lon = float(st.session_state.lon) if st.session_state.lon else 72.8777
    coord_lat = st.sidebar.number_input("Latitude:", value=default_lat, format="%.4f")
    coord_lon = st.sidebar.number_input("Longitude:", value=default_lon, format="%.4f")
    if st.sidebar.button("Apply Coordinates", use_container_width=True):
        st.session_state.lat = coord_lat
        st.session_state.lon = coord_lon
        resolved_by_coords = True
        st.session_state.engine_active = True

# Process Geolocation Reverse Addresses safely
if st.session_state.engine_active and not st.session_state.resolved_address:
    try:
        geolocator = Nominatim(user_agent="canopy_rx_platform_engine")
        resolved_loc = geolocator.reverse(f"{st.session_state.lat}, {st.session_state.lon}", timeout=3)
        st.session_state.resolved_address = resolved_loc.address if resolved_loc else f"Coordinates: {st.session_state.lat}, {st.session_state.lon}"
    except Exception:
        st.session_state.resolved_address = f"Coordinates: {st.session_state.lat}, {st.session_state.lon}"

# --- 6. MAIN CONTENT RENDERING LAYER ---
if st.session_state.engine_active and st.session_state.lat and st.session_state.lon:
    env_metrics = fetch_environmental_data(st.session_state.lat, st.session_state.lon)
    
    st.markdown(f"### 📍 Target Geo-Analysis: `{st.session_state.resolved_address}`")
    st.write(f"Coordinates processed: `{st.session_state.lat:.4f}, {st.session_state.lon:.4f}`")

    # =========================================================================
    # 🌍 TIER 1: FREE PUBLIC TRAVEL & BIO-CARE ADVICE
    # =========================================================================
    st.markdown("### <span class='free-badge'>FREE PUBLIC ACCESS</span> ✈️ Eco-Travel & Bio-Care Advisory", unsafe_allow_html=True)
    
    col_skincare, col_haircare, col_travel = st.columns(3)
    with col_skincare:
        st.markdown("#### 🧴 Bio-Adaptive Skincare")
        if env_metrics["uv"] >= 6.0:
            st.write("⚠️ **High UV Exposure:** Heavy solar index present. Pack Mineral-based SPF 50+ to protect your skin barrier.")
        else:
            st.write("☀️ **Mild Solar Index:** Standard SPF 30+ moisturizer covers daytime spans safely.")
        if env_metrics["humidity"] >= 65.0:
            st.write("💧 **High Air Humidity:** Use oil-free gel lotions to prevent sweat pores from building heat rash blocks.")
        else:
            st.write("🌵 **Arid Conditions:** Focus heavily on barrier moisture recovery with rich creams.")

    with col_haircare:
        st.markdown("#### 💇 Hair & Scalp Shielding")
        if env_metrics["pm25"] > 25.0:
            st.write("💨 **Anti-Pollution Plan:** Micro-particles coat individual hair cuticles here. Wear protective headwear or apply defensive leave-in serums.")
        else:
            st.write("🍃 **Clean Air Canopy:** Low particle pressure; minimal toxic particulate deposition onto open cuticles.")

    with col_travel:
        st.markdown("#### 🎒 Eco-Packing Matrix")
        packing_list = ["♻️ Hydro-flask Water Flask"]
        if env_metrics["uv"] >= 5.0:
            packing_list.extend(["🕶️ UV400 Polarized Shades", "👒 Wide Brim Summer Hat"])
        if env_metrics["pm25"] >= 35.0:
            packing_list.append("😷 High-filtration N95 Mask")
        for item in packing_list:
            st.write(f"- {item}")

    # =========================================================================
    # 💎 TIER 2: PREMIUM SUBSCRIPTION MANAGEMENT
    # =========================================================================
    st.write("---")
    st.markdown("### 🔬 Clinical Spatial Medicine & Occupational Pathology Engine")

    if st.session_state.user_tier == "Premium":
        st.markdown("<span class='premium-badge'>👑 PREMIUM PATIENT CONSOLE ACTIVE</span>", unsafe_allow_html=True)
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            pre_existing = st.selectbox("Select Active Pathological Concern:", ["None", "Bronchial Asthma & Hyper-Reactivity", "Atopic Dermatitis / Eczema"])
        with p_col2:
            occupation = st.selectbox("Primary Workplace Profile:", ["Office Worker (HVAC Air)", "Construction Site / Outdoor Laborer", "Chemical / Manufacturing Facility"])

        if st.button("Generate My Dynamic Clinical Prescription Plan", type="primary"):
            st.markdown("#### 📋 Custom Personalized Spatial Defense Prescription")
            st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
            st.markdown("##### 💼 Workspace Stressor Evaluation")
            if occupation == "Construction Site / Outdoor Laborer":
                st.write("⚠️ **High Particulate Threat:** Your environment places you in direct path of heavy abrasive particulate dust or silica elements.")
            elif occupation == "Chemical / Manufacturing Facility":
                st.write("☣️ **Chemical Inhalation Risk:** Vulnerable to vapor components or high structural manufacturing chemical exposure.")
            else:
                st.write("🏢 **Recirculated Air Profile:** Enclosed climate profile. Focus heavily on managing internal ambient dust allergens.")
            st.markdown("</div>", unsafe_allow_html=True)

            if pre_existing != "None":
                st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
                st.markdown(f"##### 🩺 Specific Disease Protection Protocol: **{pre_existing}**")
                if pre_existing == "Bronchial Asthma & Hyper-Reactivity":
                    st.write(f"🎯 **Airway Inflammation Management Strategy:**")
                    st.markdown(f"<div class='prescription-item'><strong>1. Active Local Tracking:</strong> Local PM2.5 reads `{env_metrics['pm25']} µg/m³`. Reduce high outdoor respiratory workloads during peak daylight.</div>", unsafe_allow_html=True)
                    st.markdown("<div class='prescription-item'><strong>2. Specific Micro-Climate Target:</strong> Maintain interior sleeping spaces at 45%-55% humidity to balance mucosal linings.</div>", unsafe_allow_html=True)
                elif pre_existing == "Atopic Dermatitis / Eczema":
                    st.write("🎯 **Skin Barrier Remediation & Hydration Strategy:**")
                    st.markdown(f"<div class='prescription-item'><strong>1. Contact Protection:</strong> Apply an antioxidant shield layer before entering outdoor high-particulate areas to block soot setting on compromised skin.</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='premium-lock-box'>
            <h4>🔒 Personalized Clinical Diagnostic Reports are Locked</h4>
            <p>Your current profile is using public access. Upgrade to unlock occupational exposure overrides, pre-existing pathological mapping, and dynamic prescription configurations.</p>
            <strong style='color: #d97706;'>⭐ Access CanopyRx Premium Medical Matrix for $9.99/mo</strong>
        </div>
        """, unsafe_allow_html=True)

    # =========================================================================
    # 📊 REFERENCE SENSORS METRICS EXPLORE
    # =========================================================================
    st.write("---")
    st.markdown("### 🔬 Scientific Environmental Metrics & Decoded Reference Baselines")

    tab_particulates, tab_gases = st.tabs(["🌪️ Particulates & Dust", "💨 Gaseous Elements"])
    with tab_particulates:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.metric("Fine Particulate Matter (PM2.5)", f"{env_metrics['pm25']} µg/m³")
            st.progress(min(1.0, env_metrics["pm25"] / 100.0))
            with st.expander("📝 Deconstruct PM2.5 & Normal Values"):
                st.markdown("""
                * **What it means:** Microscopic airborne dust particles smaller than 2.5 micrometers.
                * **Normal/Healthy Values:** <span class="normal-value-badge">WHO Safety Guideline: 24-hr average below 15 µg/m³</span>
                """, unsafe_allow_html=True)
        with col_p2:
            st.metric("Coarse Particulate Matter (PM10)", f"{env_metrics['pm10']} µg/m³")
            st.progress(min(1.0, env_metrics["pm10"] / 150.0))
            with st.expander("📝 Deconstruct PM10 & Normal Values"):
                st.markdown("""
                * **What it means:** Coarser ash, soil dust, and pollen tracking between 2.5 and 10 micrometers.
                * **Normal/Healthy Values:** <span class="normal-value-badge">WHO Safety Guideline: 24-hr average below 45 µg/m³</span>
                """, unsafe_allow_html=True)

    with tab_gases:
        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
            st.metric("Nitrogen Dioxide (NO₂)", f"{env_metrics['no2']} µg/m³")
            with st.expander("📝 Deconstruct NO₂"):
                st.markdown("""
                * **What it means:** Gas resulting from heavy vehicle exhaust and urban fossil fuel burning.
                * **Normal/Healthy Values:** <span class="normal-value-badge">WHO Guideline: Below 25 µg/m³ daily average</span>
                """, unsafe_allow_html=True)
        with col_g2:
            st.metric("Carbon Monoxide (CO)", f"{env_metrics['co']} µg/m³")
            with st.expander("📝 Deconstruct CO"):
                st.markdown("""
                * **What it means:** Odorless gas from engine combustion.
                * **Normal/Healthy Values:** <span class="normal-value-badge">Safe Threshold: Below 4000 µg/m³ daily average</span>
                """, unsafe_allow_html=True)
        with col_g3:
            st.metric("Ozone (O₃)", f"{env_metrics['o3']} µg/m³")
            with st.expander("📝 Deconstruct Ozone"):
                st.markdown("""
                * **What it means:** Smog cooked by solar light interacting with exhaust emissions.
                * **Normal/Healthy Values:** <span class="normal-value-badge">Safe Threshold: Below 100 µg/m³ over 8 hours</span>
                """, unsafe_allow_html=True)

    # --- 7. INTERACTIVE LOCATION MAP ---
    st.write("---")
    m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=13)
    folium.Circle(location=[st.session_state.lat, st.session_state.lon], radius=800, color="teal", fill=True, fill_opacity=0.1).add_to(m)
    folium.Marker([st.session_state.lat, st.session_state.lon], popup="Target Scan Center").add_to(m)
    st_folium(m, width=900, height=350, key="canopy_rx_map_layer")

else:
    st.info("👈 Set your target location coordinates or use manual inputs on the left side to get started.")