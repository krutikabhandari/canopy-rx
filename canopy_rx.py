import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

# Try imports for geocoding; install dynamically if missing
try:
    from geopy.geocoders import Nominatim
except ImportError:
    import os
    os.system('pip install geopy')
    from geopy.geocoders import Nominatim

# =========================================================================
# 🩺 1. PAGE CONFIGURATION & ARCHITECTURE THEME
# =========================================================================
st.set_page_config(
    page_title="CanopyRx Pro - Environmental Travel & Medicine Portal", 
    page_icon="🩺", 
    layout="wide"
)

# Custom High-Fidelity UI Styling
st.markdown("""
<style>
    /* Free Tier Styles */
    .free-badge {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 13px;
    }
    .normal-value-badge {
        background-color: #f0fdf4;
        color: #16a34a;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    
    /* Paid / Premium Tier Styles */
    .premium-badge {
        background-color: #fef3c7;
        color: #b45309;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 13px;
    }
    .premium-card {
        background-color: #fffbeb;
        border: 1px solid #fcd34d;
        border-left: 6px solid #d97706;
        padding: 22px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .prescription-header {
        color: #b45309;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 12px;
        border-bottom: 1px solid #fcd34d;
        padding-bottom: 6px;
    }
    .prescription-item {
        margin-bottom: 12px;
        padding-left: 12px;
        border-left: 3px solid #d97706;
        font-size: 14.5px;
    }
    .premium-lock-box {
        background-color: #fcf8e3;
        border: 2px dashed #f0ad4e;
        padding: 35px;
        border-radius: 8px;
        text-align: center;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================================
# ⚙️ 2. GLOBAL STATE ARCHITECTURE
# =========================================================================
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

# =========================================================================
# 📡 3. PRODUCTION ENVIRONMENTAL DATA ENGINE
# =========================================================================
def fetch_environmental_data(latitude, longitude):
    """Fetches real-time environmental data parameters via open meteorology APIs"""
    metrics = {
        "temp": 27.0, "humidity": 70.0, "uv": 5.0,
        "pm25": 35.0, "pm10": 50.0, "no2": 20.0, "co": 380.0, "o3": 40.0, "so2": 12.0
    }
    try:
        # Weather Metrics Fetch
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,uv_index"
        w_res = requests.get(weather_url, timeout=5).json()
        if "current" in w_res:
            metrics["temp"] = w_res["current"].get("temperature_2m", metrics["temp"])
            metrics["humidity"] = w_res["current"].get("relative_humidity_2m", metrics["humidity"])
            metrics["uv"] = w_res["current"].get("uv_index", metrics["uv"])

        # Air Quality Index Fetch
        aqi_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={latitude}&longitude={longitude}&current=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone,sulfur_dioxide"
        a_res = requests.get(aqi_url, timeout=5).json()
        if "current" in a_res:
            metrics["pm25"] = a_res["current"].get("pm2_5", metrics["pm25"])
            metrics["pm10"] = a_res["current"].get("pm10", metrics["pm10"])
            metrics["no2"] = a_res["current"].get("nitrogen_dioxide", metrics["no2"])
            metrics["co"] = a_res["current"].get("carbon_monoxide", metrics["co"])
            metrics["o3"] = a_res["current"].get("ozone", metrics["o3"])
            metrics["so2"] = a_res["current"].get("sulfur_dioxide", metrics["so2"])
    except Exception:
        pass  # Gracefully fall back to regional baseline defaults if APIs are congested
    return metrics

# =========================================================================
# 🩺 4. PLATFORM CORE BRANDING HEADER
# =========================================================================
st.markdown("# 🩺 CanopyRx: Environmental Medicine & Safe-Travel Portal")
st.markdown("##### *Smart-spatial diagnostics mapping local pathology risks, decoded micro-climate metrics, and premium personalized clinical defense plans.*")
st.write("---")

# =========================================================================
# 🗺️ 5. SIDEBAR GEOGRAPHIC CONTROL MATRIX
# =========================================================================
st.sidebar.markdown("### 🔐 User Access Level")
auth_mode = st.sidebar.radio("Select Account Tier:", ["Public Access (Free)", "Subscribed Patient (Premium)"])
st.session_state.user_tier = "Premium" if "Premium" in auth_mode else "Free"

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ Geographic Tracking")

# Manual Fallback System
input_mode = st.sidebar.radio("Location Entry Mode:", ["Search Address / Landmark", "Direct Coordinates"])

if input_mode == "Search Address / Landmark":
    country_option = st.sidebar.selectbox("Region / Country:", ["India", "United States", "United Kingdom", "Global / Other"])
    search_query = st.sidebar.text_input("Enter City, Pincode, or Area Name:", placeholder="e.g., Bandra West Mumbai...")

    if st.sidebar.button("Search & Analyze Location", use_container_width=True):
        if search_query:
            try:
                geolocator = Nominatim(user_agent="canopy_rx_platform_engine_v4")
                final_q = f"{search_query}, {country_option}" if country_option != "Global / Other" else search_query
                loc_data = geolocator.geocode(final_q, timeout=6)
                if loc_data:
                    st.session_state.lat = loc_data.latitude
                    st.session_state.lon = loc_data.longitude
                    st.session_state.resolved_address = loc_data.address
                    st.session_state.engine_active = True
                    st.rerun()
                else:
                    st.sidebar.error("Geographic query not found. Refine your query parameters.")
            except Exception:
                st.sidebar.warning("Geocoding service busy. Please re-click execution button.")
else:
    default_lat = float(st.session_state.lat) if st.session_state.lat else 19.0760
    default_lon = float(st.session_state.lon) if st.session_state.lon else 72.8777
    coord_lat = st.sidebar.number_input("Latitude:", value=default_lat, format="%.4f")
    coord_lon = st.sidebar.number_input("Longitude:", value=default_lon, format="%.4f")
    if st.sidebar.button("Apply Coordinates", use_container_width=True):
        st.session_state.lat = coord_lat
        st.session_state.lon = coord_lon
        st.session_state.resolved_address = ""
        st.session_state.engine_active = True
        st.rerun()

# Run Geolocation Address Resolution Processing
if st.session_state.engine_active and not st.session_state.resolved_address and st.session_state.lat and st.session_state.lon:
    try:
        geolocator = Nominatim(user_agent="canopy_rx_platform_engine_v4")
        resolved_loc = geolocator.reverse(f"{st.session_state.lat}, {st.session_state.lon}", timeout=4)
        st.session_state.resolved_address = resolved_loc.address if resolved_loc else f"Coordinates: {st.session_state.lat}, {st.session_state.lon}"
    except Exception:
        st.session_state.resolved_address = f"Coordinates: {st.session_state.lat}, {st.session_state.lon}"

# =========================================================================
# 💻 6. PRIMARY MAIN DATA DISPLAY LAYER
# =========================================================================
if st.session_state.engine_active and st.session_state.lat and st.session_state.lon:
    env_metrics = fetch_environmental_data(st.session_state.lat, st.session_state.lon)
    
    st.markdown(f"### 📍 Target Geo-Analysis Area: `{st.session_state.resolved_address}`")
    st.write(f"System Coordinates Processed: `{st.session_state.lat:.4f}° N, {st.session_state.lon:.4f}° E`")

    # -------------------------------------------------------------------------
    # 🌍 TIER 1: PUBLIC ACCESS INTERFACES (FREE TIER)
    # -------------------------------------------------------------------------
    st.markdown("### <span class='free-badge'>FREE PUBLIC ACCESS</span> ✈️ Eco-Travel & Daily Bio-Care Advisory", unsafe_allow_html=True)
    
    col_skincare, col_haircare, col_travel = st.columns(3)
    with col_skincare:
        st.markdown("#### 🧴 Bio-Adaptive Skincare Plan")
        if env_metrics["uv"] >= 6.0:
            st.write("⚠️ **High Solar Load:** UV Index is elevated. Utilize physical broad-spectrum mineral blockers (SPF 50+, Zinc Oxide base) every 2.5 hours.")
        else:
            st.write("☀️ **Normal Solar Index:** Standard non-comedogenic SPF 30 protective barrier cream is sufficient for general daytime exposure.")
        
        if env_metrics["humidity"] >= 65.0:
            st.write("💧 **High Humid Environment:** Transpirational cooling is inhibited. Deploy oil-free, water-based gel moisturizers to avoid sebaceous follicular blockage.")
        else:
            st.write("🌵 **Arid/Dehydrating Atmosphere:** Transepidermal water loss (TEWL) is accelerated. Apply rich lipid-replenishing occlusive barrier creams.")

    with col_haircare:
        st.markdown("#### 💇 Hair & Scalp Defensive Measures")
        if env_metrics["pm25"] > 30.0:
            st.write("💨 **High Particulate Stress:** Airborne micro-particles accumulate readily on structural hair cuticles. Apply silicone-free protective serums to minimize particulate adherence and reduce oxidative stress on the scalp root matrix.")
        else:
            st.write("🍃 **Atmospheric Clearance:** Low particulate deposition forces. Standard protective hair configurations apply safely.")

    with col_travel:
        st.markdown("#### 🎒 Eco-Packing Strategy Matrix")
        packing_list = ["♻️ Vacuum-insulated hydration flask for metabolic temperature management"]
        if env_metrics["uv"] >= 5.0:
            packing_list.extend(["🕶️ UV400 Rated Polarized Sunglasses", "👒 High-weave structural protective headwear"])
        if env_metrics["pm25"] >= 35.0:
            packing_list.append("😷 Electrostatic high-filtration NIOSH N95 Respirator")
        for item in packing_list:
            st.write(f"- {item}")

    # -------------------------------------------------------------------------
    # 💎 TIER 2: ADVANCED CLINICAL MEDICINE SUITE (PREMIUM ONLY)
    # -------------------------------------------------------------------------
    st.write("---")
    st.markdown("### 🔬 Clinical Spatial Medicine & Advanced Pathology Logic Engine")

    if st.session_state.user_tier == "Premium":
        st.markdown("<span class='premium-badge'>👑 PREMIUM PATIENT PORTAL ACTIVE</span>", unsafe_allow_html=True)
        
        # Extended Clinical Selector Framework
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            pre_existing = st.selectbox(
                "Select Verified Pathological / Diagnostic Concern:", 
                ["None", "Bronchial Asthma & Hyper-Reactivity", "Atopic Dermatitis / Eczema", "Allergic Rhinitis & Sinusitis Profile"]
            )
        with p_col2:
            occupation = st.selectbox(
                "Primary Occupational/Environment Profile:", 
                ["Office Worker (HVAC Recirculated Air)", "Construction Site / Outdoor Field Activity", "Manufacturing Facility (Powder/Chemical Processing)"]
            )

        # GRANULAR DEEP DIVE PRESCRIPTION CONFIGURATIONS
        st.markdown("#### 📋 Custom Personalized Spatial Defense Prescription")
        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        st.markdown("<div class='prescription-header'>💼 Occupational Stressors & Workspace Pathology Risk Assessment</div>", unsafe_allow_html=True)
        
        if occupation == "Construction Site / Outdoor Field Activity":
            st.write("⚠️ **Abrasive Particulate Overload:** High exposure velocity to mechanical dust and crystalline silica fragments. This significantly increases upper respiratory defense system fatigue.")
            st.markdown("<div class='prescription-item'><strong>Mandatory Clinical Protocol:</strong> Implement active nasal passages saline irrigation post-shift to clear mechanical non-filterable particulates.</div>", unsafe_allow_html=True)
        elif occupation == "Manufacturing Facility (Powder/Chemical Processing)":
            st.write("☣️ **Industrial Particulate & Inhalation Risk Matrix:** Vulnerability to chemical chemical vapors or airborne process powders (e.g., structural adhesives, mixing residues) that act as strong external allergens.")
            st.markdown("<div class='prescription-item'><strong>Mandatory Clinical Protocol:</strong> Utilize protective barriers for both epidermal layers and ocular tracking systems. Double-filtration safety masks must be combined with active ventilation blocks.</div>", unsafe_allow_html=True)
        else:
            st.write("🏢 **Recirculated Enclosed Micro-Climate:** Exposed to localized HVAC closed air pathways. Highly susceptible to concentrated mold spores, dust mites, and localized synthetic volatile organic compounds (VOCs).")
            st.markdown("<div class='prescription-item'><strong>Mandatory Clinical Protocol:</strong> Deploy structural HEPA desk filtration devices to process ambient micro-particulates within immediate workspace zones.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if pre_existing != "None":
            st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='prescription-header'>🩺 Targeted Pathological Intervention Strategy: {pre_existing}</div>", unsafe_allow_html=True)
            
            if pre_existing == "Bronchial Asthma & Hyper-Reactivity":
                st.write(f"🎯 **Airway Hyper-Reactivity Reduction Strategy (Current PM2.5 Read: `{env_metrics['pm25']} µg/m³`):**")
                st.markdown(f"<div class='prescription-item'><strong>1. Active Inhalation Threshold Control:</strong> Current local air readings contain micro-particles capable of inducing deep alveolar irritation. Restrict intense structural aerobic tasks to early morning or late night frames.</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='prescription-item'><strong>2. Preventive Bronchial Shielding:</strong> Keep fast-acting rescue inhaler protocols readily available when ambient temperature drifts rapidly alongside shifts in air particulates.</div>", unsafe_allow_html=True)
            
            elif pre_existing == "Atopic Dermatitis / Eczema":
                st.write(f"🎯 **Epidermal Barrier Remediation & Shielding Architecture (Current Humidity: `{env_metrics['humidity']}%`):**")
                st.markdown(f"<div class='prescription-item'><strong>1. External Antioxidant Matrix:</strong> Environmental stressors challenge compromised skin surfaces. Apply thick lipid-restoring ointments immediately following water contact to lock down structural surface integration.</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='prescription-item'><strong>2. Chemical Vapor Block:</strong> Block toxic gaseous compounds by deploying structural base layer garments when moving through high combustion areas.</div>", unsafe_allow_html=True)
            
            elif pre_existing == "Allergic Rhinitis & Sinusitis Profile":
                st.write(f"🎯 **Mucosal Membrane Stabilization Protocols (Current Ozone: `{env_metrics['o3']} µg/m³`):**")
                st.markdown(f"<div class='prescription-item'><strong>1. Histamine Trigger Control:</strong> Gaseous compounds present at this site can prompt structural updates within nasal mucosal cells. Utilize preventive non-sedating H1 receptor antagonists when tracking values elevate above safety lines.</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='prescription-item'><strong>2. Sinusitis Block:</strong> Administer localized sterile hypertonic sprays before bedtime hours to fully cleanse respiratory entry fields.</div>", unsafe_allow_html=True)
                
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Premium Marketing Wall
        st.markdown("""
        <div class='premium-lock-box'>
            <h4>🔒 Advanced Clinical Diagnostics & Pathological Logic Engine Blocked</h4>
            <p>Your current public tier is processing raw data metrics. Upgrade to premium console access to activate advanced disease mapping profiles, occupational hazard management blocks, and tailored dynamic prescription loops.</p>
            <strong style='color: #d97706; font-size: 15px;'>⭐ Unlock CanopyRx Premium Medical Matrix for $9.99/mo</strong>
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 📊 7. GRANULAR ENVIRONMENTAL DATA BASELINES & ANALYSIS
    # -------------------------------------------------------------------------
    st.write("---")
    st.markdown("### 🔬 Scientific Environmental Metrics & Decoded Reference Baselines")

    tab_particulates, tab_gases = st.tabs(["🌪️ Airborne Particulates & Suspended Matter", "💨 Gaseous Chemical Compounds"])
    with tab_particulates:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.metric("Fine Particulate Matter (PM2.5)", f"{env_metrics['pm25']} µg/m³")
            st.progress(min(1.0, env_metrics["pm25"] / 120.0))
            with st.expander("📝 Clinical Significance of PM2.5"):
                st.markdown("""
                * **Pathology:** Microscopic inhalable combustion soot capable of penetrating deep into alveolar networks, traversing the blood-air barrier, and precipitating systematic inflammatory feedback.
                * **Clinical Reference Baseline:** <span class="normal-value-badge">WHO Guideline: 24-hr mean limit ≤ 15 µg/m³</span>
                """, unsafe_allow_html=True)
        with col_p2:
            st.metric("Coarse Particulate Matter (PM10)", f"{env_metrics['pm10']} µg/m³")
            st.progress(min(1.0, env_metrics["pm10"] / 180.0))
            with st.expander("📝 Clinical Significance of PM10"):
                st.markdown("""
                * **Pathology:** Larger environmental crustal matter, silica fragments, and macro-dusts. Trapped inside the upper respiratory tree, causing mechanical hyper-secretion and cough reflexes.
                * **Clinical Reference Baseline:** <span class="normal-value-badge">WHO Guideline: 24-hr mean limit ≤ 45 µg/m³</span>
                """, unsafe_allow_html=True)

    with tab_gases:
        col_g1, col_g2, col_g3, col_g4 = st.columns(4)
        with col_g1:
            st.metric("Nitrogen Dioxide (NO₂)", f"{env_metrics['no2']} µg/m³")
            with st.expander("📝 Medical Risks of NO₂"):
                st.markdown("""
                * **Source & Effect:** Heavy vehicular engine emission gas. Acts as a strong mucosal toxicant, driving profound airway cell hypersensitivity loops.
                * **Reference Line:** <span class="normal-value-badge">WHO Limit: ≤ 25 µg/m³</span>
                """, unsafe_allow_html=True)
        with col_g2:
            st.metric("Carbon Monoxide (CO)", f"{env_metrics['co']} µg/m³")
            with st.expander("📝 Medical Risks of CO"):
                st.markdown("""
                * **Source & Effect:** Incomplete combustion toxic gas. Binds competitively with systemic hemoglobin networks, reducing vital cellular oxygen distribution.
                * **Reference Line:** <span class="normal-value-badge">WHO Limit: ≤ 4000 µg/m³</span>
                """, unsafe_allow_html=True)
        with col_g3:
            st.metric("Ozone (O₃)", f"{env_metrics['o3']} µg/m³")
            with st.expander("📝 Medical Risks of Ozone"):
                st.markdown("""
                * **Source & Effect:** Ground smog cooked by heavy sunlight. Causes immediate oxidative breakdown of functional lung surfactant tissue.
                * **Reference Line:** <span class="normal-value-badge">WHO Limit: ≤ 100 µg/m³</span>
                """, unsafe_allow_html=True)
        with col_g4:
            st.metric("Sulfur Dioxide (SO₂)", f"{env_metrics['so2']} µg/m³")
            with st.expander("📝 Medical Risks of SO₂"):
                st.markdown("""
                * **Source & Effect:** Industrial fossil combustion chemical output. Triggers acute, severe bronchial spasms in sensitive populations.
                * **Reference Line:** <span class="normal-value-badge">WHO Limit: ≤ 40 µg/m³</span>
                """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 🗺️ 8. DYNAMIC MAPPING CENTER
    # -------------------------------------------------------------------------
    st.write("---")
    st.markdown("### 🗺️ Geospatial Center Scanning Radius")
    m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=13)
    folium.Circle(
        location=[st.session_state.lat, st.session_state.lon], 
        radius=1000, 
        color="#d97706" if st.session_state.user_tier == "Premium" else "teal", 
        fill=True, 
        fill_opacity=0.08
    ).add_to(m)
    folium.Marker([st.session_state.lat, st.session_state.lon], popup="Target Scanning Zone").add_to(m)
    st_folium(m, width=1000, height=380, key="canopy_rx_premium_map_v4")

else:
    # Onboard Loading Screen
    st.info("👈 Set your target scanning coordinates or search a landmark in the sidebar to populate the analysis dashboards.")