import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# Page Configuration - Deep Medical-Teal Theme
st.set_page_config(
    page_title="CanopyRx - Environmental Medicine & Personal Care", 
    page_icon="🩺", 
    layout="wide"
)

# STRICTOR CSS override to force-disable browser/Streamlit red warning outlines and style custom cards
st.markdown("""
<style>
    div[data-baseweb="input"] {
        border-color: #e0e0e0 !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #0d8a72 !important;
        box-shadow: 0 0 4px rgba(13, 138, 114, 0.25) !important;
    }
    input:invalid, input:-moz-ui-invalid {
        box-shadow: none !important;
        border-color: #e0e0e0 !important;
    }
    .stTextInput>div>div>input {
        border-color: #e0e0e0 !important;
        box-shadow: none !important;
    }
    .stTextInput>div>div>input:focus {
        border-color: #0d8a72 !important;
        box-shadow: 0 0 4px rgba(13, 138, 114, 0.25) !important;
    }
    /* Clinical Card styling */
    .clinical-card {
        background-color: #f4f9f8;
        border-left: 5px solid #0d8a72;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 12px;
        font-size: 14px;
    }
    .targeted-card {
        background-color: #fbf8f3;
        border-left: 5px solid #d97706;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 15px;
    }
    /* Premium Styling */
    .premium-unlocked {
        background: linear-gradient(135deg, #fbf7f0 0%, #f4eae1 100%);
        border: 1px solid #d4af37;
        border-left: 6px solid #d4af37;
        padding: 20px;
        border-radius: 8px;
        margin-top: 15px;
    }
    .premium-badge {
        background-color: #d4af37;
        color: white;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: bold;
        border-radius: 3px;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State Safely
if "lat" not in st.session_state or st.session_state.lat is None:
    st.session_state.lat = 19.0760  # Default to Mumbai Latitude
if "lon" not in st.session_state or st.session_state.lon is None:
    st.session_state.lon = 72.8777  # Default to Mumbai Longitude
if "last_lat" not in st.session_state:
    st.session_state.last_lat = 19.0760
if "last_lon" not in st.session_state:
    st.session_state.last_lon = 72.8777
if "resolved_address" not in st.session_state:
    st.session_state.resolved_address = "Mumbai, Maharashtra, India"
if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "last_country" not in st.session_state:
    st.session_state.last_country = ""
if "engine_active" not in st.session_state:
    st.session_state.engine_active = False
if "premium_subscribed" not in st.session_state:
    st.session_state.premium_subscribed = False

# Function triggers
def activate_engine():
    st.session_state.engine_active = True

def reset_engine():
    st.session_state.engine_active = False

def unlock_premium():
    st.session_state.premium_subscribed = True

def lock_premium():
    st.session_state.premium_subscribed = False


# ==========================================
# 🗺️ SIDEBAR NAVIGATION (THE PAGE ROUTER)
# ==========================================
st.sidebar.markdown("# 🩺 CanopyRx Suite")
app_mode = st.sidebar.selectbox(
    "Select Portal Module:",
    ["🌍 CanopyRx Spatial Engine", "✈️ Travel Rx Planner", "🧴 Skin & Hair Rx"]
)
st.sidebar.write("---")


# ==========================================
# 📡 CENTRALIZED REUSABLE GEOPROCESSING & API ENGINE
# ==========================================
API_KEY = "1a7d7e605314430bb7b81210261707"  # Your WeatherAPI Key

def fetch_environmental_data(latitude, longitude):
    url = "https://api.weatherapi.com/v1/current.json"
    params = {"key": API_KEY, "q": f"{latitude},{longitude}", "aqi": "yes"}
    try:
        res = requests.get(url, params=params, timeout=8)
        if res.status_code == 200:
            w_data = res.json()
            curr = w_data["current"]
            aqi = curr.get("air_quality", {})
            return {
                "temp": curr["temp_c"],
                "humidity": curr["humidity"],
                "uv": curr.get("uv", 0.0), # Default to float
                "wind": curr.get("wind_kph", 10.0),
                "pm25": aqi.get("pm2_5", 25.0),
                "pm10": aqi.get("pm10", 40.0),
                "no2": aqi.get("no2", 15.0),
                "co": aqi.get("co", 400.0),
                "so2": aqi.get("so2", 5.0),
                "o3": aqi.get("o3", 35.0),
                "success": True
            }
    except Exception:
        pass
    # Baseline fallback values
    return {
        "temp": 28.0, "humidity": 60.0, "uv": 5.0, "wind": 12.0,
        "pm25": 25.0, "pm10": 40.0, "no2": 12.0, "co": 350.0,
        "so2": 4.0, "o3": 30.0, "success": False
    }

# Geocoder Helper (Supports full global lookups including remote locations)
def geocode_location(query, country=None):
    try:
        geolocator = Nominatim(user_agent="canopyrx_clinical_environmental_engine_v5")
        if country and country != "Global / Other" and country not in query:
            fq = f"{query}, {country}"
        else:
            fq = query
        loc = geolocator.geocode(fq, timeout=10)
        if loc:
            return loc.latitude, loc.longitude, loc.address
    except Exception:
        pass
    return None, None, None


# ==========================================
# PAGE 1: 🌍 CANOPYRX SPATIAL ENGINE
# ==========================================
if app_mode == "🌍 CanopyRx Spatial Engine":
    st.sidebar.markdown("### 📋 Diagnostic Inputs")
    input_mode = st.sidebar.radio("Location Input:", ["Search Address / Landmark", "Direct Coordinates"], on_change=reset_engine)
    resolved_by_coords = False

    if input_mode == "Search Address / Landmark":
        country_option = st.sidebar.selectbox("Region / Country:", ["India", "United States", "United Kingdom", "Indonesia", "Philippines", "Global / Other"], on_change=reset_engine)
        search_query = st.sidebar.text_input("Enter City, Pincode, or Building Name:", placeholder="e.g., Central Park NY...", on_change=reset_engine)

        if search_query and (search_query != st.session_state.last_query or country_option != st.session_state.last_country):
            with st.sidebar.spinner("Resolving location details..."):
                lat, lon, addr = geocode_location(search_query, country_option)
                if lat and lon:
                    st.session_state.lat, st.session_state.lon, st.session_state.resolved_address = lat, lon, addr
                    st.session_state.last_query, st.session_state.last_country = search_query, country_option
                    st.session_state.engine_active = True
                else:
                    st.sidebar.warning("⚠️ Location not found. Try entering coordinates directly.")
    else:
        coord_lat = st.sidebar.number_input("Latitude (Y):", value=float(st.session_state.lat), format="%.6f", step=0.0001, on_change=reset_engine)
        coord_lon = st.sidebar.number_input("Longitude (X):", value=float(st.session_state.lon), format="%.6f", step=0.0001, on_change=reset_engine)
        if st.sidebar.button("Apply Coordinates", use_container_width=True):
            st.session_state.lat, st.session_state.lon = coord_lat, coord_lon
            resolved_by_coords = True
            st.session_state.engine_active = True

    # Address Fallback Sync
    if resolved_by_coords or (st.session_state.lat != st.session_state.get("last_lat") or st.session_state.lon != st.session_state.get("last_lon")):
        try:
            geolocator = Nominatim(user_agent="canopyrx_clinical_environmental_engine_v5")
            resolved_loc = geolocator.reverse(f"{st.session_state.lat}, {st.session_state.lon}", timeout=5)
            st.session_state.resolved_address = resolved_loc.address if resolved_loc else f"Coordinates: {st.session_state.lat:.4f}, {st.session_state.lon:.4f}"
        except Exception:
            st.session_state.resolved_address = f"Coordinates: {st.session_state.lat:.4f}, {st.session_state.lon:.4f}"
        st.session_state.last_lat, st.session_state.last_lon = st.session_state.lat, st.session_state.lon

    clinical_profile = st.sidebar.selectbox("Select Medical Profile (Optional):", ["None (General Overview)", "Bronchial Asthma / COPD", "Atopic Dermatitis & Eczema", "Allergic Rhinitis / Sinusitis", "Cardiovascular Sensitivity"])
    diagnostic_radius = st.sidebar.slider("Analysis Radius (meters):", min_value=50, max_value=5000, value=400, step=50)
    st.sidebar.button("Recalculate Environmental Report", type="primary", on_click=activate_engine, use_container_width=True)
    st.sidebar.info(f"📍 **Target Coordinates:**\nLat: `{st.session_state.lat:.6f}`\nLon: `{st.session_state.lon:.6f}`")

    # App Main Frame
    st.markdown("# 🩺 CanopyRx: Spatial Diagnostic Framework")
    st.markdown("##### *Mapping urban micro-climate exposures and ecological footprints to localized pathology risks.*")
    st.write("---")

    if st.session_state.engine_active:
        env = fetch_environmental_data(st.session_state.lat, st.session_state.lon)
        
        # Calculate scores
        thermal_loading = max(0.0, env["temp"] - 22.0)
        humidity_factor = max(0.1, env["humidity"] / 100.0)
        pollution_load = min(100.0, (env["pm25"] + env["pm10"]) / 2.0)
        calculated_canopy = 45.0 - (pollution_load * 0.25) - (thermal_loading * 0.4) + (humidity_factor * 10.0)
        canopy_coverage = round(min(85.0, max(4.0, calculated_canopy)), 1)
        ndvi_estimate = round(0.08 + (canopy_coverage / 100.0) * 0.78, 2)
        acoustic_noise = round(min(88.0, max(35.0, 45.0 + (min(60.0, env["no2"]) * 0.4) + (min(1000.0, env["co"]) * 0.02))), 1)
        light_pollution = int(min(9, max(1, round(2.0 + (min(80.0, env["no2"]) * 0.08)))))
        carbon_offset_value = round(canopy_coverage * 1.25, 2)
        climate_zone = "Tropical" if abs(st.session_state.lat) <= 23.5 else "Subtropical" if abs(st.session_state.lat) <= 35.0 else "Temperate" if abs(st.session_state.lat) <= 60.0 else "Polar"
        vapor_pressure = (env["humidity"] / 100.0) * 6.105 * (2.71828 ** ((17.27 * env["temp"]) / (237.7 + env["temp"])))
        apparent_temp = env["temp"] + 0.33 * vapor_pressure - 4.0

        st.markdown(f"### 📊 Clinical Spatial Assessment: `{st.session_state.resolved_address}`")
        
        # Column Metrics with Normal Values & Simple Impact Explanations
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric(
                "🌳 Zone Canopy Coverage", 
                f"{canopy_coverage}%", 
                f"NDVI Vector: {ndvi_estimate}"
            )
            st.markdown("**[Normal Target: >30%]**  \n*Impact:* Measures local greenery. More trees cool down neighborhoods, clean toxic particles from air currents, and reduce mental stress.")
            
        with m_col2:
            st.metric(
                "🌡️ Apparent Heat Index", 
                f"{round(apparent_temp, 1)}°C", 
                f"Actual Temp: {env['temp']}°C"
            )
            st.markdown("**[Normal Comfort: 18°C - 27°C]**  \n*Impact:* How hot it actually feels to the human body. High readings indicate heat-stress hazards that place heavy strain on the heart.")
            
        with m_col3:
            st.metric(
                "💨 Live PM2.5 Level", 
                f"{round(env['pm25'], 1)} µg/m³", 
                f"Live PM10: {round(env['pm10'], 1)} µg/m³"
            )
            st.markdown("**[Normal/Safe Limit: <15 µg/m³]**  \n*Impact:* Invisible, ultra-fine combustion dust that bypasses lung defense systems, entering blood and provoking deep tissue inflammation.")

        st.write("---")

        # Map and Details Block
        col_map, col_details = st.columns([3, 2])
        zoom_val = 18 if diagnostic_radius <= 150 else 16 if diagnostic_radius <= 500 else 14 if diagnostic_radius <= 1500 else 11
        grade_color = "green" if env["pm25"] < 15 else "orange" if env["pm25"] < 35 else "red"

        with col_map:
            st.markdown("#### 🗺️ Interactive Spatial Boundary Map")
            m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=zoom_val, tiles="OpenStreetMap")
            folium.Circle(location=[st.session_state.lat, st.session_state.lon], radius=diagnostic_radius, color=grade_color, fill=True, fill_color=grade_color, fill_opacity=0.12).add_to(m)
            folium.Marker([st.session_state.lat, st.session_state.lon], icon=folium.Icon(color="darkblue")).add_to(m)
            map_data = st_folium(m, width=700, height=380, key="clinical_map")
            
            if map_data and map_data.get("last_clicked"):
                click_lat = map_data["last_clicked"]["lat"]
                click_lon = map_data["last_clicked"]["lng"]
                if round(click_lat, 5) != round(st.session_state.lat, 5) or round(click_lon, 5) != round(st.session_state.lon, 5):
                    st.session_state.lat, st.session_state.lon = click_lat, click_lon
                    st.session_state.engine_active = True
                    st.rerun()

        with col_details:
            st.markdown("#### 🔬 Baseline Pathological Risk Profiling")
            if env["pm25"] > 30.0 or env["no2"] > 25.0:
                st.markdown('<div class="clinical-card"><strong>🫁 Bronchial Vulnerability: High Risk</strong><br>Elevated PM2.5 particulates trigger respiratory hyper-reactivity, worsening bronchial asthma.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="clinical-card" style="border-left-color: #2e7d32;"><strong>🫁 Bronchial Vulnerability: Stable</strong><br>Low particulate concentrations minimize mucosal inflammation.</div>', unsafe_allow_html=True)

            if apparent_temp > 35.0:
                st.markdown('<div class="clinical-card"><strong>🩺 Cardiorespiratory & Dermatological Stress: High Risk</strong><br>High apparent temperatures amplify cardiovascular workload and inflammatory skin flare-ups.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="clinical-card" style="border-left-color: #2e7d32;"><strong>🩺 Thermal Stress: Stable/Normal</strong><br>Comfortable thermal loading reduces immediate vascular stress.</div>', unsafe_allow_html=True)

        # Tab metrics
        st.write("---")
        t1, t2, t3 = st.tabs(["💨 Gaseous Pollutants", "🌱 Ecological & Carbon Metrics", "🔊 Sensory & Physical"])
        with t1:
            g_col1, g_col2, g_col3 = st.columns(3)
            with g_col1:
                st.metric("Nitrogen Dioxide (NO₂)", f"{round(env['no2'], 1)} µg/m³")
                st.markdown("**[Normal/Safe: <40 µg/m³]**  \n*Impact:* Corrosive traffic gas. High concentrations irritate bronchial linings and worsen allergies.")
            with g_col2:
                st.metric("Sulfur Dioxide (SO₂)", f"{round(env['so2'], 1)} µg/m³")
                st.markdown("**[Normal/Safe: <20 µg/m³]**  \n*Impact:* Heavy industrial combustion emission. Triggers respiratory spasms.")
            with g_col3:
                st.metric("Carbon Monoxide (CO)", f"{round(env['co'], 1)} µg/m³")
                st.markdown("**[Normal/Safe: <4000 µg/m³]**  \n*Impact:* Toxic car exhaust gas. Reduces oxygen delivery capacity throughout the human vascular system.")
                
        with t2:
            e_col1, e_col2 = st.columns(2)
            with e_col1:
                st.metric("Carbon Sequestration Capacity", f"{carbon_offset_value} Tons/Yr")
                st.markdown("*Impact:* The total volume of dangerous carbon emissions cleaned annually by the local leafy canopy.")
            with e_col2:
                st.metric("Normalized Vegetation Index (NDVI)", f"{ndvi_estimate}")
                st.markdown("**[Normal Target: >0.30]**  \n*Impact:* A satelite-derived score from 0 (barren concrete) to 1.0 (dense jungle) measuring active botanical surface density.")
                
        with t3:
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                st.metric("Acoustic Noise Proxy", f"{acoustic_noise} dBA")
                st.markdown("**[Normal/Safe: <55 dBA daytime, <40 dBA nighttime]**  \n*Impact:* Noise levels. Chronic noise above safe thresholds triggers adrenaline spikes, keeping your body under constant fight-or-flight stress.")
            with s_col2:
                st.metric("Night Light Pollution", f"Bortle Class {light_pollution}")
                st.markdown("**[Normal/Target: Class 1 - 4]**  \n*Impact:* Artificial light. Class 1 is absolute dark sky; Class 9 is urban glare. High values disrupt sleep hormone production.")

        # Botanical Prescriptions
        st.write("---")
        st.markdown("### 💊 Preventive Medicine: Botanical Interventions")
        pres_col1, pres_col2 = st.columns(2)
        with pres_col1:
            if climate_zone in ["Tropical", "Subtropical"]:
                st.image("https://images.unsplash.com/photo-1598902108854-10e335adac99?auto=format&fit=crop&w=600&q=80", caption="Primary Canopy Recommendation: Neem & Ashoka", use_container_width=True)
            else:
                st.image("https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=600&q=80", caption="Primary Canopy Recommendation: Silver Birch & Red Maple", use_container_width=True)
        with pres_col2:
            if apparent_temp > 32.0:
                st.image("https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=600&q=80", caption="Engineering Recommendation: Albedo Deflection Membrane", use_container_width=True)
            else:
                st.image("https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=600&q=80", caption="Engineering Recommendation: Passive Cross-Ventilation Arrays", use_container_width=True)
    
    else:
        # ==========================================
        # 🧬 NEW CLINICAL EXPLANATORY LANDING PAGE & DIRECTIONS
        # ==========================================
        st.markdown("""
        ### 🧬 Welcome to the CanopyRx Ecological Diagnostics Suite
        #### *Bridging Spatial Epidemiology, Micro-Climatology, and Clinical Wellness.*
        
        Traditional pathology assessment focuses strictly on internal biomarkers. However, modern clinical science reveals that a patient's **allostatic load** (the cumulative physical wear-and-tear of life) is deeply integrated with their immediate environmental exposures. Factors like the **micro-urban heat island effect**, **airborne xenobiotics** (PM2.5, NO₂, CO), **acoustic noise pollution**, and **canopy-deprived micro-climates** trigger sub-clinical inflammatory responses.
        
        CanopyRx processes live satelite, topographic, and atmospheric data to isolate exposure hazards. By assessing these factors, clinicians and patients can formulate precise, topical, and lifestyle interventions before symptom flare-ups occur.
        
        ---
        ### 🧭 How to Use This Portal (Step-by-Step Directions):
        1. **Choose Input Mode:** On the left-hand sidebar, select your input style. Use **Search Address / Landmark** to type any global location, or select **Direct Coordinates** to feed precise GPS coordinates into the system.
        2. **Map-Click Exploration:** Once the spatial engine is running, you can click on any building, street corner, or courtyard on the interactive map. The engine will instantly recalculate risks for that exact coordinate.
        3. **Select Your Clinical Profile:** If you suffer from underlying sensitivities (like asthma, eczema, or high blood pressure), choose your match from the **Medical Profile** dropdown menu.
        4. **Select Exposure Radius:** Adjust the slider to specify your geographic analysis boundary. Keep it small ($50\text{m} - 150\text{m}$) to analyze an individual building, or wider ($1000\text{m} - 5000\text{m}$) for general neighborhood mapping.
        5. **Recalculate:** Click the red **Recalculate Environmental Report** button to initiate spatial queries and obtain live, customized health plans.
        """)
        
        welcome_col1, welcome_col2 = st.columns(2)
        with welcome_col1:
            st.image("https://images.unsplash.com/photo-1502082553048-f009c37129b9?auto=format&fit=crop&w=800&q=80", caption="Urban Micro-Climate Boundary Modeling", use_container_width=True)
        with welcome_col2:
            st.markdown("""
            #### 📊 Diagnostic Baseline Framework:
            * **Green Canopy Assessment:** Evaluates vegetation density to estimate active solar radiation filtering.
            * **Particulate Profiling (PM2.5 / PM10):** Measures the density of microscopic airborne solids capable of bypassing mucus defense structures.
            * **Acoustic & Light Modeling:** Gauges ambient stress levels that impact the nervous system during restorative hours.
            """)


# ==========================================
# PAGE 2: ✈️ TRAVEL RX PLANNER (UPGRADED)
# ==========================================
elif app_mode == "✈️ Travel Rx Planner":
    st.markdown("# ✈️ Travel Rx: Pre-Travel Environmental Exposure Planner")
    st.markdown("##### *Identify atmospheric and climatic deltas between your locations to safely adapt your health, skin, and respiratory routines.*")
    st.write("---")

    col_input1, col_input2 = st.columns(2)
    
    with col_input1:
        st.markdown("### 📍 Origin Location")
        origin_input_mode = st.radio("Origin Input Method:", ["Search Global City/Village", "Exact Coordinates (Lat, Lon)"], key="org_mode")
        
        if origin_input_mode == "Search Global City/Village":
            origin_search = st.text_input("Enter Origin Location (Accepts any remote city globally):", value="Mumbai", key="orig_search")
            orig_lat, orig_lon = None, None
        else:
            orig_lat = st.number_input("Origin Latitude:", value=19.0760, format="%.6f", key="orig_lat")
            orig_lon = st.number_input("Origin Longitude:", value=72.8777, format="%.6f", key="orig_lon")

    with col_input2:
        st.markdown("### 🛫 Destination Location")
        dest_input_mode = st.radio("Destination Input Method:", ["Search Global City/Village", "Exact Coordinates (Lat, Lon)"], key="dest_mode")
        
        if dest_input_mode == "Search Global City/Village":
            dest_search = st.text_input("Enter Destination Location (Accepts any remote city globally):", value="Reykjavik", key="dest_search")
            dest_lat, dest_lon = None, None
        else:
            dest_lat = st.number_input("Destination Latitude:", value=64.1466, format="%.6f", key="dest_lat")
            dest_lon = st.number_input("Destination Longitude:", value=-21.9426, format="%.6f", key="dest_lon")

    if st.button("Generate Travel Exposure Delta", type="primary", use_container_width=True):
        with st.spinner("Retrieving global geo-spatial atmospherics..."):
            
            # Resolve Origin
            if origin_input_mode == "Search Global City/Village":
                lat_o, lon_o, addr_o = geocode_location(origin_search)
            else:
                lat_o, lon_o, addr_o = orig_lat, orig_lon, f"Custom Coordinates ({orig_lat:.4f}, {orig_lon:.4f})"
                
            # Resolve Destination
            if dest_input_mode == "Search Global City/Village":
                lat_d, lon_d, addr_d = geocode_location(dest_search)
            else:
                lat_d, lon_d, addr_d = dest_lat, dest_lon, f"Custom Coordinates ({dest_lat:.4f}, {dest_lon:.4f})"

            if lat_o is not None and lat_d is not None:
                data_o = fetch_environmental_data(lat_o, lon_o)
                data_d = fetch_environmental_data(lat_d, lon_d)

                # Show Delta Table
                st.markdown(f"### 📊 Exposure Forecast: `{addr_o.split(',')[0]}` ➔ `{addr_d.split(',')[0]}`")
                
                temp_delta = data_d["temp"] - data_o["temp"]
                uv_delta = data_d["uv"] - data_o["uv"]
                aqi_delta = data_d["pm25"] - data_o["pm25"]

                st.markdown("#### Key Exposure Differences")
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                metric_col1.metric("Temperature Shift", f"{round(temp_delta, 1)}°C", f"Dest: {data_d['temp']}°C vs Orig: {data_o['temp']}°C", delta_color="inverse")
                metric_col2.metric("UV Radiation Shift", f"{round(uv_delta, 1)} UV Index", f"Dest: {data_d['uv']} vs Orig: {data_o['uv']}", delta_color="inverse")
                metric_col3.metric("Fine Particulate (PM2.5) Shift", f"{round(aqi_delta, 1)} µg/m³", f"Dest: {data_d['pm25']} vs Orig: {data_o['pm25']}", delta_color="inverse")

                st.write("---")

                # Travel Warnings
                st.markdown("#### 🚨 Travel Pathology Exposure Indicators")
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    if temp_delta < -8:
                        st.warning("⚠️ **Cold Dry Flare Risk:** Rapid temperature drops dry out upper respiratory mucous membranes. Packed layers and protective barrier creams are highly recommended.")
                    elif temp_delta > 8:
                        st.warning("⚠️ **Thermal Adaptation Stress:** Massive temperature increases strain cardiovascular heat dissipation pathways. Increase fluid/electrolyte intake.")
                    else:
                        st.success("✅ **Mild Thermal Shift:** Comfortable transition between regions. Low thermal acclimatization load.")
                with t_col2:
                    if aqi_delta > 20:
                        st.warning("⚠️ **Air Quality Degradation:** The target zone has substantially higher particulate concentrations. Pack emergency inhalers and a PM2.5-rated face mask.")
                    else:
                        st.success("✅ **Air Quality Optimization:** Your destination has clean, well-buffered air, reducing respiratory flare risks.")
            else:
                st.error("Could not resolve location coordinates. Double check your search spellings or try entering exact GPS coordinates.")


# ==========================================
# PAGE 3: 🧴 SKIN & HAIR RX (WITH DYNAMIC UV CORRECTION & NORMAL BRACKETS)
# ==========================================
elif app_mode == "🧴 Skin & Hair Rx":
    st.markdown("# 🧴 Skin & Hair Rx: Environmental Barrier Formulations")
    st.markdown("##### *Protect your physical moisture barrier from local atmospheric elements, solar radiation, and water quality indices.*")
    
    # Premium Billing Banner
    if not st.session_state.premium_subscribed:
        st.markdown("""
        <div style="background-color: #fff9db; border: 1px solid #f59f00; border-radius: 6px; padding: 15px; margin-bottom: 20px;">
            🔑 <strong>Unlock Premium Diagnostics:</strong> Upgrade to access customizable skin types, complex hair porosity profiles, precise local water hardness calculations, and advanced customized ingredient prescriptions.
        </div>
        """, unsafe_allow_html=True)
        if st.button("🌟 Upgrade to Premium Formulations (Simulation Mode)", type="secondary"):
            unlock_premium()
            st.rerun()
    else:
        st.markdown("""
        <div style="background-color: #e6fcf5; border: 1px solid #099268; border-radius: 6px; padding: 15px; margin-bottom: 20px;">
            💎 <strong>Premium Unlocked:</strong> You have full access to deep dermatological formulations and custom water quality integrations.
        </div>
        """, unsafe_allow_html=True)
        if st.button("Lock Premium Tools", type="secondary"):
            lock_premium()
            st.rerun()

    st.write("---")

    # Fetch live coordinates data for local context
    env = fetch_environmental_data(st.session_state.lat, st.session_state.lon)

    # ------------------ FREE TIER INTERFACE ------------------
    st.markdown("### 🌲 Free Tier: Local Environmental Exposure Diagnostics")
    st.write(f"Analyzing environmental elements for `{st.session_state.resolved_address}`:")

    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        st.metric("Local Relative Humidity", f"{env['humidity']}%")
        st.markdown("**[Normal Target Range: 40% - 60%]**  \n*Impact:* Low humidity sucks water out of skin; extreme high humidity clogs pores by trapping sebum.")
    with f_col2:
        st.metric("Ultraviolet (UV) Factor", f"{env['uv']} / 12")
        st.markdown("**[Normal/Safe: <3 (Low)]**  \n*Impact:* Measures DNA-damaging solar rays. UV triggers premature skin aging, wrinkles, and breaks down hair protein shields.")
    with f_col3:
        st.metric("Ambient Particulate Load (PM10)", f"{round(env['pm10'], 1)} µg/m³")
        st.markdown("**[Normal/Safe Limit: <50 µg/m³]**  \n*Impact:* Airborne soot particles that stick to face oil, clogging follicles and accelerating cellular aging.")

    # UV Dynamic Explanation (Addressing why UV might show as 0)
    if float(env["uv"]) == 0.0:
        st.info("💡 **Clinical Note on the '0' UV Index:** This reading occurs naturally because it is nighttime, or because of thick regional cloud cover or winter seasons in polar zones. Sunlight must be physically striking the atmosphere's ozone layer to generate measurable ultraviolet rays.")

    # Free general recommendations
    st.markdown("#### 🛡️ Standard Environmental Care Guidelines")
    if env["humidity"] < 40:
        st.info("💧 **Atmospheric Moisture Void:** The air is highly dehydrating. Transepidermal water loss (TEWL) is accelerated. Apply occlusive-rich barrier moisturizers to retain skin moisture.")
    elif env["humidity"] > 75:
        st.info("🥵 **High Humidity Pore Loading:** Highly saturated air traps excess sebum on skin surfaces. Use lightweight, non-comedogenic gel formulas and deep foaming cleansers.")
    else:
        st.info("✅ **Balanced Relative Humidity:** Atmospheric moisture levels are stable. Maintain a simple cleansing and hydration routine.")

    if env["uv"] >= 6:
        st.warning("☀️ **Critical Photolytic Damage Hazard:** Strong UV levels will degrade skin collagen and compromise hair proteins. Broad-spectrum SPF 50+ sunscreen and hair UV shield sprays are essential.")

    # ------------------ PREMIUM TIER INTERFACE ------------------
    if st.session_state.premium_subscribed:
        st.markdown('<hr style="border: 1px solid #d4af37;">', unsafe_allow_html=True)
        st.markdown('### 💎 <span class="premium-badge">Premium Feature</span> Deep Dermatological Synthesis', unsafe_allow_html=True)
        st.write("Construct a customized prescription by inputting specific skin and hair characteristics:")

        p_col1, p_col2 = st.columns(2)
        with p_col1:
            st.markdown("#### Skin Profile")
            skin_type = st.selectbox("Select Skin Type:", ["Dry / Flaky", "Oily / Acne-Prone", "Combination", "Highly Sensitive / Rosacea"])
            active_skin_concern = st.multiselect("Active Issues:", ["Frequent Flaring", "Clogged Pores / Blackheads", "Dullness", "Sun Damage"])

        with p_col2:
            st.markdown("#### Hair & Scalp Profile")
            hair_porosity = st.selectbox("Hair Porosity Level:", ["Low (Water Repellent / Build-up)", "Medium (Healthy)", "High (Highly Damaged / Quick Dry)"])
            water_hardness = st.select_slider("Expected Water Hardness at Location (ppm):", options=[50, 100, 150, 200, 300, 400], value=150, help="Hard water (>150 ppm) minerals bind to hair, building up scaling and blocking moisture absorption.")

        # Real-time Premium Prescription Engine
        if st.button("Generate Bespoke Care Formulation", type="primary"):
            st.markdown('<div class="premium-unlocked">', unsafe_allow_html=True)
            st.markdown("### 🧪 Premium Skin & Hair Prescription")
            st.write(f"Calculated for `{st.session_state.resolved_address}` taking into account a **{skin_type}** skin profile, **{hair_porosity}** porosity hair, and **{water_hardness} ppm** water hardness:")

            # Skin Prescription Logic
            st.markdown("#### 🧴 Personalized Topical Barrier Formulation")
            if skin_type == "Dry / Flaky" or env["humidity"] < 40:
                st.write("**Base Formulation Recommendation:** Emulsion Rich Cream")
                st.write("**Key Actives to Incorporate:**")
                st.write("* *Ceramides (NP, AP, EOP):* Essential lipid block replenishment to seal the compromised epidermal barrier.")
                st.write("* *Glycerin & Hyaluronic Acid:* Humectants to extract ambient humidity and bind moisture to skin.")
            elif skin_type == "Oily / Acne-Prone" or env["humidity"] > 75:
                st.write("**Base Formulation Recommendation:** Lightweight Aquagel")
                st.write("**Key Actives to Incorporate:**")
                st.write("* *Niacinamide (3-5%):* Regulates local sebum excretion rates and builds a chemical shield against micro-dust.")
                st.write("* *Salicylic Acid (BHA):* Lipophilic acid that exfoliates deeply inside the pore canal.")
            else:
                st.write("**Base Formulation Recommendation:** Balanced Moisture Lotion with Squalane.")

            # Hair Prescription Logic
            st.markdown("#### 💇 Personalized Hair & Scalp Barrier Formulation")
            if water_hardness > 150:
                st.warning(f"⚠️ **Water Hardness Alert ({water_hardness} ppm):** Mineral buildup (calcium/magnesium scaling) will cause hair to feel brittle and straw-like.")
                st.write("*   **Immediate Measure:** Use a Chelating Shampoo containing EDTA to lift calcium crusting.")
            
            if hair_porosity == "Low (Water Repellent / Build-up)":
                st.write("*   **Moisture Strategy:** Avoid heavy oils/silicones. Use lightweight, warm humectants (e.g., Honey, Aloe Vera) to swell the tightly bound cuticle layer and deposit deep hydration.")
            elif hair_porosity == "High (Highly Damaged / Quick Dry)":
                st.write("*   **Moisture Strategy:** High-porosity hair leaks moisture rapidly. Utilize rich, occlusive plant lipids (Shea Butter, Argan Oil) and hydrolyzed proteins to patch-fill structural hair shaft gaps.")
            else:
                st.write("*   **Moisture Strategy:** Standard balance maintenance using light argan seed extract.")

            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.write("---")
        st.markdown("#### 🔒 Premium Diagnostic Features Locked")
        st.caption("Subscribe or click the upgrade button above to unlock the premium section and access complete skin/hair formulations tailored to your profile.")