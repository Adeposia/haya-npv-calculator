import streamlit as st
import pandas as pd
import json
from datetime import datetime
import folium
from streamlit_folium import st_folium
import gspread
from google.oauth2.service_account import Credentials
from engine.npv import calculate_npv

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="HAYA | Unlock Your Rent", page_icon="🚌", layout="wide")

HAYA_YELLOW = "#FCD116"
HAYA_BLACK = "#1A1A1A"

# ============================================================
# BRAND STYLING
# ============================================================
st.markdown(f"""
<style>
    .stButton > button, .stFormSubmitButton > button {{
        background-color: {HAYA_BLACK}; color: {HAYA_YELLOW}; font-weight: 700;
        border: 2px solid {HAYA_BLACK}; border-radius: 10px;
        padding: 0.6rem 1rem; width: 100%; transition: all 0.15s ease-in-out;
    }}
    .stButton > button:hover, .stFormSubmitButton > button:hover {{
        background-color: {HAYA_YELLOW}; color: {HAYA_BLACK}; border: 2px solid {HAYA_BLACK};
    }}
    div[data-testid="stMetricValue"] {{ color: {HAYA_BLACK}; font-weight: 800; }}
    h2, h3 {{ border-bottom: 3px solid {HAYA_YELLOW}; padding-bottom: 4px; }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# BRANDED HEADER BANNER
# ============================================================
st.markdown(f"""
<div style="background-color:{HAYA_BLACK}; padding:40px 28px; 
    border-radius:14px; border-left:10px solid {HAYA_YELLOW}; 
    margin-bottom:22px; text-align: center;">
    <h1 style="color:{HAYA_YELLOW}; margin:0; font-size:3.5rem;">🚌 HAYA</h1>
    <p style="color:#FFFFFF; margin:10px 0 0 0; font-size:1.3rem;">
        Moving out early? Turn your unexpired rent into cash today.
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# GOOGLE SHEETS CONNECTION
# This connects to your sheet using the "robot account" secret.
# @st.cache_resource means it connects ONCE and reuses it.
# ============================================================
@st.cache_resource
def connect_to_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["app"]["sheet_id"]).sheet1
    return sheet

def save_lead(row_values):
    """Append one lead as a new row in the Google Sheet."""
    sheet = connect_to_sheet()
    sheet.append_row(row_values, value_input_option="USER_ENTERED")

# ============================================================
# LOAD WARD MAP
# ============================================================
@st.cache_data
def load_wards():
    with open("Lagos_SOW_Wards.geojson", "r", encoding="utf-8") as f:
        return json.load(f)

wards_geojson = load_wards()

# ============================================================
# STEP 1: INTERACTIVE MAP
# ============================================================
st.header("1. Where is your property?")
st.markdown("**Click your ward on the map below** to get started.")

selected_ward = st.session_state.get("selected_ward")

def style_function(feature):
    name = feature["properties"].get("ward_name")
    if name == selected_ward:
        return {"fillColor": HAYA_YELLOW, "color": HAYA_BLACK, "weight": 2.5, "fillOpacity": 0.75}
    return {"fillColor": HAYA_YELLOW, "color": HAYA_BLACK, "weight": 0.4, "fillOpacity": 0.08}

def highlight_function(feature):
    return {"fillColor": HAYA_YELLOW, "color": HAYA_BLACK, "weight": 2, "fillOpacity": 0.45}

m = folium.Map(location=[6.5244, 3.3792], zoom_start=10, tiles="cartodbpositron")
folium.GeoJson(
    wards_geojson, name="Lagos Wards",
    style_function=style_function, highlight_function=highlight_function,
    tooltip=folium.GeoJsonTooltip(fields=["ward_name", "lga_code"],
                                  aliases=["Ward:", "LGA Code:"]),
).add_to(m)

map_data = st_folium(m, height=480, use_container_width=True, key="ward_map")

clicked = map_data.get("last_active_drawing")
if clicked:
    props = clicked.get("properties", {})
    new_ward = props.get("ward_name")
    if new_ward and new_ward != st.session_state.get("selected_ward"):
        st.session_state["selected_ward"] = new_ward
        st.session_state["selected_ward_code"] = props.get("ward_code")
        st.session_state["selected_lga"] = props.get("lga_code")
        pt = map_data.get("last_clicked") or {}
        st.session_state["clicked_lat"] = pt.get("lat")
        st.session_state["clicked_lng"] = pt.get("lng")
        st.rerun()

selected_ward = st.session_state.get("selected_ward")
if selected_ward:
    st.success(f"📍 Selected ward: **{selected_ward}** (LGA code: {st.session_state.get('selected_lga')})")
else:
    st.warning("👆 No ward selected yet — click your area on the map.")

st.divider()

# ============================================================
# STEP 2 & 3: DETAILS + VALUATION
# ============================================================
col1, col2 = st.columns([1, 1])

with col1:
    st.header("2. Property Details")
    property_type = st.selectbox("Property Type:",
        ["1 Bedroom", "2 Bedroom", "3 Bedroom", "Self Contain"])
    months_left = st.number_input("Months left on your lease:", min_value=1, max_value=24, value=6)
    current_rent_annual = st.number_input("Current annual rent for similar units (₦):",
        min_value=100000, value=3000000, step=100000)

    with st.expander("⚙️ Advanced Economic Adjustments"):
        growth_rate_annual = st.slider("Expected Annual Rent Growth / Inflation (%)", 0.0, 50.0, 25.0)
        discount_rate_annual = st.slider("Annual Discount Rate / Treasury Yield (%)", 0.0, 30.0, 18.0)
        friction_pct = st.slider("HAYA + Landlord Consent Fees (%)", 0.0, 20.0, 10.0)

with col2:
    st.header("3. Market Valuation")
    results = calculate_npv(months_left, current_rent_annual,
                            discount_rate_annual, growth_rate_annual, friction_pct)
    st.metric(label="Total Realizable Value (After Fees)",
              value=f"₦ {results['realizable_value']:,.0f}")
    st.markdown(f"**Gross Market Value:** ₦ {results['gross_pv']:,.0f}  |  "
                f"**Friction Fees:** – ₦ {results['friction_cost']:,.0f}")

    st.divider()

    st.subheader("Ready to Cash Out?")
    location_label = selected_ward if selected_ward else "your area"
    st.info(f"**High Demand Alert:** We currently have corporate buyers looking "
            f"for **{property_type}** apartments in **{location_label}**.")

    with st.form("lead_capture_form"):
        st.markdown("Enter your email to match with a buyer and lock in your valuation.")
        user_email = st.text_input("Your Email Address:")
        consent = st.checkbox("I agree to be contacted by HAYA about my valuation.")
        submitted = st.form_submit_button("👉 Secure My Match")

        if submitted:
            if not selected_ward:
                st.error("Please click your ward on the map first. 👆")
            elif "@" not in user_email or "." not in user_email:
                st.error("Please enter a valid email address.")
            elif not consent:
                st.error("Please tick the consent box so we can contact you.")
            else:
                try:
                    save_lead([
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        user_email,
                        selected_ward,
                        st.session_state.get("selected_ward_code"),
                        st.session_state.get("selected_lga"),
                        st.session_state.get("clicked_lat"),
                        st.session_state.get("clicked_lng"),
                        property_type,
                        round(results["realizable_value"]),
                    ])
                    st.success("Success! Our concierge team will email you within 24 hours.")
                    st.balloons()
                except Exception as e:
                    st.error("Something went wrong saving your details. Please try again.")
                    # For your eyes during setup — remove later if you like:
                    st.caption(f"Debug: {e}")

# ============================================================
# ADMIN PANEL (now password-protected)
# ============================================================
st.divider()
with st.expander("🔒 Admin Only"):
    pw = st.text_input("Admin password:", type="password")
    if pw:
        if pw == st.secrets["app"]["admin_password"]:
            try:
                sheet = connect_to_sheet()
                records = sheet.get_all_records()
                if records:
                    st.dataframe(pd.DataFrame(records))
                else:
                    st.write("No leads captured yet.")
            except Exception as e:
                st.error(f"Could not load leads: {e}")
        else:
            st.error("Incorrect password.")
