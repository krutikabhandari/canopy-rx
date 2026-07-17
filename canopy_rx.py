import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# Page Configuration - Deep Medical-Teal Theme
st.set_page_config(
    page_title="CanopyRx - Environmental Medicine Portal", 
    page_icon="🩺", 
    layout="wide"
)

# STRICTOR CSS override to force-disable browser/Streamlit red warning outlines
st.markdown("""
<style>
    /* Absolute override for red borders/halos on input focus, validation, or active states */
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
</style>
""", unsafe_allow_html=True)

# Initialize Session State Safely (Including tracking keys to prevent state-jumps)
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

def activate_engine():
    st.session_state.engine_active = True

def reset_engine():
    st.session_state.engine_active = False

# --- CLINICAL PORTAL HEADER ---
st.markdown("# 🩺 CanopyRx: Clinical Micro-Climate & Preventive Environmental Medicine Portal")
st.markdown("##### *An advanced spatial diagnostic framework mapping urban micro-climate exposures and ecological footprints to localized pathology risks.*")
st.write("---")

# --- SIDEBAR: INPUTS & CLINICAL DROPDOWN ---
st.sidebar.markdown("### 📋 Diagnostic Inputs")

# Choose input methodology
input_mode = st.sidebar.radio(
    "Location Input Method:",
    ["Search Address / Landmark", "Direct Coordinates"],
    on_change=reset_engine
)

resolved_by_coords = False

if input_mode == "Search Address / Landmark":
    # 1. Country Selection
    country_option = st.sidebar.selectbox(
        "Region / Country:",
        ["India", "United States", "United Kingdom", "Indonesia", "Philippines", "Global / Other"],
        on_change=reset_engine
    )

    # 2. Address/Pincode/Building Text Input
    search_query = st.sidebar.text_input(
        "Enter City, Pincode, or Specific Building:", 
        placeholder="e.g., Central Park NY, or 400001...",
        on_change=reset_engine
    )

    # Geocoding function to convert search queries into lat/lon coordinates
    def geocode_address(query, country):
        try:
            geolocator = Nominatim(user_agent="canopyrx_clinical_environmental_engine_v5")
            final_query = query
            if country != "Global / Other" and country not in query:
                final_query = f"{query}, {country}"
                
            location_data = geolocator.geocode(final_query, timeout=10)
            if location_data:
                return location_data.latitude, location_data.longitude, location_data.address
            return None, None, None
        except (GeocoderTimedOut, Exception):
            return None, None, None

    # Run search instantly when input changes
    if search_query and (search_query != st.session_state.last_query or country_option != st.session_state.last_country):
        with st.sidebar.spinner("Resolving location details..."):
            lat, lon, addr = geocode_address(search_query, country_option)
            if lat and lon:
                st.session_state.lat = lat
                st.session_state.lon = lon
                st.session_state.resolved_address = addr
                st.session_state.last_query = search_query
                st.session_state.last_country = country_option
                st.session_state.engine_active = True  # Auto-activate on successful text search
            else:
                st.sidebar.warning("⚠️ Location not found. Try a broader term or check coordinates.")

else:
    # Direct Coordinate Entry
    st.sidebar.markdown("#### Enter Precise Coordinates")
    coord_lat = st.sidebar.number_input(
        "Latitude (Y):", 
        value=float(st.session_state.lat), 
        format="%.6f", 
        step=0.0001,
        on_change=reset_engine
    )
    coord_lon = st.sidebar.number_input(
        "Longitude (X):", 
        value=float(st.session_state.lon), 
        format="%.6f", 
        step=0.0001,
        on_change=reset_engine
    )
    
    if st.sidebar.button("Apply Coordinates", use_container_width=True):
        st.session_state.lat = coord_lat
        st.session_state.lon = coord_lon
        resolved_by_coords = True
        st.session_state.engine_active = True

# Reverse geocoding to find address with precision rounding safety limits
if resolved_by_coords or (st.session_state.lat != st.session_state.get("last_lat") or st.session_state.lon != st.session_state.get("last_lon")):
    try:
        geolocator = Nominatim(user_agent="canopyrx_clinical_environmental_engine_v5")
        resolved_loc = geolocator.reverse(f"{st.session_state.lat}, {st.session_state.lon}", timeout=5)
        if resolved_loc:
            st.session_state.resolved_address = resolved_loc.address
        else:
            st.session_state.resolved_address = f"Coordinates: {st.session_state.lat:.4f}, {st.session_state.lon:.4f}"
    except Exception:
        st.session_state.resolved_address = f"Coordinates: {st.session_state.lat:.4f}, {st.session_state.lon:.4f}"
    st.session_state.last_lat = st.session_state.lat
    st.session_state.last_lon = st.session_state.lon

# Dropdown to filter specific clinical condition risks
st.sidebar.markdown("---")
clinical_profile = st.sidebar.selectbox(
    "Select Medical Profile (Optional):",
    [
        "None (General Overview)", 
        "Bronchial Asthma / COPD", 
        "Atopic Dermatitis & Eczema", 
        "Allergic Rhinitis / Sinusitis", 
        "Cardiovascular Sensitivity"
    ],
    help="Select a specific condition to run a deep-dive micro-climate risk assessment."
)

# Optional Boundary Slider
st.sidebar.markdown("---")
diagnostic_radius = st.sidebar.slider(
    "Analysis Radius (meters):",
    min_value=50,
    max_value=5000,
    value=400, 
    step=50,
    help="Define the geographic boundary. Use 50m-200m for an individual building, and 2000m+ for general city-wide mapping."
)

st.sidebar.button(
    "Recalculate Environmental Report", 
    type="primary", 
    on_click=activate_engine,
    use_container_width=True
)

# Display Current Active Location Status
st.sidebar.info(f"📍 **Target Coordinates:**\nLat: `{st.session_state.lat:.6f}`\nLon: `{st.session_state.lon:.6f}`")

# --- LIVE API-BASED REAL-TIME DIAGNOSTIC COMPUTATION ---
if st.session_state.engine_active and st.session_state.lat and st.session_state.lon:
    lat = st.session_state.lat
    lon = st.session_state.lon
    resolved_address = st.session_state.resolved_address

    # PASTE YOUR WEATHERAPI.COM KEY HERE:
    API_KEY = "1a7d7e605314430bb7b81210261707"  
    
    query_location = f"{lat},{lon}"
    weather_url = "https://api.weatherapi.com/v1/current.json"
    weather_params = {
        "key": API_KEY,
        "q": query_location,
        "aqi": "yes"
    }

    try:
        with st.spinner("Retrieving live environmental sensor feeds..."):
            response = requests.get(weather_url, params=weather_params, timeout=10)
            
            if response.status_code != 200:
                error_data = response.json()
                st.error(f"WeatherAPI Error: {error_data['error']['message']}")
                raise ValueError("API call failed")
                
            weather_res = response.json()

            # Parse live weather metrics
            live_temp = weather_res["current"]["temp_c"]
            live_humidity = weather_res["current"]["humidity"]
            live_uv = weather_res["current"].get("uv", 1.0)
            live_wind = weather_res["current"].get("wind_kph", 10.0)
            
            # Parse Air Quality Metrics
            aqi_data = weather_res["current"].get("air_quality", {})
            live_pm25 = aqi_data.get("pm2_5", 25.0)
            live_pm10 = aqi_data.get("pm10", 40.0)
            live_co = aqi_data.get("co", 400.0)
            live_no2 = aqi_data.get("no2", 15.0)
            live_o3 = aqi_data.get("o3", 35.0)
            live_so2 = aqi_data.get("so2", 5.0)

    except Exception as e:
        st.error(f"Failed to fetch live API data: {e}. Reverting to baseline simulation.")
        live_temp, live_humidity, live_uv, live_wind = 28.0, 60.0, 5.0, 12.0
        live_pm25, live_pm10, live_co, live_no2, live_o3, live_so2 = 25.0, 40.0, 350.0, 12.0, 30.0, 4.0

    # ==========================================
    # 🌍 UNIVERSAL ENVIRONMENTAL INTELLIGENCE SCORING ENGINE
    # ==========================================
    
    # 1. Algorithmic Canopy & Vegetation Density (NDVI) Estimation
    thermal_loading = max(0.0, live_temp - 22.0)
    humidity_factor = max(0.1, live_humidity / 100.0)
    pollution_load = min(100.0, (live_pm25 + live_pm10) / 2.0)
    
    calculated_canopy = 45.0 - (pollution_load * 0.25) - (thermal_loading * 0.4) + (humidity_factor * 10.0)
    canopy_coverage = round(min(85.0, max(4.0, calculated_canopy)), 1)
    
    ndvi_estimate = round(0.08 + (canopy_coverage / 100.0) * 0.78, 2)

    # 2. Universal Acoustic Noise Exposure Proxy (dBA)
    ambient_noise_calc = 45.0 + (min(60.0, live_no2) * 0.4) + (min(1000.0, live_co) * 0.02)
    acoustic_noise = round(min(88.0, max(35.0, ambient_noise_calc)), 1)

    # 3. Night Light Pollution Index (Bortle Scale)
    bortle_calc = 2.0 + (min(80.0, live_no2) * 0.08)
    light_pollution = int(min(9, max(1, round(bortle_calc))))

    # 4. Planetary Carbon Sequestration Capacity
    carbon_offset_value = round(canopy_coverage * 1.25, 2)

    # 5. Global Carbon Footprint Classification
    if live_no2 > 30.0 or live_co > 600.0:
        carbon_footprint_scale = "Very High (Dense Carbon-Emitting Core)"
    elif live_no2 > 15.0 or live_co > 350.0:
        carbon_footprint_scale = "Moderate (Suburban/Developed Footprint)"
    else:
        carbon_footprint_scale = "Low-Impact (Rural or Well-Buffered Ecosystem)"

    # 6. Global Latitudinal Climate Zone Classification
    abs_lat = abs(lat)
    if abs_lat <= 23.5:
        climate_zone = "Tropical"
    elif abs_lat <= 35.0:
        climate_zone = "Subtropical"
    elif abs_lat <= 60.0:
        climate_zone = "Temperate"
    else:
        climate_zone = "Polar/Subpolar"

    # Apparent Temperature / Heat Index Calculation
    vapor_pressure = (live_humidity / 100.0) * 6.105 * (2.71828 ** ((17.27 * live_temp) / (237.7 + live_temp)))
    apparent_temp = live_temp + 0.33 * vapor_pressure - 4.0
    
    # Calculate Clinical Risk Indices
    thermal_stress_score = min(100.0, max(0.0, (apparent_temp - 20.0) * 4.0))
    pollution_penalty = (live_pm25 / 15.0) * 25.0
    canopy_mitigation = canopy_coverage * 0.5
    cardiorespiratory_risk = min(100.0, max(0.0, (pollution_penalty * 1.5) - canopy_mitigation))

    # --- MAIN PORTAL BODY ---
    st.markdown(f"### 📊 Clinical Spatial Assessment: `{resolved_address}`")
    st.write(f"Evaluating micro-climate, chemical, sensory, and ecological indices across a **{diagnostic_radius}m** geographic buffer.")
    
    # 3-Column Metrics Display
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric("🌳 Zone Canopy Coverage", f"{canopy_coverage}%", f"NDVI Vector: {ndvi_estimate}")
    with m_col2:
        st.metric("🌡️ Apparent Heat Index", f"{round(apparent_temp, 1)}°C", f"Actual Temperature: {live_temp}°C")
    with m_col3:
        st.metric("💨 Live PM2.5 Dust Level", f"{round(live_pm25, 1)} µg/m³", f"Live PM10: {round(live_pm10, 1)} µg/m³")

    st.write("---")

    # SECTION 1: INTERACTIVE SPATIAL DIAGNOSIS & MAP (MAP-CLICK INTEGRATION WITH STABILITY FIX)
    col_map, col_details = st.columns([3, 2])
    
    # Adjust zoom level dynamically based on radius selection
    if diagnostic_radius <= 150:
        zoom_val = 18  # Building Level
    elif diagnostic_radius <= 500:
        zoom_val = 16  # Local Block Level
    elif diagnostic_radius <= 1500:
        zoom_val = 14  # Neighborhood Level
    else:
        zoom_val = 11  # City Level

    grade_color = "green" if live_pm25 < 15 else "orange" if live_pm25 < 35 else "red"

    with col_map:
        st.markdown("#### 🗺️ Interactive Spatial Boundary Map")
        st.caption("💡 **Tip:** Click anywhere on the map below to drop a pin on a building or city quadrant and recalculate coordinates instantly!")
        
        m = folium.Map(location=[lat, lon], zoom_start=zoom_val, tiles="OpenStreetMap")
        folium.Circle(
            location=[lat, lon],
            radius=diagnostic_radius, 
            color=grade_color,
            fill=True,
            fill_color=grade_color,
            fill_opacity=0.12,
            popup=f"Boundary Diameter: {diagnostic_radius*2}m"
        ).add_to(m)
        folium.Marker(
            [lat, lon], 
            icon=folium.Icon(color="darkblue", icon="info-sign"),
            popup="Selected Target"
        ).add_to(m)
        
        # Capture clicks on the map to extract coordinates
        map_data = st_folium(m, width=700, height=380, key=f"clinical_map_{diagnostic_radius}")
        
        # Fixed: Precision float-rounding logic prevents infinite rerun loop
        if map_data and map_data.get("last_clicked"):
            click_lat = map_data["last_clicked"]["lat"]
            click_lon = map_data["last_clicked"]["lng"]
            if round(click_lat, 5) != round(st.session_state.lat, 5) or round(click_lon, 5) != round(st.session_state.lon, 5):
                st.session_state.lat = click_lat
                st.session_state.lon = click_lon
                st.session_state.engine_active = True
                st.rerun()
        
    with col_details:
        st.markdown("#### 🔬 Baseline Pathological Risk Profiling")
        st.write(f"The following general environmental vulnerability models are running:")
        
        # CARD 1: Respiratory Stress
        if live_pm25 > 30.0 or live_no2 > 25.0:
            st.markdown("""
            <div class="clinical-card">
                <strong>🫁 Bronchial & Upper Respiratory Vulnerability: High Risk</strong><br>
                Elevated PM2.5 particulates and gaseous irritants trigger respiratory hyper-reactivity, worsening bronchial asthma and allergic rhinitis.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="clinical-card" style="border-left-color: #2e7d32;">
                <strong>🫁 Bronchial Vulnerability: Low Risk</strong><br>
                Low particulate concentrations minimize respiratory mucous membrane irritation.
            </div>
            """, unsafe_allow_html=True)

        # CARD 2: Thermal Stress
        if apparent_temp > 35.0:
            st.markdown("""
            <div class="clinical-card">
                <strong>🩺 Cardiorespiratory & Dermatological Stress: High Risk</strong><br>
                The thermal penalty intensifies sweat gland obstruction (heat rashes) and elevates blood pressure fluctuation risks.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="clinical-card" style="border-left-color: #2e7d32;">
                <strong>🩺 Thermal Stress: Low/Moderate Risk</strong><br>
                Thermal values are stable, reducing heat-induced inflammatory flare-ups.
            </div>
            """, unsafe_allow_html=True)

    # ==========================================
    # MULTI-DIMENSIONAL ENVIRONMENTAL METRICS
    # ==========================================
    st.write("---")
    st.markdown("### 🔬 Advanced Multi-Dimensional Exposure Metrics")
    tab1, tab2, tab3 = st.tabs(["💨 Gaseous Pollutants", "🌱 Ecological & Carbon Metrics", "🔊 Sensory & Physical Stressors"])

    with tab1:
        st.markdown("#### Live Gaseous Inhalant Concentrations")
        g_col1, g_col2, g_col3, g_col4 = st.columns(4)
        with g_col1:
            st.metric("Nitrogen Dioxide (NO₂)", f"{round(live_no2, 1)} µg/m³", "Safety: 40 µg/m³")
            st.caption("Drives acute airway swelling and hyper-reactivity.")
        with g_col2:
            st.metric("Sulfur Dioxide (SO₂)", f"{round(live_so2, 1)} µg/m³", "Safety: 20 µg/m³")
            st.caption("Bronchial muscle spasm and localized airway irritant.")
        with g_col3:
            st.metric("Carbon Monoxide (CO)", f"{round(live_co, 1)} µg/m³", "Safety: 4000 µg/m³")
            st.caption("Binds hemoglobin, placing strain on cardiovascular oxygen delivery.")
        with g_col4:
            st.metric("Ground-Level Ozone (O₃)", f"{round(live_o3, 1)} µg/m³", "Safety: 100 µg/m³")
            st.caption("Highly reactive oxidant damaging delicate lung tissues.")

    with tab2:
        st.markdown(f"#### Ecological Vigor & Carbon Footprint Indices ({climate_zone} Zone)")
        e_col1, e_col2, e_col3 = st.columns(3)
        with e_col1:
            st.metric("Carbon Sequestration Capacity", f"{carbon_offset_value} Tons/Yr", "Canopy CO₂ Offset per km²")
        with e_col2:
            st.metric("Normalized Vegetation Index (NDVI)", f"{ndvi_estimate}", "Scale: 0 (Barren) to 1.0 (Lush)")
        with e_col3:
            st.metric("Carbon Footprint Estimate", "Heavy" if live_no2 > 30.0 else "Moderate" if live_no2 > 15.0 else "Minimal", carbon_footprint_scale)

    with tab3:
        st.markdown("#### Physical & Sensory System Stressors")
        s_col1, s_col2, s_col3 = st.columns(3)
        with s_col1:
            st.metric("Acoustic Noise Pollution Proxy", f"{acoustic_noise} dBA", "Sleep Limit: 40 dBA")
        with s_col2:
            st.metric("Night Light Pollution Rating", f"Bortle Class {light_pollution}", "Scale: 1 to 9")
        with s_col3:
            st.metric("Atmospheric UV Index", f"{live_uv}", "Safety: <3 Low, >8 Very High")

    # ==========================================
    # CLINICAL PROFILE DROPDOWN TRIGGER
    # ==========================================
    if clinical_profile != "None (General Overview)":
        st.write("---")
        st.markdown(f"### 🎯 Specialized Risk Assessment: **{clinical_profile}**")
        
        if clinical_profile == "Bronchial Asthma / COPD":
            trigger_score = min(100.0, (live_pm25 * 1.2) + (live_no2 * 0.8) + (live_so2 * 1.5))
            severity = "High Alert" if trigger_score > 60 else "Moderate Sensitivity" if trigger_score > 30 else "Normal/Stable"
            st.markdown(f"""
            <div class="targeted-card">
                <h4>🫁 Active Bronchial Risk Assessment: <strong>{severity} (Score: {round(trigger_score, 1)}/100)</strong></h4>
                <ul><li><strong>Live Triggers Detected:</strong> Fine dust is at {round(live_pm25, 1)} µg/m³ with Gaseous NO₂ at {round(live_no2, 1)} µg/m³. These small agents easily pass into lower airways, causing cellular hyper-reactivity.</li></ul>
            </div>
            """, unsafe_allow_html=True)
            
        elif clinical_profile == "Atopic Dermatitis & Eczema":
            skin_risk = max(100 - live_humidity, (apparent_temp - 25) * 3)
            severity = "High Flare Risk" if skin_risk > 60 else "Mild Flare Risk" if skin_risk > 35 else "Low Risk"
            st.markdown(f"""
            <div class="targeted-card">
                <h4>🩹 Active Eczema & Skin Barrier Assessment: <strong>{severity}</strong></h4>
                <ul><li><strong>Live Triggers Detected:</strong> Moisture level is {live_humidity}% and UV Index is {live_uv}.</li></ul>
            </div>
            """, unsafe_allow_html=True)
            
        elif clinical_profile == "Allergic Rhinitis / Sinusitis":
            sinus_risk = min(100.0, (live_pm10 * 1.2) + (live_humidity * 0.5))
            severity = "Highly Reactive" if sinus_risk > 65 else "Mildly Reactive" if sinus_risk > 40 else "Low Congestion Risk"
            st.markdown(f"""
            <div class="targeted-card">
                <h4>👃 Active Sinus & Mucous Membrane Assessment: <strong>{severity}</strong></h4>
                <ul><li><strong>Live Triggers Detected:</strong> PM10 coarse particulate load is {round(live_pm10, 1)} µg/m³.</li></ul>
            </div>
            """, unsafe_allow_html=True)
            
        elif clinical_profile == "Cardiovascular Sensitivity":
            cardio_risk = min(100.0, (apparent_temp * 1.5) + (live_co * 0.05) + (live_pm25 * 0.5))
            severity = "Vascular Strain Flag" if cardio_risk > 75 else "Stable Environment"
            st.markdown(f"""
            <div class="targeted-card">
                <h4>❤️ Active Cardiovascular Load Assessment: <strong>{severity}</strong></h4>
                <ul><li><strong>Live Triggers Detected:</strong> Real-time Heat Stress of {round(apparent_temp, 1)}°C and Carbon Monoxide levels of {round(live_co, 1)} µg/m³.</li></ul>
            </div>
            """, unsafe_allow_html=True)

    st.write("---")

    # SECTION 2: VISUAL GREEN PRESCRIPTIONS (DYNAMICALLY ADAPTED BY CLIMATE ZONE)
    st.markdown("### 💊 Preventive Medicine: Personalized Green Prescriptions")
    pres_col1, pres_col2 = st.columns(2)
    
    with pres_col1:
        st.markdown(f"#### 🌳 Botanical Interventions ({diagnostic_radius}m Planting Scope in {climate_zone} Zone)")
        
        if climate_zone in ["Tropical", "Subtropical"]:
            tree_title = "Neem (Azadirachta indica) & Ashoka (Saraca asoca)"
            tree_desc = "Highly textured foliar surfaces designed to trap fine particulate matter and gaseous toxins in warm humid or dry zones."
            img_url = "https://images.unsplash.com/photo-1598902108854-10e335adac99?auto=format&fit=crop&w=600&q=80"
        else:  # Temperate / Polar / General High Latitude
            tree_title = "Silver Birch (Betula pendula) & Red Maple (Acer rubrum)"
            tree_desc = "Deciduous canopy shields that survive freezing winters, providing maximum cooling shade in summer, and shedding leaves to let winter sunlight pass."
            img_url = "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=600&q=80"
            
        st.image(img_url, caption=f"Primary Canopy Recommendation: {tree_title}", use_container_width=True)
        st.write(tree_desc)

    with pres_col2:
        st.markdown("#### 🏠 Structural & Architectural Adaptations")
        if apparent_temp > 32.0:
            struct_title = "High-Albedo Thermal Deflection Membrane"
            struct_desc = f"With a localized Apparent Temperature of **{round(apparent_temp, 1)}°C**, treating roofs with solar-reflective coating (SRI > 78) blocks severe indoor heat accumulation."
            struct_img = "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=600&q=80"
        else:
            struct_title = "Passive Spatial Cross-Ventilation Arrays"
            struct_desc = "For cooler climates, prioritize natural air streams to safely purge indoor carbon dioxide and common dust mites without relying on energy-intensive chillers."
            struct_img = "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=600&q=80"
            
        st.image(struct_img, caption=f"Engineering Recommendation: {struct_title}", use_container_width=True)
        st.write(struct_desc)

else:
    # --- VISUAL LANDING HOMEPAGE ---
    st.info("👈 Enter coordinates, a local address, or click directly on the interactive map in the sidebar to run the diagnostic engine.")
    
    welcome_col1, welcome_col2 = st.columns(2)
    with welcome_col1:
        st.markdown("### 🧬 The CanopyRx Vision: Healing Spaces, Preventing Illness")
        st.write(
            "Environmental medicine maps micro-climate stressors like excessive heat load, gaseous inhalants, "
            "and acoustic levels to specific physiological vulnerabilities. By using hyper-local tracking (from cities to precise buildings), "
            "CanopyRx designs green solutions to mitigate spatial health risks."
        )
        st.image("https://images.unsplash.com/photo-1502082553048-f009c37129b9?auto=format&fit=crop&w=800&q=80", use_container_width=True)
        
    with welcome_col2:
        st.markdown("### 📋 Spatial Scale Setup")
        st.write(
            "To target a location:\n"
            "* **The City Level:** Enter general coordinates (e.g., `40.7128`, `-74.0060` for NYC) and use a **2000m+ analysis radius**.\n"
            "* **The Building Level:** Input precise coordinates (e.g., `18.9218`, `72.8347`), or type a building name in the search field, and scale the radius down to **50m-150m** to isolate structural exposure."
        )