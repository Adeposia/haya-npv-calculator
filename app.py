import streamlit as st
import pandas as pd
import os
from engine.npv import calculate_npv

# ============================================================
# PAGE CONFIG  (must be the first Streamlit command)
# ============================================================
st.set_page_config(
    page_title="HAYA | Unlock Your Rent",
    page_icon="🚌",
    layout="wide",
)

# ============================================================
# BRAND STYLING  (danfo yellow + black)
# This injects custom CSS. You don't need to fully understand
# it — just know it controls colors, buttons, and the banner.
# ============================================================
HAYA_YELLOW = "#FCD116"
HAYA_BLACK = "#1A1A1A"

st.markdown(f"""
<style>
    /* Buttons: black background, yellow text, rounded */
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
    /* The big value number */
    div[data-testid="stMetricValue"] {{
        color: {HAYA_BLACK};
        font-weight: 800;
    }}
    /* Section headers get a yellow underline */
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
<div style="
    background-color:{HAYA_BLACK};
    padding:22px 28px;
    border-radius:14px;
    border-left: 10px solid {HAYA_YELLOW};
    margin-bottom:22px;">
    <h1 style="color:{HAYA_YELLOW}; margin:0; font-size:2.1rem;">
        🚌 HAYA
    </h1>
    <p style="color:#FFFFFF; margin:4px 0 0 0; font-size:1.05rem;">
        Moving out early? Turn your unexpired rent into cash today.
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# MAIN LAYOUT
# ============================================================
col1, col2 = st.columns([1, 1])

with col1:
    st.header("1. Property Details")
    neighborhood = st.selectbox(
        "Neighborhood:",
        ["Lekki Phase 1", "Victoria Island", "Ikoyi", "Ikeja GRA",
         "Surulere", "Yaba", "Other"]
    )
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
    st.header("2. Market Valuation")
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
    st.info(
        f"**High Demand Alert:** We currently have corporate buyers looking "
        f"for **{property_type}** apartments in **{neighborhood}**."
    )

    with st.form("lead_capture_form"):
        st.markdown("Enter your email to match with a buyer and lock in your valuation.")
        user_email = st.text_input("Your Email Address:")
        submitted = st.form_submit_button("👉 Secure My Match")

        if submitted:
            if "@" in user_email and "." in user_email:
                new_lead = pd.DataFrame({
                    "Email": [user_email],
                    "Neighborhood": [neighborhood],
                    "Property": [property_type],
                    "Value Expected (NGN)": [round(results['realizable_value'])]
                })
                if os.path.exists("haya_leads.csv"):
                    new_lead.to_csv("haya_leads.csv", mode="a", header=False, index=False)
                else:
                    new_lead.to_csv("haya_leads.csv", index=False)

                st.success("Success! Our concierge team will email you within 24 hours.")
                st.balloons()
            else:
                st.error("Please enter a valid email address.")

# ============================================================
# ADMIN PANEL
# ============================================================
st.divider()
with st.expander("🔒 Admin Only: View Captured Leads"):
    if os.path.exists("haya_leads.csv"):
        st.dataframe(pd.read_csv("haya_leads.csv"))
    else:
        st.write("No leads captured yet.")
