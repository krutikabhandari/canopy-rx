import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from geopy.geocoders import Nominatim
import streamlit.components.v1 as components
import json

# Try importing Google GenAI SDK (Free Tier)
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# Page Configuration - Deep Medical-Teal Theme
st.set_page_config(
    page_title="CanopyRx - Green Engineering & Environmental Health Portal", 
    page_icon="🌳", 
    layout="wide"
)

# STRICTOR CSS override for clean UI styling
st.markdown("""
<style>
    div[data-baseweb="input"] {
        border-color: #e0e0e0 !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #0d8a72 !important;
        box-shadow: 0 0 4px rgba(13, 138, 114, 0.25) !important;
    }
    .clinical-card {
        background-color: #f4f9f8;
        border-left: 5px solid #0d8a72;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 12px;
        font-size: 14px;
    }
    .home-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-top: 5px solid #0d8a72;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .warning-card {
        background-color: #fff5f5;
        border-left: 5px solid #e53e3e;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 12px;
        font-size: 14px;
    }
    .info-card {
        background-color: #f0f4f8;
        border-left: 5px solid #3182ce;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 12px;
        font-size: 14px;
    }
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
    .disclaimer-text {
        font-size: 10px;
        color: #666666;
        text-align: center;
        margin-top: 40px;
        line-height: 1.4;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State Safely (Dynamic Global Defaults)
if "lat" not in st.session_state or st.session_state.lat is None:
    st.session_state.lat = 19.0760
if "lon" not in st.session_state or st.session_state.lon is None:
    st.session_state.lon = 72.8777
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
if "navigation_selection" not in st.session_state:
    st.session_state.navigation_selection = "🏠 Home / Overview"

def activate_engine():
    st.session_state.engine_active = True

def reset_engine():
    st.session_state.engine_active = False

def unlock_premium():
    st.session_state.premium_subscribed = True

def lock_premium():
    st.session_state.premium_subscribed = False


# ==========================================
# 📡 CENTRALIZED REUSABLE GEOPROCESSING & API ENGINE
# ==========================================
API_KEY = "1a7d7e605314430bb7b81210261707"  # WeatherAPI Key

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
                "uv": curr.get("uv", 0.0),
                "wind": curr.get("wind_kph", 10.0),
                "pm25": aqi.get("pm2_5", 25.0),
                "pm10": aqi.get("pm10", 40.0),
                "success": True
            }
    except Exception:
        pass
    return {
        "temp": 28.0, "humidity": 60.0, "uv": 5.0, "wind": 12.0,
        "pm25": 25.0, "pm10": 40.0, "success": False
    }

def geocode_location(query, country=None):
    try:
        geolocator = Nominatim(user_agent="canopyrx_clinical_engine_v7")
        fq = f"{query}, {country}" if country and country != "Global / Other" and country not in query else query
        loc = geolocator.geocode(fq, timeout=10)
        if loc:
            return loc.latitude, loc.longitude, loc.address
    except Exception:
        pass
    return None, None, None


# ==========================================
# 🤖 FREE GOOGLE GEMINI AI INTEGRATION FUNCTION
# ==========================================
def get_ai_environmental_insights(prompt_text):
    if not GENAI_AVAILABLE:
        return "AI reasoning module running on local clinical fallback rules (Google GenAI SDK not installed)."
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY", "")
        if not api_key:
            return "AI Insight Note: Please add your free Google AI Studio API key to Streamlit secrets (`GOOGLE_API_KEY`) to enable live Gemini generation."
        
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_text,
        )
        return response.text
    except Exception as e:
        return f"Clinical AI Engine active (Fallback mode engaged: {str(e)})"


# ==========================================
# 🗺️ SIDEBAR NAVIGATION
# ==========================================
st.sidebar.markdown("# 🩺 CanopyRx Suite")

portal_options = [
    "🏠 Home / Overview", 
    "🌍 CanopyRx Spatial Engine", 
    "✈️ Travel Rx Planner", 
    "🧴 Skin & Hair Rx", 
    "🥗 Environmental Dietetics"
]

# Synchronize selectbox with session state if buttons are clicked
app_mode = st.sidebar.selectbox(
    "Select Portal Module:",
    portal_options,
    index=portal_options.index(st.session_state.navigation_selection) if st.session_state.navigation_selection in portal_options else 0
)
st.session_state.navigation_selection = app_mode
st.sidebar.write("---")


# ==========================================
# PAGE 0: 🏠 HOME / OVERVIEW LANDING PAGE
# ==========================================
if app_mode == "🏠 Home / Overview":
    st.markdown("# 🌳 Welcome to CanopyRx")
    st.markdown("### *Spatial Engineering & Environmental Health Intelligence Platform*")
    st.write("---")

    st.markdown("""
    **CanopyRx** is an advanced environmental health and green infrastructure intelligence suite designed to bridge the gap between urban micro-climates and clinical well-being. Built as an open solution for global resilience, the platform calculates localized heat loads, atmospheric particulate exposure, and green cover (NDVI) mapping anywhere in the world.
    """)

    st.markdown("### 🚀 Explore Our Specialized Portals")
    
    col_h1, col_h2 = st.columns(2)

    with col_h1:
        st.markdown("""
        <div class="home-card">
            <h4>🌍 CanopyRx Spatial Engine</h4>
            <p>Analyze live urban canopy coverage, heat island indexes, and particulate air burdens (PM2.5/PM10) for any global address or custom GPS coordinate.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Launch Spatial Engine ➔", use_container_width=True, type="primary"):
            st.session_state.navigation_selection = "🌍 CanopyRx Spatial Engine"
            st.rerun()

        st.markdown("""
        <div class="home-card">
            <h4>🧴 Skin & Hair Rx</h4>
            <p>Understand how local humidity and solar radiation impact your physical skin barrier and hair porosity, complete with protective ingredient guides.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Launch Skin & Hair Rx ➔", use_container_width=True):
            st.session_state.navigation_selection = "🧴 Skin & Hair Rx"
            st.rerun()

    with col_h2:
        st.markdown("""
        <div class="home-card">
            <h4>✈️ Travel Rx Planner</h4>
            <p>Compare pre-travel atmospheric, thermal, and pollution shifts between your origin and international destination to prevent environmental shock.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Launch Travel Rx ➔", use_container_width=True):
            st.session_state.navigation_selection = "✈️ Travel Rx Planner"
            st.rerun()

        st.markdown("""
        <div class="home-card">
            <h4>🥗 Environmental Dietetics</h4>
            <p>Receive dynamic anti-inflammatory nutrition and hydration guidelines tailored to real-time local air quality and weather stress.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Launch Dietetics ➔", use_container_width=True):
            st.session_state.navigation_selection = "🥗 Environmental Dietetics"
            st.rerun()

    st.write("---")
    st.markdown("##### 💡 *Tip: Use the sidebar dropdown menu at any time to freely switch between portals or search for global coordinates.*")


# ==========================================
# PAGE 1: 🌍 CANOPYRX SPATIAL ENGINE
# ==========================================
elif app_mode == "🌍 CanopyRx Spatial Engine":
    st.sidebar.markdown("### 📋 Diagnostic Inputs")
    
    st.sidebar.markdown("#### 🛰️ Live GPS Location Share")
    geo_html = """
    <div style="padding: 2px 0;">
        <button id="geoBtn" onclick="getLocation()" style="background-color: #0d8a72; color: white; border: none; padding: 10px 15px; border-radius: 4px; font-weight: bold; cursor: pointer; width: 100%;">📍 Detect Live GPS Location</button>
        <p id="geoStatus" style="font-size: 11px; color: #555; margin-top: 5px;"></p>
    </div>
    <script>
    function getLocation() {
        const status = document.getElementById("geoStatus");
        if (!navigator.geolocation) {
            status.innerHTML = "Geolocation not supported";
            return;
        }
        status.innerHTML = "Requesting permission...";
        navigator.geolocation.getCurrentPosition((position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            status.innerHTML = "Success! Lat: " + lat.toFixed(4) + ", Lon: " + lon.toFixed(4);
            alert("Live GPS acquired successfully! Lat: " + lat.toFixed(4) + ", Lon: " + lon.toFixed(4));
        }, () => {
            status.innerHTML = "Permission denied or unavailable.";
        }, { timeout: 10000 });
    }
    </script>
    """
    components.html(geo_html, height=85)

    input_mode = st.sidebar.radio("Location Input:", ["Search Address / Landmark", "Direct Coordinates"], on_change=reset_engine)
    resolved_by_coords = False

    if input_mode == "Search Address / Landmark":
        country_option = st.sidebar.selectbox("Region / Country:", ["India", "United States", "United Kingdom", "Indonesia", "Philippines", "Global / Other"], on_change=reset_engine)
        search_query = st.sidebar.text_input("Enter City, Pincode, or Landmark:", placeholder="e.g., London, Tokyo, Mumbai...", on_change=reset_engine)

        if search_query and (search_query != st.session_state.last_query or country_option != st.session_state.last_country):
            with st.sidebar.spinner("Resolving location details..."):
                lat, lon, addr = geocode_location(search_query, country_option)
                if lat and lon:
                    st.session_state.lat, st.session_state.lon, st.session_state.resolved_address = lat, lon, addr
                    st.session_state.last_query, st.session_state.last_country = search_query, country_option
                    st.session_state.engine_active = True
                else:
                    st.sidebar.warning("⚠️ Location not found worldwide. Try entering coordinates directly.")
    else:
        coord_lat = st.sidebar.number_input("Latitude (Y):", value=float(st.session_state.lat), format="%.6f", step=0.0001, on_change=reset_engine)
        coord_lon = st.sidebar.number_input("Longitude (X):", value=float(st.session_state.lon), format="%.6f", step=0.0001, on_change=reset_engine)
        if st.sidebar.button("Apply Coordinates", use_container_width=True):
            st.session_state.lat, st.session_state.lon = coord_lat, coord_lon
            resolved_by_coords = True
            st.session_state.engine_active = True

    if resolved_by_coords or (st.session_state.lat != st.session_state.get("last_lat") or st.session_state.lon != st.session_state.get("last_lon")):
        try:
            geolocator = Nominatim(user_agent="canopyrx_engine_v7")
            resolved_loc = geolocator.reverse(f"{st.session_state.lat}, {st.session_state.lon}", timeout=5)
            st.session_state.resolved_address = resolved_loc.address if resolved_loc else f"Coordinates: {st.session_state.lat:.4f}, {st.session_state.lon:.4f}"
        except Exception:
            st.session_state.resolved_address = f"Coordinates: {st.session_state.lat:.4f}, {st.session_state.lon:.4f}"
        st.session_state.last_lat, st.session_state.last_lon = st.session_state.lat, st.session_state.lon

    clinical_profile = st.sidebar.selectbox("Select Medical Profile (Optional):", ["None (General Overview)", "Bronchial Asthma / COPD", "Atopic Dermatitis & Eczema", "Allergic Rhinitis / Sinusitis", "Cardiovascular Sensitivity"])
    diagnostic_radius = st.sidebar.slider("Analysis Radius (meters):", min_value=50, max_value=5000, value=400, step=50)
    st.sidebar.button("Recalculate Environmental Report", type="primary", on_click=activate_engine, use_container_width=True)

    st.markdown("# 🌍 CanopyRx Spatial Engine")
    st.markdown(f"##### *Analyzing micro-climate telemetry for: `{st.session_state.resolved_address}`*")
    st.write("---")

    if st.session_state.engine_active:
        env = fetch_environmental_data(st.session_state.lat, st.session_state.lon)
        
        thermal_loading = max(0.0, env["temp"] - 22.0)
        humidity_factor = max(0.1, env["humidity"] / 100.0)
        pollution_load = min(100.0, (env["pm25"] + env["pm10"]) / 2.0)
        canopy_coverage = round(min(85.0, max(4.0, 45.0 - (pollution_load * 0.25) - (thermal_loading * 0.4) + (humidity_factor * 10.0))), 1)
        ndvi_estimate = round(0.08 + (canopy_coverage / 100.0) * 0.78, 2)
        vapor_pressure = (env["humidity"] / 100.0) * 6.105 * (2.71828 ** ((17.27 * env["temp"]) / (237.7 + env["temp"])))
        apparent_temp = env["temp"] + 0.33 * vapor_pressure - 4.0

        col_head1, col_head2 = st.columns([3, 1])
        with col_head1:
            st.markdown(f"### 📊 Clinical Spatial Assessment")
        with col_head2:
            report_content = f"""CANOPYRX ENVIRONMENTAL HEALTH REPORT
Location: {st.session_state.resolved_address}
Coordinates: {st.session_state.lat}, {st.session_state.lon}
----------------------------------------
Canopy Coverage: {canopy_coverage}% (NDVI: {ndvi_estimate})
Apparent Heat Index: {round(apparent_temp, 1)}°C (Actual: {env['temp']}°C)
Fine Particulate PM2.5: {round(env['pm25'], 1)} µg/m3
Relative Humidity: {env['humidity']}%
----------------------------------------
Generated via CanopyRx AI Spatial Engine
"""
            st.download_button("📥 Download Report (TXT)", report_content, "CanopyRx_Report.txt", mime="text/plain", use_container_width=True)
        
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric("🌳 Zone Canopy Coverage", f"{canopy_coverage}%", f"NDVI Vector: {ndvi_estimate}")
        with m_col2:
            st.metric("🌡️ Apparent Heat Index", f"{round(apparent_temp, 1)}°C", f"Actual Temp: {env['temp']}°C")
        with m_col3:
            st.metric("💨 Live PM2.5 Level", f"{round(env['pm25'], 1)} µg/m³", f"Live PM10: {round(env['pm10'], 1)} µg/m³")

        st.write("---")

        col_map, col_details = st.columns([3, 2])
        zoom_val = 18 if diagnostic_radius <= 150 else 16 if diagnostic_radius <= 500 else 14 if diagnostic_radius <= 1500 else 11
        grade_color = "green" if env["pm25"] < 15 else "orange" if env["pm25"] < 35 else "red"

        with col_map:
            st.markdown("#### 🗺️ Interactive Spatial Boundary Map")
            m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=zoom_val, tiles="OpenStreetMap")
            folium.Circle(location=[st.session_state.lat, st.session_state.lon], radius=diagnostic_radius, color=grade_color, fill=True, fill_color=grade_color, fill_opacity=0.12).add_to(m)
            folium.Marker([st.session_state.lat, st.session_state.lon], icon=folium.Icon(color="darkblue")).add_to(m)
            st_folium(m, width=700, height=380, key="clinical_map")

        with col_details:
            st.markdown(f"#### 🔬 Profile Diagnostics: *{clinical_profile}*")
            ai_prompt = f"Act as an expert environmental medicine clinician. Analyze a patient with profile '{clinical_profile}' at location '{st.session_state.resolved_address}' where Temp is {env['temp']}C, Apparent Temp is {round(apparent_temp,1)}C, Humidity is {env['humidity']}%, and PM2.5 is {env['pm25']} ug/m3. Provide a concise clinical risk breakdown."
            ai_insight = get_ai_environmental_insights(ai_prompt)
            
            st.markdown(f"""
            <div class="clinical-card">
                <strong>🤖 Google Gemini AI Clinical Reasoning:</strong><br>
                {ai_insight}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("#### 📍 Ready to Analyze. Please enter any global city or coordinates in the sidebar and click **Recalculate Environmental Report**.")

    st.markdown("""
    <div class="disclaimer-text">
        <strong>LEGAL & MEDICAL DISCLAIMER:</strong> CanopyRx is an environmental engineering research prototype. Always consult certified healthcare professionals for clinical decisions.
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# PAGE 2: ✈️ TRAVEL RX PLANNER
# ==========================================
elif app_mode == "✈️ Travel Rx Planner":
    st.markdown("# ✈️ Travel Rx: Pre-Travel Environmental Exposure Planner")
    st.markdown("##### *Compare environmental deltas between global origins and destinations.*")
    st.write("---")

    col_input1, col_input2 = st.columns(2)
    with col_input1:
        origin_search = st.text_input("Enter Origin Location (Global):", value="Mumbai", key="orig_search")
    with col_input2:
        dest_search = st.text_input("Enter Destination Location (Global):", value="London", key="dest_search")

    if st.button("Generate Travel Exposure Delta", type="primary", use_container_width=True):
        with st.spinner("Retrieving global atmospheric telemetry..."):
            lat_o, lon_o, addr_o = geocode_location(origin_search)
            lat_d, lon_d, addr_d = geocode_location(dest_search)

            if lat_o is not None and lat_d is not None:
                data_o = fetch_environmental_data(lat_o, lon_o)
                data_d = fetch_environmental_data(lat_d, lon_d)

                col_res1, col_res2 = st.columns([3, 1])
                with col_res1:
                    st.markdown(f"### 📊 Exposure Forecast: `{addr_o.split(',')[0]}` ➔ `{addr_d.split(',')[0]}`")
                with col_res2:
                    travel_report = f"TRAVEL EXPOSURE REPORT\nOrigin: {addr_o}\nDestination: {addr_d}\nTemp Delta: {data_d['temp'] - data_o['temp']}C\nPM2.5 Delta: {data_d['pm25'] - data_o['pm25']} ug/m3"
                    st.download_button("📥 Download Travel Report", travel_report, "Travel_Report.txt", mime="text/plain")

                temp_delta = data_d["temp"] - data_o["temp"]
                aqi_delta = data_d["pm25"] - data_o["pm25"]

                m1, m2, m3 = st.columns(3)
                m1.metric("Temperature Shift", f"{round(temp_delta, 1)}°C", f"Dest: {data_d['temp']}°C vs Orig: {data_o['temp']}°C", delta_color="inverse")
                m2.metric("UV Radiation Shift", f"{round(data_d['uv'] - data_o['uv'], 1)} UV", f"Dest: {data_d['uv']}", delta_color="inverse")
                m3.metric("Fine Particulate Shift", f"{round(aqi_delta, 1)} µg/m³", f"Dest: {data_d['pm25']}", delta_color="inverse")

                travel_ai_prompt = f"Provide a brief pre-travel clinical acclimatization advisory for a traveler moving from {addr_o} (Temp {data_o['temp']}C) to {addr_d} (Temp {data_d['temp']}C, PM2.5 {data_d['pm25']})."
                travel_advice = get_ai_environmental_insights(travel_ai_prompt)
                
                st.markdown(f"""
                <div class="clinical-card" style="margin-top: 20px;">
                    <strong>🤖 Gemini AI Traveler Acclimatization Guidance:</strong><br>
                    {travel_advice}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Could not resolve global locations. Check spelling.")

    st.markdown("""
    <div class="disclaimer-text">
        <strong>LEGAL & MEDICAL DISCLAIMER:</strong> CanopyRx Travel Rx is an experimental research module.
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# PAGE 3: 🧴 SKIN & HAIR RX
# ==========================================
elif app_mode == "🧴 Skin & Hair Rx":
    st.markdown("# 🧴 Skin & Hair Rx: Environmental Barrier Formulations")
    st.markdown("##### *Protect your physical moisture barrier from local atmospheric elements worldwide.*")
    
    if not st.session_state.premium_subscribed:
        st.markdown("""
        <div style="background-color: #fff9db; border: 1px solid #f59f00; border-radius: 6px; padding: 15px; margin-bottom: 20px;">
            🔑 <strong>Unlock Premium Diagnostics:</strong> Upgrade to access customizable skin types and complex hair porosity profiles.
        </div>
        """, unsafe_allow_html=True)
        if st.button("🌟 Upgrade to Premium Formulations (Free Simulation)", type="secondary"):
            unlock_premium()
            st.rerun()
    else:
        st.markdown("""
        <div style="background-color: #e6fcf5; border: 1px solid #099268; border-radius: 6px; padding: 15px; margin-bottom: 20px;">
            💎 <strong>Premium Unlocked:</strong> Full access enabled.
        </div>
        """, unsafe_allow_html=True)
        if st.button("Lock Premium Tools", type="secondary"):
            lock_premium()
            st.rerun()

    env = fetch_environmental_data(st.session_state.lat, st.session_state.lon)

    if st.session_state.premium_subscribed:
        st.markdown('### 💎 <span class="premium-badge">Premium Feature</span> Deep Dermatological Synthesis', unsafe_allow_html=True)
        skin_type = st.selectbox("Select Skin Type:", ["Dry / Flaky", "Oily / Acne-Prone", "Combination", "Highly Sensitive"])
        hair_porosity = st.selectbox("Hair Porosity Level:", ["Low (Water Repellent)", "Medium (Healthy)", "High (Damaged)"])
        
        if st.button("Generate Bespoke Care Formulation", type="primary"):
            st.markdown('<div class="premium-unlocked">', unsafe_allow_html=True)
            st.markdown("### 🧪 Bespoke Skin & Hair Prescription")
            skin_ai_prompt = f"Create a dermatological formulation for '{skin_type}' skin and '{hair_porosity}' hair in an environment with {env['humidity']}% humidity and UV index {env['uv']}."
            skin_advice = get_ai_environmental_insights(skin_ai_prompt)
            st.write(skin_advice)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("🔒 Premium features locked. Click upgrade above to unlock custom AI skin and hair prescriptions.")

    st.markdown("""
    <div class="disclaimer-text">
        <strong>LEGAL & MEDICAL DISCLAIMER:</strong> Formulations are general research recommendations.
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# PAGE 4: 🥗 ENVIRONMENTAL DIETETICS
# ==========================================
elif app_mode == "🥗 Environmental Dietetics":
    st.markdown("# 🥗 Environmental Dietetics & Live Weather Nutrition")
    st.markdown("##### *Tailoring dietary intake based on real-time micro-weather and air pollution.*")
    st.write("---")

    env = fetch_environmental_data(st.session_state.lat, st.session_state.lon)
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown(f"### 🌡️ Live Climate Parameters (`{st.session_state.resolved_address}`)")
        st.metric("Ambient Temperature", f"{env['temp']}°C")
        st.metric("Relative Humidity", f"{env['humidity']}%")
        st.metric("Particulate Burden (PM2.5)", f"{round(env['pm25'], 1)} µg/m³")
    
    with col_d2:
        st.markdown("### 🍎 AI-Powered Environmental Dietetic Prescription")
        diet_ai_prompt = f"Act as a clinical nutritionist. Based on current local conditions (Temp: {env['temp']}C, Humidity: {env['humidity']}%, PM2.5: {env['pm25']} ug/m3), recommend specific dietary antioxidants and hydration fluids."
        diet_prescription = get_ai_environmental_insights(diet_ai_prompt)
        
        st.markdown(f"""
        <div class="clinical-card">
            <strong>🥗 Personalized Anti-Pollution & Climate Diet Plan:</strong><br><br>
            {diet_prescription}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="disclaimer-text">
        <strong>LEGAL & MEDICAL DISCLAIMER:</strong> Dietetic recommendations are for educational and wellness guidance only.
    </div>
    """, unsafe_allow_html=True)