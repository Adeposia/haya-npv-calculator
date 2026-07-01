import streamlit as st
import folium
from streamlit_folium import st_folium
from engine.npv import calculate_npv

# --- PAGE SETUP ---
st.set_page_config(page_title="HAYA Rent Calculator V2", page_icon="🏠", layout="wide")
st.title("🏠 HAYA: Stranded Rent Valuation")
st.markdown("Calculate the true secondary market value of your unexpired lease in Lagos.")

# --- LAYOUT: Two Columns ---
col1, col2 = st.columns([1, 1])

with col1:
    st.header("1. Lease & Market Data")
    months_left = st.number_input("Months left on your lease:", min_value=1, max_value=24, value=6)
    current_rent_annual = st.number_input("Current annual rent for similar units (₦):", min_value=100000, value=3000000, step=100000)
    
    st.markdown("### Economic Adjustments")
    growth_rate_annual = st.slider("Expected Annual Rent Growth / Inflation (%)", min_value=0.0, max_value=50.0, value=25.0)
    discount_rate_annual = st.slider("Annual Discount Rate / Treasury Yield (%)", min_value=0.0, max_value=30.0, value=18.0)
    friction_pct = st.slider("HAYA + Landlord Consent Fees (%)", min_value=0.0, max_value=20.0, value=10.0)

with col2:
    st.header("2. Valuation Results")
    
    # Run the math from our new engine!
    results = calculate_npv(months_left, current_rent_annual, discount_rate_annual, growth_rate_annual, friction_pct)
    
    st.metric(label="Total Realizable Value (After Fees)", value=f"₦ {results['realizable_value']:,.2f}")
    st.markdown(f"**Gross Market Value:** ₦ {results['gross_pv']:,.2f}")
    st.markdown(f"**Friction Fees:** - ₦ {results['friction_cost']:,.2f}")
    
    st.divider()
    st.markdown("### Area Map")
    # Basic map centered on Lagos (we will upgrade this to GeoJSON later)
    m = folium.Map(location=[6.4474, 3.4883], zoom_start=11) # Centered on Lekki/VI
    st_folium(m, height=300, use_container_width=True)

st.divider()
st.success("Ready to cash out? Join the HAYA waitlist to match with a verified corporate buyer.")
