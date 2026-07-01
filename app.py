import streamlit as st
import pandas as pd
import os
import json
import folium
from streamlit_folium import st_folium
from engine.npv import calculate_npv

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="HAYA | Unlock Your Rent",
    page_icon="🚌",
    layout="wide",
)

HAYA_YELLOW = "#FCD116"
HAYA_BLACK = "#1A1A1A"

# ============================================================
# BRAND STYLING (from Phase 1)
# ============================================================
st.markdown(f"""
<style>
    .stButton > button, .stFormSubmitButton > button {{
        background-color: {HAYA_BLACK};
        color: {HAYA_YELLOW};
        font-weight: 700;
        border: 2px solid {HAYA_BLACK};
        border-radius: 10px;
        padding: 0.6rem 1rem;
        width: 100%;
        transition: all 0.15s ease-in-out;
    }}
    .stButton > button:hover, .stFormSubmitButton > button:hover {{
        background-color: {HAYA_YELLOW};
        color: {HAYA_BLACK};
        border: 2px solid {HAYA_BLACK};
    }}
    div[data-testid="stMetricValue"] {{
        color: {HAYA_BLACK};
        font-weight: 800;
    }}
    h2, h3 {{
        border-bottom: 3px solid {HAYA_YELLOW};
        padding-bottom: 4px;
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# BRANDED HEADER BANNER
# ============================================================
st.markdown(f"""
<div style="background-color:{HAYA_BLACK}; padding:22px 28px;
    border-radius:14px; border-left:10px solid {HAYA_YELLOW};
    margin-bottom:22px;">
    <h1 style="color:{HAYA_YELLOW}; margin:0; font-size:2.1rem;">🚌 HAYA</h1>
    <p style="color:#FFFFFF; margin:4px 0 0 0; font-size:1.05rem;">
        Moving out early? Turn your unexpired rent into cash today.
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# LOAD THE WARD MAP DATA
# @st.cache_data means: load the big file ONCE, then reuse it.
# Without this, the 750KB file would reload on every click (slow).
# ============================================================
@st.cache_data
def load_wards():
    with open("Lagos_SOW_Wards.geojson", "r", encoding="utf-8") as f:
        return json.load(f)

wards_geojson = load_wards()

# ============================================================
# STEP 1: THE INTERACTIVE MAP
# ============================================================
st.header("1. Where is your property?")
st.markdown("**Click your ward on the map below** to get started.")

# Read the currently-selected ward from memory (session_state).
# On the very first run there's nothing selected yet.
selected_ward = st.session_state.get("selected_ward")

# This function decides how each ward is colored.
# The selected ward gets a solid yellow fill; the rest are faint.
def style_function(feature):
    name = feature["properties"].get("ward_name")
    if name == selected_ward:
        return {"fillColor": HAYA_YELLOW, "color": HAYA_BLACK,
                "weight": 2.5, "fillOpacity": 0.75}
    return {"fillColor": HAYA_YELLOW, "color": HAYA_BLACK,
            "weight": 0.4, "fillOpacity": 0.08}

# This makes a ward glow when you hover over it.
def highlight_function(feature):
    return {"fillColor": HAYA_YELLOW, "color": HAYA_BLACK,
            "weight": 2, "fillOpacity": 0.45}

# Build the map, centered on Lagos.
m = folium.Map(location=[6.5244, 3.3792], zoom_start=10, tiles="cartodbpositron")

folium.GeoJson(
    wards_geojson,
    name="Lagos Wards",
    style_function=style_function,
    highlight_function=highlight_function,
    tooltip=folium.GeoJsonTooltip(
        fields=["ward_name", "lga_code"],
        aliases=["Ward:", "LGA Code:"],
    ),
).add_to(m)

# Render the map and capture what the user clicked.
map_data = st_folium(m, height=480, use_container_width=True, key="ward_map")

# When a ward is clicked, st_folium returns it in "last_active_drawing".
# We save its details to memory. The "if != " check prevents an
# infinite loop of the page refreshing over and over.
clicked = map_data.get("last_active_drawing")
if clicked:
    props = clicked.get("properties", {})
    new_ward = props.get("ward_name")
    if new_ward and new_ward != st.session_state.get("selected_ward"):
        st.session_state["selected_ward"] = new_ward
        st.session_state["selected_ward_code"] = props.get("ward_code")
        st.session_state["selected_lga"] = props.get("lga_code")
        # Also grab the exact point they clicked (lat/lng)
        pt = map_data.get("last_clicked") or {}
        st.session_state["clicked_lat"] = pt.get("lat")
        st.session_state["clicked_lng"] = pt.get("lng")
        st.rerun()  # refresh so the highlight updates immediately

# Re-read after possible update
selected_ward = st.session_state.get("selected_ward")

if selected_ward:
    st.success(f"📍 Selected ward: **{selected_ward}** "
               f"(LGA code: {st.session_state.get('selected_lga')})")
else:
    st.warning("👆 No ward selected yet — click your area on the map.")

st.divider()

# ============================================================
# STEP 2 & 3: PROPERTY DETAILS + VALUATION
# ============================================================
col1, col2 = st.columns([1, 1])

with col1:
    st.header("2. Property Details")
    property_type = st.selectbox(
        "Property Type:",
        ["1 Bedroom", "2 Bedroom", "3 Bedroom", "Self Contain"]
    )
    months_left = st.number_input(
        "Months left on your lease:", min_value=1, max_value=24, value=6
    )
    current_rent_annual = st.number_input(
        "Current annual rent for similar units (₦):",
        min_value=100000, value=3000000, step=100000
    )

    with st.expander("⚙️ Advanced Economic Adjustments"):
        growth_rate_annual = st.slider(
            "Expected Annual Rent Growth / Inflation (%)", 0.0, 50.0, 25.0
        )
        discount_rate_annual = st.slider(
            "Annual Discount Rate / Treasury Yield (%)", 0.0, 30.0, 18.0
        )
        friction_pct = st.slider(
            "HAYA + Landlord Consent Fees (%)", 0.0, 20.0, 10.0
        )

with col2:
    st.header("3. Market Valuation")
    results = calculate_npv(
        months_left, current_rent_annual,
        discount_rate_annual, growth_rate_annual, friction_pct
    )
    st.metric(
        label="Total Realizable Value (After Fees)",
        value=f"₦ {results['realizable_value']:,.0f}"
    )
    st.markdown(
        f"**Gross Market Value:** ₦ {results['gross_pv']:,.0f}  |  "
        f"**Friction Fees:** – ₦ {results['friction_cost']:,.0f}"
    )

    st.divider()

    # ---- LEAD CAPTURE ----
    st.subheader("🚀 Ready to Cash Out?")
    location_label = selected_ward if selected_ward else "your area"
    st.info(
        f"**High Demand Alert:** We currently have corporate buyers looking "
        f"for **{property_type}** apartments in **{location_label}**."
    )

    with st.form("lead_capture_form"):
        st.markdown("Enter your email to match with a buyer and lock in your valuation.")
        user_email = st.text_input("Your Email Address:")
        submitted = st.form_submit_button("👉 Secure My Match")

        if submitted:
            if not selected_ward:
                st.error("Please click your ward on the map first. 👆")
            elif "@" in user_email and "." in user_email:
                new_lead = pd.DataFrame({
                    "Email": [user_email],
                    "Ward": [selected_ward],
                    "Ward_Code": [st.session_state.get("selected_ward_code")],
                    "LGA_Code": [st.session_state.get("selected_lga")],
                    "Latitude": [st.session_state.get("clicked_lat")],
                    "Longitude": [st.session_state.get("clicked_lng")],
                    "Property": [property_type],
                    "Value Expected (NGN)": [round(results['realizable_value'])]
                })
                if os.path.exists("haya_leads_v2.csv"):
                    new_lead.to_csv("haya_leads_v2.csv", mode="a", header=False, index=False)
                else:
                    new_lead.to_csv("haya_leads_v2.csv", index=False)

                st.success("Success! Our concierge team will email you within 24 hours.")
                st.balloons()
            else:
                st.error("Please enter a valid email address.")

# ============================================================
# ADMIN PANEL
# ============================================================
st.divider()
with st.expander("🔒 Admin Only: View Captured Leads"):
    if os.path.exists("haya_leads_v2.csv"):
        st.dataframe(pd.read_csv("haya_leads_v2.csv"))
    else:
        st.write("No leads captured yet.")
