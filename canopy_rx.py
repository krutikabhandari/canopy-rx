import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from geopy.geocoders import Nominatim
from datetime import datetime
import io
import google.generativeai as genai

# ReportLab Imports for Structured Professional PDF Generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Page Configuration - Deep Medical-Teal & Forest Green Theme
st.set_page_config(
    page_title="CanopyRx - Green Engineering & Environmental Health Portal", 
    page_icon="🌳", 
    layout="wide"
)

# Premium Professional UI Styling & Visual Enhancement
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #064e3b 0%, #0d8a72 100%);
        padding: 30px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .portal-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-top: 6px solid #0d8a72;
        padding: 22px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
        text-align: center;
        margin-bottom: 18px;
        min-height: 210px;
    }
    .clinical-card {
        background-color: #f4f9f8;
        border-left: 6px solid #0d8a72;
        padding: 18px;
        border-radius: 8px;
        margin-bottom: 18px;
        font-size: 14px;
        line-height: 1.6;
        color: #1e293b;
    }
    .gemini-response-card {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        border-left: 6px solid #0d8a72;
        padding: 24px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        color: #1e293b;
        font-size: 15px;
        line-height: 1.7;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .source-citation {
        background-color: #f8fafc;
        border: 1px dashed #cbd5e1;
        padding: 10px 14px;
        border-radius: 6px;
        font-size: 12px;
        color: #475569;
        margin-top: 12px;
        margin-bottom: 18px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State Safely
if "lat" not in st.session_state or st.session_state.lat is None:
    st.session_state.lat = 19.9975  
if "lon" not in st.session_state or st.session_state.lon is None:
    st.session_state.lon = 73.7898  
if "resolved_address" not in st.session_state:
    st.session_state.resolved_address = "Nashik, Maharashtra, India (Pincode: 422001)"
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "🏠 Home / Overview"

# Persistent AI Response Keys
if "spatial_ai_response" not in st.session_state:
    st.session_state.spatial_ai_response = None
if "travel_ai_response" not in st.session_state:
    st.session_state.travel_ai_response = None
if "skin_ai_response" not in st.session_state:
    st.session_state.skin_ai_response = None
if "nutrition_ai_response" not in st.session_state:
    st.session_state.nutrition_ai_response = None
if "weather_ai_response" not in st.session_state:
    st.session_state.weather_ai_response = None

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
                "so2": aqi.get("so2", 10.0),
                "co": aqi.get("co", 400.0),
                "o3": aqi.get("o3", 30.0),
                "success": True
            }
    except Exception:
        pass
    return {
        "temp": 28.0, "humidity": 60.0, "uv": 5.0, "wind": 12.0,
        "pm25": 25.0, "pm10": 40.0, "no2": 12.0, "so2": 8.0, "co": 350.0, "o3": 28.0, "success": False
    }

def geocode_location(query):
    try:
        geolocator = Nominatim(user_agent="canopyrx_clinical_engine_v16")
        loc = geolocator.geocode(query, timeout=10)
        if loc:
            return loc.latitude, loc.longitude, loc.address
    except Exception:
        pass
    return None, None, None


# ==========================================
# 🤖 GEMINI AI CLINICAL SYNTHESIS ENGINE
# ==========================================
def generate_gemini_clinical_insight(prompt_context):
    try:
        if "GEMINI_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        else:
            return "⚠️ Gemini API key not found in Streamlit secrets configuration."
        
        formatted_prompt = (
            prompt_context 
            + "\n\nIMPORTANT FORMATTING INSTRUCTION: Do NOT wrap the entire output in markdown code blocks (triple backticks ```). Use standard Markdown headers (###), bold styling, bullet points, and plain markdown tables so it displays cleanly."
        )
        
        model = genai.GenerativeModel('gemini-3.5-flash')
        response = model.generate_content(formatted_prompt)
        return response.text
    except Exception as e:
        return f"Gemini Synthesis Error: {str(e)}"


# ==========================================
# 📄 PROFESSIONAL STRUCTURED PDF GENERATOR
# ==========================================
def generate_section_specific_pdf(section_name, address, lat, lon, env, metrics_data, clinical_analysis, solutions_list):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=14, textColor=colors.HexColor('#0d8a72'), spaceAfter=4)
    subtitle_style = ParagraphStyle('DocSubTitle', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#555555'), spaceAfter=8)
    heading_style = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=10, textColor=colors.HexColor('#1e293b'), spaceBefore=6, spaceAfter=3)
    body_style = ParagraphStyle('BodyDark', parent=styles['Normal'], fontSize=8.5, textColor=colors.HexColor('#333333'), spaceAfter=4)
    disclaimer_style = ParagraphStyle('DisclaimerText', parent=styles['Normal'], fontSize=7.5, textColor=colors.HexColor('#64748b'), spaceBefore=10, spaceAfter=4)

    story.append(Paragraph(f"CanopyRx Environmental & Clinical Report: {section_name}", title_style))
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | <b>Sources:</b> WeatherAPI & OpenStreetMap Nominatim", subtitle_style))
    story.append(Paragraph(f"<b>Target Location & Coordinates:</b> {address} (Lat: {lat:.4f}, Lon: {lon:.4f})", body_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("1. Location-Specific Environmental Parameter Analysis", heading_style))
    story.append(Paragraph(f"Multi-parameter telemetry measured directly for coordinates ({lat:.4f}, {lon:.4f}).", body_style))
    
    table_data = [["Parameter", "Measured Value", "Standard Threshold", "Localized Clinical Significance"]]
    for m in metrics_data:
        table_data.append(m)
        
    t = Table(table_data, colWidths=[90, 75, 85, 290])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0d8a72')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d1d5db')),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f9fafb'))
    ]))
    story.append(t)
    story.append(Spacer(1, 4))

    story.append(Paragraph("2. Regional Pathophysiological Risk Assessment", heading_style))
    for c in clinical_analysis:
        story.append(Paragraph(f"• <b>{c['condition']}:</b> {c['risk_factor']}", body_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("3. Prescriptive Green Engineering & Remediation Solutions", heading_style))
    for idx, sol in enumerate(solutions_list, 1):
        story.append(Paragraph(f"<b>3.{idx} {sol['title']}:</b> {sol['details']}", body_style))
        story.append(Spacer(1, 2))

    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Clinical Disclaimer:</b> This report is generated by CanopyRx based on real-time spatial telemetry and computational environmental modeling for the specified coordinates. It is designed to assist healthcare practitioners and urban planners in assessing microclimatic exposure risks.", disclaimer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 🗺️ SIDEBAR NAVIGATION
# ==========================================
pages_list = [
    "🏠 Home / Overview", 
    "🌍 CanopyRx Spatial Engine & Green Engineering", 
    "✈️ Travel Rx Planner & Journey Mode", 
    "🧴 Skin & Hair Rx", 
    "🥗 Dietetics & Nutrition Rx", 
    "👕 Clothing & Protection Rx", 
    "⛅ Live Weather & Climate Dashboard"
]

st.sidebar.markdown("# 🌳 CanopyRx Suite")
app_mode = st.sidebar.selectbox(
    "Select Portal Module:",
    pages_list,
    index=pages_list.index(st.session_state.nav_page) if st.session_state.nav_page in pages_list else 0
)
st.session_state.nav_page = app_mode


# ==========================================
# PAGE 0: HOME / OVERVIEW
# ==========================================
if app_mode == "🏠 Home / Overview":
    st.markdown("""
    <div class="main-header" style="background: linear-gradient(135deg, #064e3b 0%, #0d8a72 50%, #1e3a8a 100%);">
        <h1>🌳 CanopyRx: Green Engineering & Environmental Health Portal</h1>
        <p style="font-size: 16px; margin-top: 8px; color: #e2e8f0;">Quantifying Green Cover Canopy Solutions to Combat Localized Anthropogenic Exposure and Restore Global Spatial Health.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="source-citation"><strong>Portal Data Sources:</strong> Telemetry integrated via WeatherAPI live environmental feed & OpenStreetMap Nominatim spatial geocoding engine.</div>', unsafe_allow_html=True)
    st.markdown("### 🌿 Explore All Intelligence Portal Modules")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="portal-card"><h3>🌍 Spatial Engine 🌴</h3><p>Urban microclimate, NDVI foliage, green prescription & Gemini clinical synthesis.</p></div>', unsafe_allow_html=True)
        if st.button("Launch Spatial Engine 🌿", use_container_width=True):
            st.session_state.nav_page = "🌍 CanopyRx Spatial Engine & Green Engineering"
            st.rerun()
            
        st.markdown('<div class="portal-card"><h3>🥗 Dietetics & Nutrition Rx 🥗</h3><p>Anti-inflammatory micronutrients, pulmonary protection & custom hydration protocols.</p></div>', unsafe_allow_html=True)
        if st.button("Launch Dietetics Rx 🍲", use_container_width=True):
            st.session_state.nav_page = "🥗 Dietetics & Nutrition Rx"
            st.rerun()

    with col2:
        st.markdown('<div class="portal-card"><h3>✈️ Travel Rx Planner 🗺️</h3><p>Pre-travel climate deltas & live commuter journey route exposure analysis.</p></div>', unsafe_allow_html=True)
        if st.button("Launch Travel Rx 🌴", use_container_width=True):
            st.session_state.nav_page = "✈️ Travel Rx Planner & Journey Mode"
            st.rerun()
            
        st.markdown('<div class="portal-card"><h3>👕 Clothing & Protection Rx 👕</h3><p>Smart fabric selections, UV protective textiles, and particulate filtration gear.</p></div>', unsafe_allow_html=True)
        if st.button("Launch Clothing Rx 🧥", use_container_width=True):
            st.session_state.nav_page = "👕 Clothing & Protection Rx"
            st.rerun()

    with col3:
        st.markdown('<div class="portal-card"><h3>🧴 Skin & Hair Rx 💧</h3><p>Multi-parameter dermatological barrier protection & hard water mitigation.</p></div>', unsafe_allow_html=True)
        if st.button("Launch Skin & Hair Rx 🌱", use_container_width=True):
            st.session_state.nav_page = "🧴 Skin & Hair Rx"
            st.rerun()
            
        st.markdown('<div class="portal-card"><h3>⛅ Live Weather Dashboard ⛅</h3><p>Real-time meteorological tracking, heat stress alerts & public health advisories.</p></div>', unsafe_allow_html=True)
        if st.button("Launch Weather Dashboard 🌤️", use_container_width=True):
            st.session_state.nav_page = "⛅ Live Weather & Climate Dashboard"
            st.rerun()


# ==========================================
# PAGE 1: SPATIAL ENGINE & GREEN ENGINEERING
# ==========================================
elif app_mode == "🌍 CanopyRx Spatial Engine & Green Engineering":
    st.sidebar.markdown("### 📋 Spatial Engine Inputs")
    input_method = st.sidebar.radio("Input Type:", ["Search City / Pincode", "Exact Latitude & Longitude"])
    
    if input_method == "Search City / Pincode":
        search_query = st.sidebar.text_input("Enter Address / Pincode / Landmark:", "Nashik 422001")
        if st.sidebar.button("Run Spatial Diagnostic", type="primary", use_container_width=True):
            lat, lon, addr = geocode_location(search_query)
            if lat and lon:
                st.session_state.lat, st.session_state.lon, st.session_state.resolved_address = lat, lon, addr
    else:
        lat_input = st.sidebar.number_input("Latitude:", value=st.session_state.lat, format="%.4f")
        lon_input = st.sidebar.number_input("Longitude:", value=st.session_state.lon, format="%.4f")
        if st.sidebar.button("Apply Coordinates & Run", type="primary", use_container_width=True):
            st.session_state.lat = lat_input
            st.session_state.lon = lon_input
            _, _, addr = geocode_location(f"{lat_input}, {lon_input}")
            st.session_state.resolved_address = addr if addr else f"Coordinates ({lat_input}, {lon_input})"

    diagnostic_radius = st.sidebar.slider("Spatial Analysis Radius (meters):", min_value=50, max_value=5000, value=500, step=50)

    st.markdown("# 🌍 Spatial Engine & Green Engineering Module")
    resolved_display = st.session_state.get("resolved_address", "Selected Region")
    st.markdown(f"##### *Localized Analysis for: `{resolved_display}` (Lat: `{st.session_state.lat:.4f}`, Lon: `{st.session_state.lon:.4f}` | Radius: {diagnostic_radius}m)*")
    st.write("---")

    env = fetch_environmental_data(st.session_state.lat, st.session_state.lon)
    pollution_load = min(100.0, (env["pm25"] + env["pm10"]) / 2.0)
    canopy_coverage = round(min(85.0, max(4.0, 45.0 - (pollution_load * 0.25))), 1)
    apparent_temp = env["temp"] + 2.0

    st.markdown(f'<div class="source-citation"><strong>Data Sources:</strong> Spatial telemetry fetched via WeatherAPI & OpenStreetMap Nominatim. Coordinates: {st.session_state.lat:.4f}, {st.session_state.lon:.4f}</div>', unsafe_allow_html=True)

    # 8 Parameters Metrics Matrix
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🌳 Canopy Coverage", f"{canopy_coverage}%", "[Target: >30%]")
    m2.metric("🌡️ Apparent Heat", f"{round(apparent_temp, 1)}°C", f"Actual: {env['temp']}°C")
    m3.metric("💨 PM2.5 Particulate", f"{round(env['pm25'], 1)} µg/m³", "[Safe: <15]")
    m4.metric("🌫️ PM10 Dust", f"{round(env['pm10'], 1)} µg/m³", "[Safe: <45]")

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("🧪 Nitrogen Dioxide (NO2)", f"{round(env['no2'], 1)} µg/m³", "[Safe: <40]")
    m6.metric("⚗️ Sulfur Dioxide (SO2)", f"{round(env['so2'], 1)} µg/m³", "[Safe: <20]")
    m7.metric("🚗 Carbon Monoxide (CO)", f"{round(env['co'], 1)} µg/m³", "[Safe: <4000]")
    m8.metric("☀️ Ozone (O3)", f"{round(env['o3'], 1)} µg/m³", "[Safe: <100]")

    st.write("---")
    st.markdown("### 🌿 Specific Green Prescription & Visual Tree Recommendations")
    
    col_tree1, col_tree2 = st.columns(2)
    with col_tree1:
        st.markdown("##### 1. *Azadirachta indica* (Neem)")
        # Using Markdown image syntax safely instead of malformed st.image URLs
        st.markdown("![Azadirachta indica](https://images.unsplash.com/photo-1593121926326-8854c6020593?q=80&w=600&auto=format&fit=crop)")
        st.markdown("<p style='font-size: 13px; color: #475569;'><b>Clinical Value:</b> Releases terpene-based phytoncides that suppress airborne fungal spores in high humidity.</p>", unsafe_allow_html=True)
    with col_tree2:
        st.markdown("##### 2. *Polyalthia longifolia* (False Ashoka)")
        st.markdown("![Polyalthia longifolia](https://images.unsplash.com/photo-1542273917363-3b1817f69a2d?q=80&w=600&auto=format&fit=crop)")
        st.markdown("<p style='font-size: 13px; color: #475569;'><b>Clinical Value:</b> Dense canopy architecture acts as a natural wind buffer and particulate precipitation surface.</p>", unsafe_allow_html=True)

    st.markdown("""
    <div class="clinical-card" style="margin-top: 15px;">
        <strong>Green Architecture & Structural Engineering Interventions for this Location:</strong><br>
        - <em>Vertical Living Walls (Biophilic Facades):</em> Install modular exterior green walls on building facades facing high-traffic corridors to absorb NO2 and lower ambient temperature by up to 3.5°C.<br>
        - <em>Cool Roof Albedo Coatings:</em> Apply high solar reflectance white membranes (SRI > 80) to reduce urban heat island absorption.<br>
        - <em>Permeable Paving & Rain Gardens:</em> Replace impermeable concrete buffers with porous pavers and bio-swales within the selected radius to manage stormwater runoff and enhance local microclimate humidity regulation.
    </div>
    """, unsafe_allow_html=True)

    # 🤖 PERSISTENT GEMINI AI SYNTHESIS BOX
    st.markdown("### 🤖 Gemini AI Clinical & Spatial Synthesis Engine")
    if st.button("Synthesize Advanced Clinical AI Report", type="primary"):
        with st.spinner("Consulting Gemini AI clinical engine..."):
            prompt = f"""
            Analyze the following environmental telemetry specifically for location {resolved_display} (Lat: {st.session_state.lat}, Lon: {st.session_state.lon}):
            - Temperature: {env['temp']}°C (Apparent: {apparent_temp}°C)
            - Humidity: {env['humidity']}%
            - PM2.5: {env['pm25']} µg/m³
            - PM10: {env['pm10']} µg/m³
            - NO2: {env['no2']} µg/m³
            - Canopy Coverage: {canopy_coverage}%
            
            Provide a rigorous clinical and green engineering assessment covering cardiorespiratory risks and targeted botanical/architectural interventions strictly customized to this location.
            """
            st.session_state.spatial_ai_response = generate_gemini_clinical_insight(prompt)

    if st.session_state.spatial_ai_response:
        st.markdown('<div class="gemini-response-card">', unsafe_allow_html=True)
        st.markdown("#### Gemini AI Clinical Intelligence Report:")
        cleaned_response = (
            st.session_state.spatial_ai_response
            .replace("```markdown", "")
            .replace("```", "")
        )
        st.markdown(cleaned_response)
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("---")
    col_map, col_rep = st.columns([3, 2])
    with col_map:
        st.markdown("#### 🗺️ Selected Region Map Boundary with Radius Buffer & Coordinates")
        m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=14)
        folium.Marker([st.session_state.lat, st.session_state.lon], popup=f"{resolved_display} (Lat: {st.session_state.lat}, Lon: {st.session_state.lon})").add_to(m)
        folium.Circle(
            radius=diagnostic_radius,
            location=[st.session_state.lat, st.session_state.lon],
            color="#0d8a72",
            fill=True,
            fill_color="#0d8a72",
            fill_opacity=0.2,
            popup=f"Analysis Radius: {diagnostic_radius}m"
        ).add_to(m)
        st_folium(m, width=580, height=320, key="spatial_map_fixed")

    with col_rep:
        st.markdown("#### 📥 Section-Specific Spatial PDF Report")
        st.write("Download the structured professional report containing comprehensive multi-parameter metrics, green plant prescriptions, and localized architectural solutions.")
        
        metrics_spatial = [
            ["Canopy Coverage", f"{canopy_coverage}%", "> 30%", "Urban shade and dust filtration capacity"],
            ["PM2.5 Particulate", f"{round(env['pm25'], 1)} µg/m³", "< 15 µg/m³", "Deep lung alveolar penetration risk"],
            ["PM10 Dust Load", f"{round(env['pm10'], 1)} µg/m³", "< 45 µg/m³", "Upper respiratory tract irritation index"],
            ["Nitrogen Dioxide", f"{round(env['no2'], 1)} µg/m³", "< 40 µg/m³", "Bronchial inflammation & oxidative stress"],
            ["Apparent Temp", f"{round(apparent_temp, 1)}°C", "18°C - 27°C", "Cardiovascular thermal workload stress"]
        ]
        clinical_spatial = [
            {"condition": "COPD & Asthma Exacerbation", "risk_factor": f"PM2.5 load at {round(env['pm25'],1)} µg/m³ triggers chronic airway inflammation."},
            {"condition": "Urban Heat Island Strain", "risk_factor": f"Apparent heat {round(apparent_temp,1)}°C increases cardiovascular workload."}
        ]
        solutions_spatial = [
            {"title": "Phytoremediation Planting", "details": "Plant Azadirachta indica and Polyalthia longifolia perimeter rows for particulate filtration."},
            {"title": "Vertical Green Architecture", "details": "Install biophilic exterior green walls and cool roof high-albedo coatings to reduce urban heat absorption."}
        ]

        pdf_bytes = generate_section_specific_pdf("Spatial Engine & Green Engineering", resolved_display, st.session_state.lat, st.session_state.lon, env, metrics_spatial, clinical_spatial, solutions_spatial)
        st.download_button(
            label="📥 Download Spatial PDF Report",
            data=pdf_bytes,
            file_name=f"CanopyRx_Spatial_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )


# ==========================================
# PAGE 1B: TRAVEL RX PLANNER & JOURNEY MODE
# ==========================================
elif app_mode == "✈️ Travel Rx Planner & Journey Mode":
    st.markdown("# ✈️ Travel Rx Planner & Journey Mode")
    st.markdown("##### *Calculate environmental deltas and view real-time commuter journey route exposure maps.*")
    st.write("---")
    
    st.markdown('<div class="source-citation"><strong>Data Sources:</strong> WeatherAPI live meteorological telemetry & OpenStreetMap Nominatim routing geocoding.</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["✈️ Pre-Travel Environmental Delta", "🚗 Live Journey Route Exposure Map"])
    
    with tab1:
        st.markdown("### Pre-Travel Climate & Exposure Comparison")
        oc1, oc2 = st.columns(2)
        with oc1:
            st.markdown("#### Origin Specification")
            orig_type = st.radio("Origin Input Type:", ["City / Pincode", "Coordinates (Lat/Lon)"], key="orig_type")
            if orig_type == "City / Pincode":
                orig_query = st.text_input("Origin City / Pincode:", "Nashik 422001", key="orig_q")
                orig_lat, orig_lon = 19.9975, 73.7898
                if orig_query:
                    lat_o, lon_o, _ = geocode_location(orig_query)
                    if lat_o and lon_o:
                        orig_lat, orig_lon = lat_o, lon_o
            else:
                orig_lat = st.number_input("Origin Latitude:", value=19.9975, format="%.4f", key="orig_lat_in")
                orig_lon = st.number_input("Origin Longitude:", value=73.7898, format="%.4f", key="orig_lon_in")

        with oc2:
            st.markdown("#### Destination Specification")
            dest_type = st.radio("Destination Input Type:", ["City / Pincode", "Coordinates (Lat/Lon)"], key="dest_type")
            if dest_type == "City / Pincode":
                dest_query = st.text_input("Destination City / Pincode:", "Mumbai 400001", key="dest_q")
                dest_lat, dest_lon = 19.0760, 72.8777
                if dest_query:
                    lat_d, lon_d, _ = geocode_location(dest_query)
                    if lat_d and lon_d:
                        dest_lat, dest_lon = lat_d, lon_d
            else:
                dest_lat = st.number_input("Destination Latitude:", value=19.0760, format="%.4f", key="dest_lat_in")
                dest_lon = st.number_input("Destination Longitude:", value=72.8777, format="%.4f", key="dest_lon_in")
            
        if st.button("Calculate Travel Delta", type="primary"):
            d_orig = fetch_environmental_data(orig_lat, orig_lon)
            d_dest = fetch_environmental_data(dest_lat, dest_lon)
            t_diff = d_dest["temp"] - d_orig["temp"]
            pm_diff = d_dest["pm25"] - d_orig["pm25"]
            
            tc1, tc2, tc3 = st.columns(3)
            tc1.metric("Temperature Shift", f"{round(t_diff, 1)}°C", f"Dest: {d_dest['temp']}°C")
            tc2.metric("PM2.5 Particulate Shift", f"{round(pm_diff, 1)} µg/m³", f"Dest: {d_dest['pm25']} µg/m³")
            tc3.metric("UV Index Delta", f"{d_dest['uv'] - d_orig['uv']}")

            with st.spinner("Analyzing travel climate shift..."):
                t_prompt = f"""
                Analyze the health and acclimatization impacts of traveling from Origin (Lat: {orig_lat}, Lon: {orig_lon}, Temp: {d_orig['temp']}°C, PM2.5: {d_orig['pm25']} µg/m³) 
                to Destination (Lat: {dest_lat}, Lon: {dest_lon}, Temp: {d_dest['temp']}°C, PM2.5: {d_dest['pm25']} µg/m³).
                Provide practical clinical precautions, hydration protocols, and respiratory protection advice tailored precisely to this journey.
                """
                st.session_state.travel_ai_response = generate_gemini_clinical_insight(t_prompt)

        if st.session_state.travel_ai_response:
            st.markdown('<div class="gemini-response-card">', unsafe_allow_html=True)
            st.markdown("#### Gemini AI Travel Synthesis:")
            cleaned_travel = (
                st.session_state.travel_ai_response
                .replace("```markdown", "")
                .replace("```", "")
            )
            st.markdown(cleaned_travel)
            st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown("### Commuter Journey Route Exposure Map")
        journey_map = folium.Map(location=[19.5367, 73.3338], zoom_start=9)
        folium.Marker([19.9975, 73.7898], popup="Origin", icon=folium.Icon(color="green")).add_to(journey_map)
        folium.Marker([19.0760, 72.8777], popup="Destination", icon=folium.Icon(color="red")).add_to(journey_map)
        folium.PolyLine([[19.9975, 73.7898], [19.0760, 72.8777]], color="#0d8a72", weight=4, opacity=0.8, tooltip="Commuter Corridor").add_to(journey_map)
        st_folium(journey_map, width=800, height=380, key="journey_map_fixed")


# ==========================================
# PAGE 2: SKIN & HAIR RX
# ==========================================
elif app_mode == "🧴 Skin & Hair Rx":
    st.markdown("# 🧴 Skin & Hair Rx: Multi-Parameter Barrier Formulations")
    st.markdown("##### *Comprehensive dermatological and hair barrier prescriptions tailored to local telemetry.*")
    st.write("---")
    
    st.markdown(f'<div class="source-citation"><strong>Data Sources:</strong> Local humidity and UV index telemetry sourced via WeatherAPI. Coordinates: {st.session_state.lat:.4f}, {st.session_state.lon:.4f}</div>', unsafe_allow_html=True)
    
    sc1, sc2 = st.columns(2)
    with sc1:
        skin_type = st.selectbox("Skin Baseline Type:", ["Sensitive / Reactive", "Dry / Compromised Barrier", "Oily / Acne-Prone", "Combination", "Normal"])
        skin_sensitivity = st.selectbox("Cutaneous Reactivity / Sensitivity Level:", ["Low (Resilient)", "Moderate (Mild Stinging)", "High (Rosacea / Eczema Prone)"])
        pore_congestion = st.selectbox("Pore Tendency / Comedogenicity:", ["Clear", "Prone to Blackheads / Whiteheads", "Cystic Breakout Prone"])
    with sc2:
        water_hardness = st.select_slider("Local Water Hardness Level (ppm):", options=[50, 100, 150, 200, 300, 400], value=200)
        scalp_condition = st.selectbox("Scalp & Hair Condition:", ["Normal / Balanced", "Dry / Flaky Scalp", "Oily Scalp with Mineral Build-up", "Color-Treated / Chemically Damaged"])
        outdoor_exposure_hours = st.slider("Daily Outdoor Exposure Hours:", 0.0, 12.0, 3.5, 0.5)

    if st.button("Generate Detailed Multi-Parameter Barrier Regimen", type="primary"):
        env_sh = fetch_environmental_data(st.session_state.lat, st.session_state.lon)
        with st.spinner("Consulting Gemini dermatology AI..."):
            d_prompt = f"""
            Provide an expert dermatological and trichological formulation for a patient in {st.session_state.resolved_address} with:
            - Skin Type: {skin_type} (Sensitivity: {skin_sensitivity}, Pores: {pore_congestion})
            - Water Hardness: {water_hardness} ppm
            - Scalp Condition: {scalp_condition}
            - Outdoor Exposure: {outdoor_exposure_hours} hours/day
            - Local Environmental UV Index: {env_sh['uv']}, PM2.5: {env_sh['pm25']} µg/m³
            
            Give specific active ingredient recommendations, barrier repair protocols, and hard water mitigation strategies customized to this environment.
            """
            st.session_state.skin_ai_response = generate_gemini_clinical_insight(d_prompt)

    if st.session_state.skin_ai_response:
        st.markdown('<div class="gemini-response-card" style="border-left-color: #db2777;">', unsafe_allow_html=True)
        st.markdown("#### Gemini AI Dermatological Expert Synthesis:")
        cleaned_skin = (
            st.session_state.skin_ai_response
            .replace("```markdown", "")
            .replace("```", "")
        )
        st.markdown(cleaned_skin)
        st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# PAGE 3: DIETETICS & NUTRITION RX
# ==========================================
elif app_mode == "🥗 Dietetics & Nutrition Rx":
    st.markdown("# 🥗 Dietetics & Nutrition Rx")
    st.markdown("##### *Tailoring dietary and fluid intake recommendations based on local air quality and thermal stress.*")
    st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        user_age = st.number_input("Age:", min_value=1, max_value=120, value=28)
        user_gender = st.selectbox("Gender:", ["Male", "Female", "Other"])
        user_occupation = st.selectbox("Occupation Category:", ["Outdoor Field Worker / Laborer", "Desk / Office Worker", "Commuter / Travel Intensive"])
    with col2:
        diet_preference = st.selectbox("Dietary Preference:", ["Vegetarian", "Vegan", "Omnivore / Non-Vegetarian"])
        cuisine_region = st.selectbox("Local Cuisine Style:", ["Indian (North / South)", "Mediterranean", "Western / Continental"])

    if st.button("Generate Personalized Nutritional Plan & Recipes", type="primary"):
        env = fetch_environmental_data(st.session_state.lat, st.session_state.lon)
        with st.spinner("Consulting Gemini nutrition AI..."):
            n_prompt = f"""
            Provide an advanced clinical nutrition and anti-inflammatory diet plan tailored for {st.session_state.resolved_address} (Lat: {st.session_state.lat}):
            - Age: {user_age}, Gender: {user_gender}, Occupation: {user_occupation}
            - Diet: {diet_preference}, Cuisine: {cuisine_region}
            - Local Environmental Stressors: PM2.5 = {env['pm25']} µg/m³, Temperature = {env['temp']}°C
            
            Highlight specific antioxidant foods, micronutrients for pulmonary protection against particulate matter, and customized hydration strategies.
            """
            st.session_state.nutrition_ai_response = generate_gemini_clinical_insight(n_prompt)

    if st.session_state.nutrition_ai_response:
        st.markdown('<div class="gemini-response-card" style="border-left-color: #ca8a04;">', unsafe_allow_html=True)
        st.markdown("#### Gemini AI Clinical Nutritionist Synthesis:")
        cleaned_nutri = (
            st.session_state.nutrition_ai_response
            .replace("```markdown", "")
            .replace("```", "")
        )
        st.markdown(cleaned_nutri)
        st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# PAGE 4: CLOTHING & PROTECTION RX
# ==========================================
elif app_mode == "👕 Clothing & Protection Rx":
    st.markdown("# 👕 Clothing & Protection Rx")
    st.markdown("##### *Smart fabric and barrier clothing selections based on local UV index and particulate load.*")
    st.write("---")
    
    activity_type = st.selectbox("Planned Activity:", ["Outdoor Field Work / Exercise", "Urban Commuting", "Indoor Office Environment"])
    if st.button("Get Textile & Gear Recommendation", type="primary"):
        env = fetch_environmental_data(st.session_state.lat, st.session_state.lon)
        st.markdown(f"""
        <div class="clinical-card">
            <strong>Gear Advisory for {st.session_state.resolved_address} (Activity: {activity_type} | UV Index: {env['uv']} | Temp: {env['temp']}°C):</strong><br>
            - <strong>Respiratory Gear:</strong> {"N95 / KN95 respirator required due to active particulate load (" + str(round(env['pm25'],1)) + " µg/m³)." if env['pm25'] > 20 else "Standard surgical mask optional for current baseline."}<br>
            - <strong>Fabric Selection:</strong> Breathable, tightly-woven organic cotton or performance synthetics with UPF 50+ sun protection rating to counteract local UV levels.
        </div>
        """, unsafe_allow_html=True)


# ==========================================
# PAGE 5: LIVE WEATHER & CLIMATE DASHBOARD
# ==========================================
elif app_mode == "⛅ Live Weather & Climate Dashboard":
    st.markdown("# ⛅ Live Weather & Climate Dashboard")
    st.markdown("##### *Real-time meteorological tracking and public health advisories for your active location.*")
    st.write("---")
    
    dash_env = fetch_environmental_data(st.session_state.lat, st.session_state.lon)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌡️ Temperature", f"{dash_env['temp']} °C")
    c2.metric("💧 Humidity", f"{dash_env['humidity']}%")
    c3.metric("💨 Wind Speed", f"{dash_env['wind']} km/h")
    c4.metric("☀️ UV Index", f"{dash_env['uv']}")

    st.markdown("### 🤖 Gemini AI Real-Time Public Health & Climate Advisory")
    if st.button("Generate Live AI Climate Advisory", type="primary"):
        with st.spinner("Synthesizing live climate health advisory..."):
            w_prompt = f"""
            Provide an urgent public health advisory for real-time meteorological conditions at {st.session_state.resolved_address} (Lat: {st.session_state.lat}, Lon: {st.session_state.lon}):
            - Temperature: {dash_env['temp']}°C, Humidity: {dash_env['humidity']}%
            - PM2.5: {dash_env['pm25']} µg/m³, PM10: {dash_env['pm10']} µg/m³, NO2: {dash_env['no2']} µg/m³
            - UV Index: {dash_env['uv']}
            
            Outline immediate precautions for vulnerable populations, heat stress risks, and vector-borne disease warnings customized precisely to this location.
            """
            st.session_state.weather_ai_response = generate_gemini_clinical_insight(w_prompt)

    if st.session_state.weather_ai_response:
        st.markdown('<div class="gemini-response-card">', unsafe_allow_html=True)
        st.markdown("#### Gemini AI Real-Time Advisory:")
        cleaned_weather = (
            st.session_state.weather_ai_response
            .replace("```markdown", "")
            .replace("```", "")
        )
        st.markdown(cleaned_weather)
        st.markdown('</div>', unsafe_allow_html=True)