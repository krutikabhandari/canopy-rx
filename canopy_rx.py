import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np
import pandas as pd
import os

# Page Configuration
st.set_page_config(
    page_title="CanopyRx - Public Environmental Portal", 
    page_icon="🌿", 
    layout="wide"
)

# Header
st.title("🌿 CanopyRx: Climate Medicine & Green Engineering")
st.markdown("### Translating satellite data into public health action for our communities.")
st.write("---")

# --- AUTOMATIC DATA GENERATOR ---
csv_filename = "canopy_environmental_data.csv"
if not os.path.exists(csv_filename):
    np.random.seed(42)
    regions = ["Nashik Industrial Hub (India)", "Jakarta Suburbs (Indonesia)", "Manila Port Zone (Philippines)"]
    data = []
    for _ in range(300):
        reg = np.random.choice(regions)
        if reg == "Nashik Industrial Hub (India)":
            canopy = np.random.uniform(12.0, 19.5)
            temp_offset = np.random.uniform(-0.8, -0.2)
            pm25_reduction = np.random.uniform(5.0, 12.0)
        elif reg == "Jakarta Suburbs (Indonesia)":
            canopy = np.random.uniform(15.0, 24.0)
            temp_offset = np.random.uniform(-1.5, -0.5)
            pm25_reduction = np.random.uniform(10.0, 18.0)
        else:
            canopy = np.random.uniform(8.0, 15.0)
            temp_offset = np.random.uniform(-0.5, 0.1)
            pm25_reduction = np.random.uniform(3.0, 8.0)
            
        data.append({
            "Region": reg,
            "Canopy_Density_Pct": round(canopy, 2),
            "Temp_Offset_Celsius": round(temp_offset, 2),
            "PM25_Abatement_UG": round(pm25_reduction, 2)
        })
    df = pd.DataFrame(data)
    df.to_csv(csv_filename, index=False)

df = pd.read_csv(csv_filename)

# Sidebar Configuration
st.sidebar.header("📍 Diagnostic Engine")
location = st.sidebar.selectbox(
    "Select Target Bounding Coordinate:",
    ["Select a Region...", "Nashik Industrial Hub (India)", "Jakarta Suburbs (Indonesia)", "Manila Port Zone (Philippines)"]
)

# Coordinates for map centering
coords = {
    "Nashik Industrial Hub (India)": [19.9975, 73.7898],
    "Jakarta Suburbs (Indonesia)": [-6.2088, 106.8456],
    "Manila Port Zone (Philippines)": [14.5995, 120.9842]
}

# --- SUB-ZONE MAPPING DATA ---
# This maps out micro-neighborhoods/zones inside each city to showcase on the map
sub_zones = {
    "Nashik Industrial Hub (India)": [
        {"name": "Satpur Industrial Sector", "offset": [0.015, -0.02], "canopy": "9.4%", "status": "Critical", "color": "red", "desc": "High factory emissions, severe concrete density, immediate tree canopy intervention required."},
        {"name": "Ambad Residential Belt", "offset": [-0.01, 0.015], "canopy": "16.2%", "status": "Moderate", "color": "orange", "desc": "Suburban area showing moderate heat island traps. Room for park expansion."},
        {"name": "Pandavleni Green Reserve", "offset": [-0.025, -0.015], "canopy": "28.7%", "status": "Healthy", "color": "green", "desc": "Natural forest canopy providing massive cooling and air-filtering runoffs."}
    ],
    "Jakarta Suburbs (Indonesia)": [
        {"name": "Tanjung Priok Port Zone", "offset": [0.02, -0.025], "canopy": "7.1%", "status": "Critical", "color": "red", "desc": "Dense cargo transport corridor with heavy soot. Lacks critical green shading."},
        {"name": "Kelapa Gading Suburbs", "offset": [-0.01, 0.02], "canopy": "17.8%", "status": "Moderate", "color": "orange", "desc": "Densely populated housing blocks. Urban heat islands forming along paved roads."},
        {"name": "Tebet Eco Park Zone", "offset": [-0.025, -0.01], "canopy": "31.2%", "status": "Healthy", "color": "green", "desc": "High-performing urban forest filtering local PM2.5 and regulating surface heat."}
    ],
    "Manila Port Zone (Philippines)": [
        {"name": "Tondo High-Density District", "offset": [0.012, -0.015], "canopy": "6.2%", "status": "Critical", "color": "red", "desc": "Extremely dense residential and port area. High risk of pediatric asthma due to zero canopy filtration."},
        {"name": "Intramuros Cultural Area", "offset": [-0.005, 0.01], "canopy": "14.9%", "status": "Moderate", "color": "orange", "desc": "Historic plazas offer minimal tree shade, but paved streets retain a lot of heat."},
        {"name": "Rizal Sanctuary Park", "offset": [-0.018, -0.005], "canopy": "29.4%", "status": "Healthy", "color": "green", "desc": "Crucial coastal green shield, actively lowering local temperatures by up to 2°C."}
    ]
}

# Session State
if "diagnostic_active" not in st.session_state:
    st.session_state.diagnostic_active = False
if "prev_location" not in st.session_state:
    st.session_state.prev_location = location
if st.session_state.prev_location != location:
    st.session_state.diagnostic_active = False
    st.session_state.prev_location = location

# --- MAIN PAGE LOGIC ---
if location != "Select a Region...":
    selected_coord = coords[location]
    st.sidebar.success(f"Connected to satellite stream for: {location}")
    
    run_diagnostic_button = st.sidebar.button("Run CanopyRx Clinical Diagnostic")
    if run_diagnostic_button:
        st.session_state.diagnostic_active = True
    
    if st.session_state.diagnostic_active:
        st.subheader(f"Analysis for {location}")
        
        # Calculate Averages
        region_data = df[df['Region'] == location]
        avg_canopy = region_data['Canopy_Density_Pct'].mean()
        avg_temp_offset = region_data['Temp_Offset_Celsius'].mean()
        total_pm_abatement = region_data['PM25_Abatement_UG'].mean()
        
        # Public Health Grade
        if avg_canopy >= 20:
            health_grade = "B (Moderate)"
            grade_color = "orange"
        elif avg_canopy >= 15:
            health_grade = "C (Under Stress)"
            grade_color = "orange"
        else:
            health_grade = "D (Critical/Hazardous)"
            grade_color = "red"

        # Create 2 Columns
        main_col1, main_col2 = st.columns([3, 2])
        
        with main_col1:
            st.markdown("#### Interactive Environmental Risk Zone Map")
            st.caption("🔴 Red = At-Risk Zone | 🟡 Orange = Moderate Zone | 🟢 Green = Safe / Healthy Zone")
            
            # Map centered on target
            m = folium.Map(location=selected_coord, zoom_start=13, tiles="OpenStreetMap")
            
            # Generate and add the neighborhood circles
            for zone in sub_zones[location]:
                zone_coords = [selected_coord[0] + zone["offset"][0], selected_coord[1] + zone["offset"][1]]
                
                # Add transparent overlay circle reflecting risk
                folium.Circle(
                    location=zone_coords,
                    radius=800,
                    color=zone["color"],
                    fill=True,
                    fill_color=zone["color"],
                    fill_opacity=0.35,
                    popup=f"<b>{zone['name']}</b><br>Canopy: {zone['canopy']}<br>Status: {zone['status']}",
                    tooltip=zone["name"]
                ).add_to(m)
                
                # Add marker inside circle
                folium.Marker(
                    location=zone_coords,
                    icon=folium.Icon(color=zone["color"], icon="info-sign")
                ).add_to(m)
                
            st_folium(m, width=700, height=450)
            
        with main_col2:
            st.markdown(f"#### 🏥 Public Health Score: :{grade_color}[{health_grade}]")
            
            st.markdown("### 🗺️ Local Environmental Zones Found:")
            for zone in sub_zones[location]:
                st.markdown(f"**:{zone['color']}[● {zone['name']}] ({zone['status']})**")
                st.markdown(f"* **Local Canopy Cover:** {zone['canopy']}\n* **Risk Profile:** {zone['desc']}")
                st.write("")
        
        st.write("---")
        st.markdown("#### Calculated Environmental Planetary Health Estimates")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label="🌳 Green Cover (Target: 25.0%)", 
                value=f"{avg_canopy:.2f}%", 
                delta=f"{(avg_canopy - 25.0):+.1f}% vs Target", 
                delta_color="normal" if avg_canopy >= 25 else "inverse"
            )
            st.markdown(
                "**What this is:** The percentage of land shaded by tree canopies. \n\n"
                "*Health Impact:* Low cover raises neighborhood stress levels and reduces outdoor physical activity."
            )
            
        with col2:
            st.metric(
                label="🌡️ Cool Down Effect", 
                value=f"{avg_temp_offset:.2f}°C", 
                delta="Direct Relief"
            )
            st.markdown(
                "**What this is:** The average temperature difference generated by urban tree shading.\n\n"
                "*Health Impact:* Every 1°C of cooling cuts heat stroke incidence and lowers domestic AC energy bills."
            )
            
        with col3:
            st.metric(
                label="🍃 Air Pollution Trapped", 
                value=f"{total_pm_abatement:.2f} µg/m³", 
                delta="Direct Filtration"
            )
            st.markdown(
                "**What this is:** Fine dust (PM2.5) successfully filtered by tree leaves instead of entering human lungs.\n\n"
                "*Health Impact:* Cleaner air reduces pediatric asthma flare-ups and chronic respiratory fatigue."
            )

        st.write("---")
        
        st.markdown("### 🛠️ CanopyRx Clinical Prescription: What Can We Do?")
        action_col1, action_col2 = st.columns(2)
        with action_col1:
            st.success("👨‍👩‍👧‍👦 **For the Local Community**")
            st.markdown(
                "* **Plant 'Miyawaki' Mini-Forests:** Grow dense, native plants rapidly in small, empty urban plots.\n"
                "* **Introduce Green Roofs:** Plant low-maintenance vegetation on structural flat roofs.\n"
                "* **Use Permeable Pavements:** Swap concrete pathways with interlocking grid-grass pavers."
            )
        with action_col2:
            st.warning("🏢 **For City Planners & Developers**")
            st.markdown(
                "* **Enforce Canopy Goals:** Mandate a minimum of 25% green cover for all new infrastructure layouts.\n"
                "* **Establish Cooling Corridors:** Route green strips in directions that channel wind to sweep out city heat.\n"
                "* **Industrial Bio-Buffers:** Construct thick, multi-tier vegetation boundaries around industrial hotspots."
            )
            
else:
    st.session_state.diagnostic_active = False
    st.info("👈 Please select a target bounding coordinate in the sidebar to run the CanopyRx model analysis.")
    
    welcome_col1, welcome_col2 = st.columns(2)
    with welcome_col1:
        st.markdown("### ❓ What is CanopyRx?")
        st.write(
            "CanopyRx is an environmental diagnostic platform that treats tree canopies like a **preventative medical prescription** "
            "for cities. By utilizing dynamic satellite feeds, we analyze how urban design directly translates to public respiratory and "
            "cardiovascular health outcomes in local communities."
        )
    with welcome_col2:
        st.markdown("### 📈 How to use this platform:")
        st.write(
            "1. **Select a Target Region** on the sidebar menu.\n"
            "2. Click **Run CanopyRx Clinical Diagnostic**.\n"
            "3. Examine the real-time satellite mapping and biological indicators below it to see if your community is green-healthy or at-risk!"
        )