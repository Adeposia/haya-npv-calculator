import streamlit as st
import pandas as pd
import os
import folium
from streamlit_folium import st_folium
from engine.npv import calculate_npv

# --- PAGE SETUP ---
st.set_page_config(page_title="HAYA Rent Calculator", page_icon="🏠", layout="wide")
st.title("🏠 HAYA: Unlock Your Stranded Rent")

col1, col2 = st.columns([1, 1])

with col1:
    st.header("1. Property Details")
    neighborhood = st.selectbox("Neighborhood:", ["Lekki Phase 1", "Victoria Island", "Ikoyi", "Ikeja GRA", "Surulere", "Yaba", "Other"])
    property_type = st.selectbox("Property Type:", ["1 Bedroom", "2 Bedroom", "3 Bedroom", "Self Contain"])
    months_left = st.number_input("Months left on your lease:", min_value=1, max_value=24, value=6)
    current_rent_annual = st.number_input("Current annual rent for similar units (₦):", min_value=100000, value=3000000, step=100000)
    
    with st.expander("⚙️ Advanced Economic Adjustments"):
        growth_rate_annual = st.slider("Expected Annual Rent Growth / Inflation (%)", 0.0, 50.0, 25.0)
        discount_rate_annual = st.slider("Annual Discount Rate / Treasury Yield (%)", 0.0, 30.0, 18.0)
        friction_pct = st.slider("HAYA + Landlord Consent Fees (%)", 0.0, 20.0, 10.0)

with col2:
    st.header("2. Market Valuation")
    results = calculate_npv(months_left, current_rent_annual, discount_rate_annual, growth_rate_annual, friction_pct)
    
    st.metric(label="Total Realizable Value (After Fees)", value=f"₦ {results['realizable_value']:,.2f}")
    st.markdown(f"**Gross Market Value:** ₦ {results['gross_pv']:,.2f}  |  **Friction Fees:** - ₦ {results['friction_cost']:,.2f}")
    
    st.divider()
    
    # --- LEAD CAPTURE FORM ---
    st.subheader("🚀 Ready to Cash Out?")
    st.info(f"**High Demand Alert:** We currently have corporate buyers looking for **{property_type}** apartments in **{neighborhood}**.")
    
    with st.form("lead_capture_form"):
        st.markdown("Enter your email to securely match with a buyer and lock in your valuation.")
        user_email = st.text_input("Your Email Address:")
        submitted = st.form_submit_button("👉 Secure My Match")
        
        if submitted:
            if "@" in user_email:
                # Create a DataFrame with the new lead
                new_lead = pd.DataFrame({
                    "Email": [user_email], 
                    "Neighborhood": [neighborhood], 
                    "Property": [property_type], 
                    "Value Expected (NGN)": [round(results['realizable_value'])]
                })
                
                # Save it to a CSV file
                if os.path.exists("haya_leads.csv"):
                    new_lead.to_csv("haya_leads.csv", mode="a", header=False, index=False)
                else:
                    new_lead.to_csv("haya_leads.csv", index=False)
                    
                st.success("Success! Our concierge team will email you within 24 hours.")
                st.balloons() # Adds a fun animation on success!
            else:
                st.error("Please enter a valid email address.")

# --- ADMIN PANEL (Only you will know this is down here) ---
st.divider()
with st.expander("🔒 Admin Only: View Captured Leads"):
    if os.path.exists("haya_leads.csv"):
        df_leads = pd.read_csv("haya_leads.csv")
        st.dataframe(df_leads)
    else:
        st.write("No leads captured yet.")
