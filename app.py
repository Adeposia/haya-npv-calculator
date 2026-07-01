import streamlit as st
from engine.npv import calculate_npv

# --- PAGE SETUP ---
st.set_page_config(page_title="HAYA Rent Calculator", page_icon="🏠", layout="wide")
st.title("🏠 HAYA: Unlock Your Stranded Rent")
st.markdown("Moving out early? Find out exactly how much your unexpired lease in Lagos is worth on the secondary market today.")

# --- LAYOUT: Two Columns ---
col1, col2 = st.columns([1, 1])

with col1:
    st.header("1. Property Details")
    # New Lead-Gen Inputs
    neighborhood = st.selectbox("Neighborhood:", ["Lekki Phase 1", "Victoria Island", "Ikoyi", "Ikeja GRA", "Surulere", "Yaba", "Other"])
    property_type = st.selectbox("Property Type:", ["1 Bedroom", "2 Bedroom", "3 Bedroom", "Self Contain", "Other"])
    
    months_left = st.number_input("Months left on your lease:", min_value=1, max_value=24, value=6)
    current_rent_annual = st.number_input("Current annual rent for similar units (₦):", min_value=100000, value=3000000, step=100000)
    
    # Hide the nerdy math in an expander so it doesn't scare normal users
    with st.expander("⚙️ Advanced Economic Adjustments (Optional)"):
        growth_rate_annual = st.slider("Expected Annual Rent Growth / Inflation (%)", min_value=0.0, max_value=50.0, value=25.0)
        discount_rate_annual = st.slider("Annual Discount Rate / Treasury Yield (%)", min_value=0.0, max_value=30.0, value=18.0)
        friction_pct = st.slider("HAYA + Landlord Consent Fees (%)", min_value=0.0, max_value=20.0, value=10.0)

with col2:
    st.header("2. Market Valuation")
    
    # Run the math
    results = calculate_npv(months_left, current_rent_annual, discount_rate_annual, growth_rate_annual, friction_pct)
    
    st.metric(label="Total Realizable Value (After Fees)", value=f"₦ {results['realizable_value']:,.2f}")
    st.markdown(f"**Gross Market Value:** ₦ {results['gross_pv']:,.2f}")
    st.markdown(f"**Friction Fees:** - ₦ {results['friction_cost']:,.2f}")
    
    st.divider()
    
    # --- THE LEAD GEN HOOK ---
    st.subheader("🚀 Ready to Cash Out?")
    
    # Dynamic text based on their inputs creates urgency
    st.info(f"**High Demand Alert:** We currently have pre-verified corporate buyers actively looking for **{property_type}** apartments in **{neighborhood}**.")
    st.markdown(f"Don't abandon your lease. You can legally transfer your remaining months and walk away with **₦ {results['realizable_value']:,.2f}**.")
    
    # A big, clickable button that goes straight to your waitlist
    st.markdown(
        """
        <a href="https://haya.crd.co/" target="_blank" style="display: block; width: 100%; padding: 15px; background-color: #FF4B4B; color: white; text-align: center; text-decoration: none; font-size: 18px; border-radius: 8px; font-weight: bold;">
            👉 Securely Match With a Buyer Now
        </a>
        """, 
        unsafe_allow_html=True
    )
