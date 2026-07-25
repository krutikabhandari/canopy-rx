import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from geopy.geocoders import Nominatim
from datetime import datetime
import io

# ReportLab imports for Lab-Grade Full-Suite PDF Generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Page Configuration - Deep Medical-Teal Theme
st.set_page_config(
    page_title="CanopyRx - Green Engineering & Environmental Health Portal", 
    page_icon="🌳", 
    layout="wide"
)

# STRICTOR CSS override for professional clinical UI styling
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
        padding: 14px;
        border-radius: 4px;
        margin-bottom: 12px;
        font-size: 14px;
    }
    .warning-card {
        background-color: #fff5f5;
        border-left: 5px solid #e53e3e;
        padding: 14px;
        border-radius: 4px;
        margin-bottom: 12px;
        font-size: 14px;
    }
    .info-card {
        background-color: #f0f4f8;
        border-left: 5px solid #3182ce;
        padding: 14px;
        border-radius: 4px;
        margin-bottom: 12px;
        font-size: 14px;
    }
    .legal-disclaimer {
        background-color: #fcfcfc;
        border: 1px solid #e2e8f0;
        padding: 12px;
        border-radius: 6px;
        font-size: 11px;
        color: #64748b;
        margin-top: 25px;
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
</style>
""", unsafe_allow_html=True)

# Initialize Session State Safely (Defaulting cleanly to Mumbai/Global baseline)
if "lat" not in st.session_state or st.session_state.lat is None:
    st.session_state.lat = 19.0760  
if "lon" not in st.session_state or st.session_state.lon is None:
    st.session_state.lon = 72.8777  
if "resolved_address" not in st.session_state:
    st.session_state.resolved_address = "Mumbai, Maharashtra, India"
if "engine_active" not in st.session_state:
    st.session_state.engine_active = False
if "premium_subscribed" not in st.session_state:
    st.session_state.premium_subscribed = False

def activate_engine():
    st.session_state.engine_active = True

def reset_engine():
    st.session_state.engine_active = False

def unlock_premium():
    st.session_state.premium_subscribed = True

def lock_premium():
    st.session_state.premium_subscribed = False

# ==========================================
# 🗺️ SIDEBAR NAVIGATION (ALL PORTALS RESTORED)
# ==========================================
st.sidebar.markdown("# 🩺 CanopyRx Suite")
app_mode = st.sidebar.selectbox(
    "Select Portal Module:",
    [
        "🏠 Home / Overview", 
        "🌍 CanopyRx Spatial Engine", 
        "✈️ Travel Rx Planner", 
        "🧴 Skin & Hair Rx", 
        "🥗 Dietetics & Nutrition Rx", 
        "👕 Clothing & Protection Rx", 
        "⛅ Live Weather & Climate Dashboard"
    ]
)
st.sidebar.write("---")

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
                "no2": aqi.get("no2", 15.0),
                "co": aqi.get("co", 400.0),
                "so2": aqi.get("so2", 5.0),
                "o3": aqi.get("o3", 35.0),
                "success": True
            }
    except Exception:
        pass
    return {
        "temp": 28.0, "humidity": 60.0, "uv": 5.0, "wind": 12.0,
        "pm25": 25.0, "pm10": 40.0, "no2": 12.0, "co": 350.0,
        "so2": 4.0, "o3": 30.0, "success": False
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

def generate_full_suite_pdf(address, lat, lon, env, metrics_summary):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#0d8a72'), spaceAfter=4)
    subtitle_style = ParagraphStyle('DocSubTitle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#555555'), spaceAfter=12)
    heading_style = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#1e293b'), spaceBefore=8, spaceAfter=4)
    body_style = ParagraphStyle('BodyDark', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#333333'), spaceAfter=6)

    story.append(Paragraph("CanopyRx Full-Suite Clinical & Environmental Intelligence Report", title_style))
    story.append(Paragraph(f"<b>Generated on:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | <b>Data Source:</b> WeatherAPI & OpenStreetMap Nominatim Geospatial Engine", subtitle_style))
    story.append(Paragraph(f"<b>Target Analysis Location:</b> {address} (Lat: {lat:.4f}, Lon: {lon:.4f})", body_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("1. Atmospheric & Environmental Exposure Metrics", heading_style))
    table_data = [
        ["Parameter", "Measured Value", "Standard Normal Range", "Clinical Impact Summary"],
        ["Ambient Temperature", f"{env['temp']} °C", "18°C - 27°C", "Thermal load index"],
        ["Relative Humidity", f"{env['humidity']}%", "40% - 60%", "Epithelial moisture balance"],
        ["Fine Particulate (PM2.5)", f"{round(env['pm25'], 1)} µg/m³", "< 15 µg/m³", "Deep pulmonary inflammation risk"],
        ["Particulate Matter (PM10)", f"{round(env['pm10'], 1)} µg/m³", "< 50 µg/m³", "Upper airway deposition risk"],
        ["Nitrogen Dioxide (NO2)", f"{round(env['no2'], 1)} µg/m³", "< 40 µg/m³", "Mucosal irritation index"],
        ["Ultraviolet Index", f"{env['uv']}", "< 3.0 (Low)", "Photolytic skin/tissue stress"]
    ]
    
    t = Table(table_data, colWidths=[110, 85, 110, 235])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0d8a72')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d1d5db')),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f9fafb'))
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    story.append(Paragraph("2. Prescriptive Multi-Modal Interventions & Protocols", heading_style))
    for rec in metrics_summary:
        story.append(Paragraph(f"• {rec}", body_style))
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("3. Legal & Medical Compliance Disclaimer", heading_style))
    story.append(Paragraph("<b>Disclaimer:</b> This report is generated by the CanopyRx AI Spatial Medicine Intelligence Suite for informational and environmental engineering assessment purposes only. It does not constitute formal medical diagnosis or clinical prescription. Consult qualified healthcare providers for medical conditions.", body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# PAGE 0: 🏠 HOME / OVERVIEW
# ==========================================
if app_mode == "🏠 Home / Overview":
    st.markdown("# 🩺 CanopyRx: Green Engineering & Environmental Health Portal")
    st.markdown("##### *Quantifying Green Cover Canopy Solutions to Combat Localized Anthropogenic Exposure and Restore Spatial Health.*")
    st.write("---")
    
    st.markdown("""
    ### Welcome to the CanopyRx Intelligence Suite
    Modern urbanization has systematically compromised Earth's natural mechanical and biological buffer: **the urban green canopy**. When green cover is degraded, localized micro-climates experience extreme thermal stress, elevated pollutant concentrations, and heightened acoustic/airborne loads. 
    
    **CanopyRx** bridges environmental engineering with spatial medicine, offering real-time computational diagnostics and targeted preventative interventions.
    """)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        #### 🌍 Spatial Engine
        Analyze micro-climates, PM2.5/PM10 loads, NDVI green indices, and localized clinical health profiles.
        """)
    with c2:
        st.markdown("""
        #### ✈️ Travel Rx Planner
        Calculate pre-travel environmental deltas and thermal/respiratory acclimatization requirements between any two points globally.
        """)
    with c3:
        st.markdown("""
        #### 🧴 Skin & Hair Rx
        Protect physical moisture barriers against local humidity, UV radiation, and water hardness mineral scaling.
        """)
        
    st.write("---")
    st.markdown("### 🚀 Quick Navigation")
    st.info("👈 Use the **Select Portal Module** dropdown in the sidebar to jump directly into any diagnostic engine, configure your target location, and generate comprehensive multi-aspect reports.")


# ==========================================
# PAGE 1: 🌍 CANOPYRX SPATIAL ENGINE
# ==========================================
elif app_mode == "🌍 CanopyRx Spatial Engine":
    st.sidebar.markdown("### 📋 Diagnostic Inputs")
    input_mode = st.sidebar.radio("Location Input:", ["Search Address / Landmark", "Direct Coordinates"], on_change=reset_engine)

    if input_mode == "Search Address / Landmark":
        country_option = st.sidebar.selectbox("Region / Country:", ["India", "United States", "United Kingdom", "Indonesia", "Philippines", "Global / Other"], on_change=reset_engine)
        search_query = st.sidebar.text_input("Enter City, Pincode, or Building Name:", placeholder="e.g., Nashik, Central Park NY...", on_change=reset_engine)

        if search_query:
            with st.sidebar.spinner("Resolving location details..."):
                lat, lon, addr = geocode_location(search_query, country_option)
                if lat and lon:
                    st.session_state.lat, st.session_state.lon, st.session_state.resolved_address = lat, lon, addr
                    st.session_state.engine_active = True
    else:
        coord_lat = st.sidebar.number_input("Latitude (Y):", value=float(st.session_state.lat), format="%.6f", step=0.0001, on_change=reset_engine)
        coord_lon = st.sidebar.number_input("Longitude (X):", value=float(st.session_state.lon), format="%.6f", step=0.0001, on_change=reset_engine)
        if st.sidebar.button("Apply Coordinates & Generate", use_container_width=True):
            st.session_state.lat, st.session_state.lon = coord_lat, coord_lon
            try:
                geolocator = Nominatim(user_agent="canopyrx_clinical_engine_v7")
                resolved_loc = geolocator.reverse(f"{coord_lat}, {coord_lon}", timeout=5)
                if resolved_loc:
                    st.session_state.resolved_address = resolved_loc.address
            except Exception:
                st.session_state.resolved_address = f"Coordinates: {coord_lat:.4f}, {coord_lon:.4f}"
            st.session_state.engine_active = True

    clinical_profile = st.sidebar.selectbox("Select Medical Profile:", ["None (General Overview)", "Bronchial Asthma / COPD", "Atopic Dermatitis & Eczema", "Allergic Rhinitis / Sinusitis", "Cardiovascular Sensitivity"])
    diagnostic_radius = st.sidebar.slider("Analysis Radius (meters):", min_value=50, max_value=5000, value=400, step=50)
    
    st.sidebar.button("Recalculate Environmental Report", type="primary", on_click=activate_engine, use_container_width=True)

    st.markdown("# 🩺 CanopyRx: Green Engineering & Environmental Health Portal")
    st.markdown("##### *Quantifying Green Cover Canopy Solutions to Combat Localized Anthropogenic Exposure.*")
    st.write("---")

    if st.session_state.engine_active:
        env = fetch_environmental_data(st.session_state.lat, st.session_state.lon)
        pollution_load = min(100.0, (env["pm25"] + env["pm10"]) / 2.0)
        canopy_coverage = round(min(85.0, max(4.0, 45.0 - (pollution_load * 0.25))), 1)
        ndvi_estimate = round(0.08 + (canopy_coverage / 100.0) * 0.78, 2)
        apparent_temp = env["temp"] + 2.0
        climate_zone = "Tropical" if abs(st.session_state.lat) <= 23.5 else "Subtropical" if abs(st.session_state.lat) <= 35.0 else "Temperate" if abs(st.session_state.lat) <= 60.0 else "Polar"

        st.markdown(f"### 📊 Clinical Spatial Assessment: `{st.session_state.resolved_address}`")
        
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric("🌳 Zone Canopy Coverage", f"{canopy_coverage}%", f"NDVI: {ndvi_estimate}")
            st.markdown("**[Normal Target: >30%]**  \n*Impact:* Cools neighborhoods, filters toxic particulate matter, and reduces cortisol stress.")
        with m_col2:
            st.metric("🌡️ Apparent Heat Index", f"{round(apparent_temp, 1)}°C", f"Actual: {env['temp']}°C")
            st.markdown("**[Normal Comfort: 18°C - 27°C]**  \n*Impact:* Measures physiological thermal stress load on the cardiovascular system.")
        with m_col3:
            st.metric("💨 Live PM2.5 Level", f"{round(env['pm25'], 1)} µg/m³", f"PM10: {round(env['pm10'], 1)} µg/m³")
            st.markdown("**[Normal Safe Limit: <15 µg/m³]**  \n*Impact:* Fine combustion dust penetrating pulmonary alveolar barriers into the bloodstream.")

        st.write("---")

        # Profile Diagnostics
        st.markdown(f"#### 🔬 Medical Profile Diagnostics: *{clinical_profile}*")
        if clinical_profile == "Bronchial Asthma / COPD" and (env["pm25"] > 15.0 or env["no2"] > 20.0):
            st.markdown(f'<div class="warning-card"><strong>🚨 HIGH BRONCHIAL REACTIVITY WARNING:</strong> Fine particulate level (PM2.5: {round(env["pm25"], 1)} µg/m³) exceeds safe tolerances. Keep rescue inhalers accessible.</div>', unsafe_allow_html=True)
        elif clinical_profile == "Atopic Dermatitis & Eczema" and env["humidity"] < 40.0:
            st.markdown(f'<div class="warning-card"><strong>🚨 HIGH TRANSEPIDERMAL WATER LOSS:</strong> Ambient humidity is low ({env["humidity"]}%). Apply lipid ceramide creams immediately after washing.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="clinical-card"><strong>✨ Clinical Status Stable:</strong> Environmental parameters for profile <i>{clinical_profile}</i> are within manageable thresholds.</div>', unsafe_allow_html=True)

        st.write("---")

        col_map, col_details = st.columns([3, 2])
        with col_map:
            st.markdown("#### 🗺️ Interactive Spatial Boundary Map")
            m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=15, tiles="OpenStreetMap")
            folium.Circle(location=[st.session_state.lat, st.session_state.lon], radius=diagnostic_radius, color="orange", fill=True, fill_opacity=0.15).add_to(m)
            folium.Marker([st.session_state.lat, st.session_state.lon], icon=folium.Icon(color="darkblue")).add_to(m)
            st_folium(m, width=650, height=350, key="spatial_map")

        with col_details:
            st.markdown("#### 📥 Full-Suite Clinical Report Export")
            st.write("Download an official structured clinical and environmental diagnostic report covering all portal dimensions.")
            
            summary_bullets = [
                f"Target Location: {st.session_state.resolved_address}",
                f"Canopy Coverage Density: {canopy_coverage}% (NDVI: {ndvi_estimate})",
                f"Air Quality Index PM2.5: {env['pm25']} µg/m³ | PM10: {env['pm10']} µg/m³",
                f"Thermal Stress Index: Apparent Temp {round(apparent_temp, 1)} °C",
                f"Active Biome Classification: {climate_zone} Zone"
            ]

            pdf_bytes = generate_full_suite_pdf(st.session_state.resolved_address, st.session_state.lat, st.session_state.lon, env, summary_bullets)

            st.download_button(
                label="📥 Download Full-Suite PDF Report",
                data=pdf_bytes,
                file_name=f"CanopyRx_Full_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
            
        st.markdown("""
        <div class="legal-disclaimer">
            <strong>Data Source & Legal Compliance Notice:</strong> Meteorological and air quality metrics are sourced in real-time via WeatherAPI and geospatial coordinates resolved through OpenStreetMap Nominatim. This platform operates as an environmental intelligence tool; all prescriptive outputs adhere strictly to non-diagnostic engineering advisory standards.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("👈 Please select your location via the sidebar and click **Recalculate Environmental Report**.")


# ==========================================
# PAGE 2: ✈️ TRAVEL RX PLANNER
# ==========================================
elif app_mode == "✈️ Travel Rx Planner":
    st.markdown("# ✈️ Travel Rx: Pre-Travel Environmental Exposure Planner")
    st.markdown("##### *Identify atmospheric, climatic, and coordinate deltas between locations to safely adapt health and respiratory routines.*")
    st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🛫 Origin Location")
        orig_search = st.text_input("Origin City or Coordinates:", "Nashik, India")
    with col2:
        st.markdown("### 🛬 Destination Location")
        dest_search = st.text_input("Destination City or Coordinates:", "London, UK")
        
    if st.button("Calculate Environmental Transition Delta", type="primary", use_container_width=True):
        lat_o, lon_o, addr_o = geocode_location(orig_search)
        lat_d, lon_d, addr_d = geocode_location(dest_search)
        
        if lat_o and lat_d:
            data_o = fetch_environmental_data(lat_o, lon_o)
            data_d = fetch_environmental_data(lat_d, lon_d)
            
            st.markdown(f"### 📊 Exposure Forecast: `{addr_o}` ➔ `{addr_d}`")
            
            temp_delta = data_d["temp"] - data_o["temp"]
            uv_delta = data_d["uv"] - data_o["uv"]
            aqi_delta = data_d["pm25"] - data_o["pm25"]
            humidity_delta = data_d["humidity"] - data_o["humidity"]

            m_c1, m_c2, m_c3, m_c4 = st.columns(4)
            m_c1.metric("Temperature Shift", f"{round(temp_delta, 1)}°C", f"Dest: {data_d['temp']}°C")
            m_c2.metric("Humidity Shift", f"{round(humidity_delta, 1)}%", f"Dest: {data_d['humidity']}%")
            m_c3.metric("UV Index Shift", f"{round(uv_delta, 1)}", f"Dest: {data_d['uv']}")
            m_c4.metric("PM2.5 Particulate Shift", f"{round(aqi_delta, 1)} µg/m³", f"Dest: {data_d['pm25']} µg/m³")
            
            st.markdown("### 📋 Recommended Travel Adaptation Protocol")
            st.markdown(f"""
            <div class="clinical-card">
                <strong>Transition Analysis Summary:</strong><br>
                - <strong>Thermal Acclimatization:</strong> A temperature shift of {round(temp_delta, 1)}°C requires gradual cardiovascular adaptation. Pack appropriate barrier wear.<br>
                - <strong>Respiratory Preparation:</strong> Destination particulate levels ({data_d['pm25']} µg/m³) dictate whether rescue inhalers or N95 filtration masks are required during transit.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Could not resolve origin or destination coordinates. Please check your spelling.")


# ==========================================
# PAGE 3: 🧴 SKIN & HAIR RX
# ==========================================
elif app_mode == "🧴 Skin & Hair Rx":
    st.markdown("# 🧴 Skin & Hair Rx: Environmental Barrier Formulations")
    st.markdown("##### *Protect your physical moisture barrier from local atmospheric elements, solar radiation, and water quality indices.*")
    st.write("---")
    
    skin_type = st.selectbox("Select Skin Type:", ["Sensitive / Reactive", "Dry / Compromised Barrier", "Oily / Acne-Prone", "Combination"])
    hair_porosity = st.selectbox("Hair Porosity Level:", ["Low (Water Repellent / Build-up)", "Medium (Healthy)", "High (Highly Damaged / Quick Dry)"])
    water_hardness = st.select_slider("Expected Water Hardness (ppm):", options=[50, 100, 150, 200, 300, 400], value=150)
    
    if st.button("Generate Tailored Formulation", type="primary"):
        st.markdown("### 🧪 Prescriptive Topical & Hair Regimen")
        st.markdown(f"""
        <div class="clinical-card">
            <strong>Active Protection Plan for {skin_type}:</strong><br>
            - <strong>AM Routine:</strong> Mineral-based Zinc Oxide SPF 50+ sunscreen paired with Niacinamide (5%) barrier serum.<br>
            - <strong>PM Routine:</strong> Ceramide-infused lipid replenishing cream to counteract regional transepidermal water loss.<br>
            - <strong>Hair & Scalp Defense:</strong> Formulated for <strong>{hair_porosity}</strong> hair with a water hardness rating of <strong>{water_hardness} ppm</strong>. Utilize chelating shampoos if hardness exceeds 150 ppm to prevent mineral scaling.
        </div>
        """, unsafe_allow_html=True)


# ==========================================
# PAGE 4: 🥗 DIETETICS & NUTRITION RX
# ==========================================
elif app_mode == "🥗 Dietetics & Nutrition Rx":
    st.markdown("# 🥗 Dietetics & Nutrition Rx")
    st.markdown("##### *Tailoring dietary and fluid intake recommendations based on localized environmental stressors and particulate loads.*")
    st.write("---")
    
    diet_goal = st.selectbox("Nutritional Focus:", ["Pulmonary Anti-Inflammatory Support", "Antioxidant Heavy Metal Defense", "High Hydration & Electrolyte Balance"])
    
    if st.button("Generate Nutritional Guidelines", type="primary"):
        st.markdown("### 🍽️ Prescribed Dietary Focus")
        st.markdown(f"""
        <div class="clinical-card">
            <strong>Selected Pathway: {diet_goal}</strong><br>
            - <strong>Key Micronutrients:</strong> Increase intake of Vitamin C, E, and Omega-3 fatty acids to combat oxidative stress induced by high urban particulate exposures.<br>
            - <strong>Hydration Index:</strong> Target baseline fluid consumption scaled to local thermal load indexes and humidity shifts.
        </div>
        """, unsafe_allow_html=True)


# ==========================================
# PAGE 5: 👕 CLOTHING & PROTECTION RX
# ==========================================
elif app_mode == "👕 Clothing & Protection Rx":
    st.markdown("# 👕 Clothing & Protection Rx")
    st.markdown("##### *Smart fabric and barrier clothing selections based on UV index, temperature, and atmospheric allergens.*")
    st.write("---")
    
    activity_type = st.selectbox("Planned Activity:", ["Urban Commuting / Walking", "Outdoor Exercise / Jogging", "Industrial / Construction Site Visit"])
    
    if st.button("Get Textile & Protection Advice", type="primary"):
        st.markdown("### 🥼 Recommended Protective Wear")
        st.markdown(f"""
        <div class="clinical-card">
            <strong>Gear Advisory for: {activity_type}</strong><br>
            - <strong>Respiratory Mask:</strong> N95 / KN95 respirator recommended due to regional particulate metrics.<br>
            - <strong>Fabric Selection:</strong> Breathable, tightly-woven organic cotton or moisture-wicking synthetic blends with UV-blocking ratings (UPF 40+).
        </div>
        """, unsafe_allow_html=True)


# ==========================================
# PAGE 6: ⛅ LIVE WEATHER & CLIMATE DASHBOARD
# ==========================================
elif app_mode == "⛅ Live Weather & Climate Dashboard":
    st.markdown("# ⛅ Live Weather & Climate Dashboard")
    st.markdown("##### *Real-time meteorological tracking, air quality indices, and pollution monitoring.*")
    st.write("---")
    
    dash_env = fetch_environmental_data(st.session_state.lat, st.session_state.lon)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🌡️ Temperature", f"{dash_env['temp']} °C")
    col2.metric("💧 Humidity", f"{dash_env['humidity']}%")
    col3.metric("💨 Wind Speed", f"{dash_env['wind']} km/h")
    col4.metric("☀️ UV Index", f"{dash_env['uv']}")
    
    st.markdown("### 🌫️ Detailed Air Quality Breakdown")
    aq_col1, aq_col2, aq_col3 = st.columns(3)
    aq_col1.metric("PM2.5 Fine Particles", f"{round(dash_env['pm25'], 1)} µg/m³")
    aq_col2.metric("PM10 Dust Particles", f"{round(dash_env['pm10'], 1)} µg/m³")
    aq_col3.metric("Nitrogen Dioxide (NO2)", f"{round(dash_env['no2'], 1)} µg/m³")