def calculate_npv(months_left, current_rent_annual, discount_rate_annual, growth_rate_annual, friction_pct):
    current_rent_monthly = current_rent_annual / 12
    r_monthly = (discount_rate_annual / 100) / 12
    g_monthly = (growth_rate_annual / 100) / 12

    gross_pv = 0
    for t in range(1, int(months_left) + 1):
        # Rent grows over time, but cash today is worth more (discounted)
        rent_at_t = current_rent_monthly * ((1 + g_monthly) ** t)
        gross_pv += rent_at_t / ((1 + r_monthly) ** t)
        
    friction_cost = gross_pv * (friction_pct / 100)
    realizable_value = gross_pv - friction_cost
    
    return {
        "gross_pv": gross_pv,
        "friction_cost": friction_cost,
        "realizable_value": realizable_value
    }
