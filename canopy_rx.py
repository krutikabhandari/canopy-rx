import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# For retrieving browser-based GPS coordinate values safely
try:
    from streamlit_js_eval import streamlit_js_eval
except ImportError:
    st.warning("⚠️ For live GPS support, run: 'pip install streamlit-js-eval'")

# Page Configuration - Premium Medical-Teal/Gold Theme
st.set_page_config(
    page_title="CanopyRx Pro - Environmental Travel & Medicine Portal", 
    page_icon="🩺", 
    layout="wide"
)

# Custom Styles
st.markdown("""
<style>
    /* Free Tier Styles */
    .free-badge {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
    }
    .metric-explainer {
        font-size: 13px;
        color: #4b5563;
        background-color: #f9fafb;
        padding: 8px 12px;
        border-radius: 6px;
        border-left: 3px solid #9ca3af;
        margin-top: 5px;
        margin-bottom: 12px;
    }
    .normal-value-badge {
        background-color: #f0fdf4;
        color: #16a34a;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
    }
    
    /* Paid/Premium Tier Styles */
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
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "lat" not in st.session_state or st.session_state.lat is None:
    st.session_state.lat = 19.0760  # Default to Mumbai
if "lon" not in st.session_state or st.session_state.lon is None:
    st.session_state.lon = 72.8777  # Default to Mumbai
if "resolved_address" not in st.session_state:
    st.session_state.resolved_address = "Mumbai, Maharashtra, India"
if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "last_country" not in st.session_state:
    st.session_state.last_country = ""
if "engine_active" not in st.session_state:
    st.session_state.engine_active = False

# --- LIVE LOCATION DETECTION ---
# --- FIND THIS IN YOUR SIDEBAR SECTION AND REPLACE IT ---
st.sidebar.markdown("#### 📍 Live Satellite Tracking")

# 1. This HTML/JavaScript script talks directly to the browser's native GPS
location_html = """
<div style="display: flex; justify-content: center;">
    <button onclick="sendLocation()" style="
        width: 100%; 
        background-color: #0d8a72; 
        color: white; 
        border: none; 
        padding: 10px; 
        border-radius: 8px; 
        cursor: pointer;
        font-weight: bold;
        font-family: sans-serif;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.1);
    ">📌 Detect My Live Location</button>
</div>

<script>
    function sendLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position) {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                
                // Send coordinates securely back to Streamlit
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: {lat: lat, lon: lon}
                }, '*');
            }, function(error) {
                alert("Location access denied or unavailable. Please check your browser permissions.");
            });
        } else {
            alert("Geolocation is not supported by this browser.");
        }
    }
</script>
"""

# 2. Embed the component into the sidebar
import streamlit.components.v1 as components
gps_data = components.html(location_html, height=50)

# 3. Catch the coordinates when the user clicks the button
if gps_data:
    st.session_state.lat = gps_data.get("lat")
    st.session_state.lon = gps_data.get("lon")
    st.session_state.engine_active = True

def activate_engine():
    st.session_state.engine_active = True

def reset_engine():
    st.session_state.engine_active = False

# --- PORTAL HEADER ---
st.markdown("# 🩺 CanopyRx: Environmental Medicine & Safe-Travel Portal")
st.markdown("##### *Smart-spatial diagnostics mapping local pathology risks, decoded micro-climate metrics, and premium personalized clinical defense plans.*")
st.write("---")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.markdown("### 🗺️ Geographic & Account Controls")

# Tier Toggle
app_tier = st.sidebar.radio("⭐ Application Portal Tier", ["Free Public Tier", "Premium Clinical Tier"], index=0)

# LIVE GEOLOCATION BUTTON
st.sidebar.markdown("#### 📍 Live Satellite Tracking")
if st.sidebar.button("📌 Detect My Live Location", use_container_width=True):
    use_live_gps()

st.sidebar.markdown("---")

# Alternative Manual Input Modes
input_mode = st.sidebar.radio(
    "Manual Input Method:",
    ["Search Address / Landmark", "Direct Coordinates"],
    on_change=reset_engine
)

resolved_by_coords = False

if input_mode == "Search Address / Landmark":
    country_option = st.sidebar.selectbox(
        "Region / Country:",
        ["India", "United States", "United Kingdom", "Indonesia", "Philippines", "Global / Other"],
        on_change=reset_engine
    )
    search_query = st.sidebar.text_input(
        "Enter City, Pincode, or Landmark:", 
        placeholder="e.g., Central Park NY...",
        on_change=reset_engine
    )

    def geocode_address(query, country):
        try:
            geolocator = Nominatim(user_agent="canopyrx_clinical_environmental_engine")
            final_query = query
            if country != "Global / Other" and country not in query:
                final_query = f"{query}, {country}"
            location_data = geolocator.geocode(final_query, timeout=10)
            if location_data:
                return location_data.latitude, location_data.longitude, location_data.address
            return None, None, None
        except Exception:
            return None, None, None

    if search_query and (search_query != st.session_state.last_query or country_option != st.session_state.last_country):
        with st.sidebar.spinner("Resolving coordinates..."):
            lat, lon, addr = geocode_address(search_query, country_option)
            if lat and lon:
                st.session_state.lat = lat
                st.session_state.lon = lon
                st.session_state.resolved_address = addr
                st.session_state.last_query = search_query
                st.session_state.last_country = country_option
                st.session_state.engine_active = True
            else:
                st.sidebar.warning("⚠️ Location not found.")

else:
    coord_lat = st.sidebar.number_input("Latitude:", value=float(st.session_state.lat), format="%.6f", on_change=reset_engine)
    coord_lon = st.sidebar.number_input("Longitude:", value=float(st.session_state.lon), format="%.6f", on_change=reset_engine)
    if st.sidebar.button("Apply Coordinates", use_container_width=True):
        st.session_state.lat = coord_lat
        st.session_state.lon = coord_lon
        resolved_by_coords = True
        st.session_state.engine_active = True

# Sync addresses
if resolved_by_coords or ("last_lat" in st.session_state and (st.session_state.lat != st.session_state.get("last_lat") or st.session_state.lon != st.session_state.get("last_lon"))):
    try:
        geolocator = Nominatim(user_agent="canopyrx_clinical_environmental_engine")
        resolved_loc = geolocator.reverse(f"{st.session_state.lat}, {st.session_state.lon}", timeout=5)
        st.session_state.resolved_address = resolved_loc.address if resolved_loc else f"Coordinates: {st.session_state.lat:.4f}, {st.session_state.lon:.4f}"
    except Exception:
        st.session_state.resolved_address = f"Coordinates: {st.session_state.lat:.4f}, {st.session_state.lon:.4f}"
    st.session_state.last_lat = st.session_state.lat
    st.session_state.last_lon = st.session_state.lon

st.sidebar.markdown("---")
st.sidebar.button("Recalculate Environmental Report", type="primary", on_click=activate_engine, use_container_width=True)

# --- RUN COMPUTATION LOGIC ---
if st.session_state.engine_active and st.session_state.lat and st.session_state.lon:
    lat, lon, resolved_address = st.session_state.lat, st.session_state.lon, st.session_state.resolved_address

    # Core data arrays (Simulated baseline metrics)
    live_temp, live_humidity, live_uv, live_wind = 29.0, 72.0, 8.0, 15.0
    live_pm25, live_pm10, live_no2, live_co, live_so2, live_o3 = 38.0, 52.0, 28.0, 420.0, 8.0, 42.0
    canopy_coverage = 24.5
    ndvi_estimate = 0.32
    acoustic_noise = 58.4
    light_pollution = 6
    carbon_offset_value = 30.6

    abs_lat = abs(lat)
    climate_zone = "Tropical" if abs_lat <= 23.5 else "Subtropical" if abs_lat <= 35.0 else "Temperate" if abs_lat <= 60.0 else "Polar"

    st.markdown(f"### 📍 Target Geo-Analysis: `{resolved_address}`")
    st.write(f"Environment Model: **{climate_zone} Zone** | Coordinates: `{lat:.4f}, {lon:.4f}`")

    # =========================================================================
    # 🌍 PORTAL TIER 1: FREE TIER (TRAVEL PRECAUTIONS & BIO-CARE)
    # =========================================================================
    if app_tier == "Free Public Tier":
        st.markdown("### <span class='free-badge'>FREE ACCESS</span> ✈️ Eco-Travel & Bio-Care Advisory", unsafe_allow_html=True)
        st.write("Dynamic packing checklist and customized physical shielding tips adjusted to this location's atmospheric load:")

        col_skincare, col_haircare, col_travel = st.columns(3)

        with col_skincare:
            st.markdown("#### 🧴 Bio-Adaptive Skincare Advice")
            if live_uv >= 6.0:
                uv_rec = "⚠️ **High UV Defense:** Apply broad-spectrum Mineral SPF 50+ (Zinc Oxide base) every 2 hours."
            else:
                uv_rec = "☀️ **Moderate UV Protection:** SPF 30+ is sufficient for brief daylight spans."
                
            if live_humidity >= 70.0:
                hum_rec = "💧 **High Humidity Care:** Use non-comedogenic gel-based moisturizers to block sweat-gland obstruction (Miliaria)."
            else:
                hum_rec = "🌵 **Arid Climate Care:** Focus on skin barrier retention with hyaluronic acid and ceramide creams."
            st.write(f"{uv_rec}\n\n{hum_rec}")

        with col_haircare:
            st.markdown("#### 💇 Hair & Scalp Defense")
            if live_pm25 > 25.0:
                pm_hair = "💨 **Anti-Pollution Wash:** Micro-particulates damage hair cuticles. Consider applying a leave-in hair shield or botanical coat."
            else:
                pm_hair = "🍃 **Clean Canopy Air:** Scalp exposure to air pollutants is minimal here."
            if live_humidity > 65.0:
                hum_hair = "🌀 **Frizz & Scalp Protection:** High relative moisture triggers cuticle swelling. Keep scalp dry to avoid fungal flare-ups."
            else:
                hum_hair = "🍂 **Moisture Shielding:** Dry conditions cause split ends. Use nourishing botanical scalp oils."
            st.write(f"{pm_hair}\n\n{hum_hair}")

        with col_travel:
            st.markdown("#### 🎒 Location Packing Essentials")
            items = ["♻️ Reusable Water Vessel (Hydration)"]
            if live_uv >= 5.0:
                items.append("🕶️ UV400 Rated Eye Shielding")
                items.append("👒 Wide-Brimmed Sun Hat")
            if live_pm25 > 35.0:
                items.append("😷 High-filtration Mask (N95) for transit days")
            if live_humidity < 40.0:
                items.append("👄 Natural Beeswax Lip Balm")
            
            st.write("Before boarding, ensure you pack:")
            for item in items:
                st.write(f"- {item}")

    # =========================================================================
    # 💎 PORTAL TIER 2: PREMIUM TIER (SPECIFIC DIAGNOSIS & OCCUPATIONAL PLANS)
    # =========================================================================
    else:
        st.markdown("### <span class='premium-badge'>👑 PREMIUM CLINICAL ACCESS</span> 🧬 Occupational & Pathology Engine", unsafe_allow_html=True)
        st.write("Formulate a customized clinical shield matching active pre-existing symptoms, age metrics, and workspace exposures:")

        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            pre_existing = st.selectbox(
                "Primary Clinical Pathology:",
                ["None", "Bronchial Asthma & Hyper-Reactivity", "Atopic Dermatitis & Psoriasis", "Allergic Sinusitis & Rhinitis"]
            )
        with p_col2:
            occupation = st.selectbox(
                "Work Environment / Occupation:",
                ["Office (HVAC Controlled)", "Construction Site / Outdoor Laborer", "Chemical & Materials Industry", "Active Field Travel"]
            )
        with p_col3:
            daily_exposure = st.slider("Daily Outdoor Exposure (Hours):", 1, 14, 4)

        if st.button("Generate My Dynamic Clinical Prescription Plan", type="primary"):
            st.markdown("---")
            st.markdown("#### 📋 Custom Personalized Spatial Defense Prescription")
            
            st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
            st.markdown("##### 💼 Workspace Stressor Evaluation")
            if occupation == "Construction Site / Outdoor Laborer":
                st.write("⚠️ **High Particulate Threat:** Your occupation places you in direct path of airborne cement dust and coarse silica particulate matter.")
            elif occupation == "Chemical & Materials Industry":
                st.write("☣️ **Chemical Inhalation Threat:** High sensitivity risk to gaseous solvents and acid vapor compounds. Protective respirator systems are highly recommended.")
            else:
                st.write("🏢 **Recirculated Air Profile:** Moderate risk of structural indoor dust mite density and CO2 retention. Prioritize routine cross-ventilation cycles.")
            st.markdown("</div>", unsafe_allow_html=True)

            if pre_existing != "None":
                st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
                st.markdown(f"##### 🩺 Specific Disease Protection Protocol: **{pre_existing}**")
                if pre_existing == "Bronchial Asthma & Hyper-Reactivity":
                    st.write("🎯 **Airway Inflammation Management Strategy:**")
                    st.markdown("<div class='prescription-item'><strong>1. Critical Threshold Warning:</strong> PM2.5 at this coordinate is currently high. Limit peak outdoor respiratory activity between 11 AM - 4 PM.</div>", unsafe_allow_html=True)
                    st.markdown("<div class='prescription-item'><strong>2. Specific Botanical Defense:</strong> Seek environments buffered by mature <i>Azadirachta indica</i> (Neem) trees, which naturally absorb gaseous NO₂ pollutants.</div>", unsafe_allow_html=True)
                elif pre_existing == "Atopic Dermatitis & Psoriasis":
                    st.write("🎯 **Skin Barrier Remediation & Hydration Strategy:**")
                    st.markdown("<div class='prescription-item'><strong>1. Micro-Climate Factor:</strong> Atmospheric humidity is currently high. Avoid heavy lipid-rich creams that trap ambient heat. Opt for light, water-binding formulas.</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # 📊 DECODED ENVIRONMENTAL METRICS SECTION (WITH EXPLANATIONS & NORMAL VALUES)
    # =========================================================================
    st.write("---")
    st.markdown("### 🔬 Scientific Environmental Metrics & Decoded Reference Baselines")
    st.caption("Expand any parameter box below to understand what the numbers mean and inspect standard healthy baselines.")

    tab_particulates, tab_gases, tab_ecology, tab_sensory = st.tabs([
        "🌪️ Particulates & Dust", "💨 Gaseous Toxins", "🌱 Ecological Vigor", "🔊 Sensory Stressors"
    ])

    with tab_particulates:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.metric("Fine Particulate Matter (PM2.5)", f"{live_pm25} µg/m³")
            st.progress(min(1.0, live_pm25 / 75.0)) # Visual tracking gauge
            with st.expander("📝 Deconstruct PM2.5 & Normal Values"):
                st.markdown("""
                * **What it means:** Super-fine microscopic dust particles smaller than 2.5 micrometers (1/30th of a human hair width) suspended in the air.
                * **Why it matters:** Because they are incredibly small, they bypass your upper nasal filters and lodge deep into the lung alveoli, passing straight into the bloodstream.
                * **Normal/Healthy Values:** <span class="normal-value-badge">WHO Safety Guideline: Annual average below 5 µg/m³; 24-hr average below 15 µg/m³</span>
                """, unsafe_allow_html=True)
        
        with col_p2:
            st.metric("Coarse Particulate Matter (PM10)", f"{live_pm10} µg/m³")
            st.progress(min(1.0, live_pm10 / 150.0))
            with st.expander("📝 Deconstruct PM10 & Normal Values"):
                st.markdown("""
                * **What it means:** Coarser dust, pollen, soot, and mold particles between 2.5 and 10 micrometers in size.
                * **Why it matters:** Stays primarily trapped in the windpipe and upper respiratory tract, inducing severe coughing, allergic rhinitis, and sinus congestion.
                * **Normal/Healthy Values:** <span class="normal-value-badge">WHO Safety Guideline: Annual average below 15 µg/m³; 24-hr average below 45 µg/m³</span>
                """, unsafe_allow_html=True)

    with tab_gases:
        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
            st.metric("Nitrogen Dioxide (NO₂)", f"{live_no2} µg/m³")
            with st.expander("📝 Deconstruct NO₂"):
                st.markdown("""
                * **What it means:** A toxic, highly reactive gas primarily emitted from vehicle exhausts and industrial combustion.
                * **Why it matters:** Severely irritates the inner linings of airways, heightening allergic responses to pollen and causing asthma flareups.
                * **Normal/Healthy Values:** <span class="normal-value-badge">WHO Safety Baseline: Below 25 µg/m³ (24-hr average)</span>
                """, unsafe_allow_html=True)

        with col_g2:
            st.metric("Carbon Monoxide (CO)", f"{live_co} µg/m³")
            with st.expander("📝 Deconstruct CO"):
                st.markdown("""
                * **What it means:** An odorless, colorless gas produced by incomplete fossil fuel combustion.
                * **Why it matters:** Reduces the oxygen-carrying capacity of blood cells, inducing headaches, fatigue, and vascular stress.
                * **Normal/Healthy Values:** <span class="normal-value-badge">WHO Safety Baseline: Below 4000 µg/m³ (24-hr average)</span>
                """, unsafe_allow_html=True)

        with col_g3:
            st.metric("Ground-Level Ozone (O₃)", f"{live_o3} µg/m³")
            with st.expander("📝 Deconstruct Ozone"):
                st.markdown("""
                * **What it means:** Surface-level smog created when sunshine cooks traffic pollution. 
                * **Why it matters:** Functions like a chemical sunburn on delicate inner lung tissues, causing chest tightness.
                * **Normal/Healthy Values:** <span class="normal-value-badge">WHO Safety Baseline: Below 100 µg/m³ (8-hr average)</span>
                """, unsafe_allow_html=True)

    with tab_ecology:
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.metric("Zone Canopy Coverage", f"{canopy_coverage}%")
            with st.expander("📝 Deconstruct Canopy Score"):
                st.markdown("""
                * **What it means:** The percentage of ground surface area overhead shaded by living tree leaves when viewed from above.
                * **Why it matters:** Shaded surfaces lower surface temperatures up to 10°C, absorbing airborne dust elements directly onto leaf cuticles.
                * **Normal/Healthy Values:** <span class="normal-value-badge">Target Urban Metric: 30% to 40% optimal neighborhood canopy cover</span>
                """, unsafe_allow_html=True)

        with col_e2:
            st.metric("Normalized Vegetation Index (NDVI)", f"{ndvi_estimate}")
            with st.expander("📝 Deconstruct NDVI"):
                st.markdown("""
                * **What it means:** Satellite proxy index calculating green leaf health via near-infrared light absorption.
                * **Why it matters:** Separates concrete structures from lush living ecosystems to gauge immediate biodiversity access.
                * **Normal/Healthy Values:** <span class="normal-value-badge">Scale: 0.0 (Barren Concrete) to 1.0 (Dense Rainforest). Target: >0.40</span>
                """, unsafe_allow_html=True)

    with tab_sensory:
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("Acoustic Noise Pollution Proxy", f"{acoustic_noise} dBA")
            with st.expander("📝 Deconstruct Decibel (dBA) Stress"):
                st.markdown("""
                * **What it means:** Estimated ambient noise background levels influenced by localized transit and industrial density.
                * **Why it matters:** Continuous ambient background sound levels above safe baselines disrupt autonomic sleep, keeping cortisol (stress hormones) elevated.
                * **Normal/Healthy Values:** <span class="normal-value-badge">Safe Thresholds: Outdoor Residential Day: <55 dBA; Safe Sleep Night: <40 dBA</span>
                """, unsafe_allow_html=True)

        with col_s2:
            st.metric("Night Light Pollution Rating", f"Bortle Class {light_pollution}")
            with st.expander("📝 Deconstruct Bortle Sky Scale"):
                st.markdown("""
                * **What it means:** A 1-to-9 numeric ranking mapping night sky brightness and light saturation.
                * **Why it matters:** Excess blue/white artificial light exposure at night prevents normal melatonin production, degrading cellular repair cycles.
                * **Normal/Healthy Values:** <span class="normal-value-badge">Bortle Class 1-3: Pristine Rural Sky; Class 4-6: Suburban; Class 7-9: Saturated Inner City</span>
                """, unsafe_allow_html=True)

    # Map Rendering Boundary
    st.write("---")
    m = folium.Map(location=[lat, lon], zoom_start=14, tiles="OpenStreetMap")
    folium.Circle(location=[lat, lon], radius=600, color="teal", fill=True, fill_opacity=0.1).add_to(m)
    folium.Marker([lat, lon], icon=folium.Icon(color="darkblue", icon="info-sign")).add_to(m)
    st_folium(m, width=800, height=350, key="interactive_shared_map")

else:
    st.info("👈 Set your target location! Click 'Detect My Live Location' or select manual inputs to test.")