from engine.npv import calculate_npv

def test_flat_rent_no_fees():
    # Test: 12 months, 1,200,000 annual rent, 0% growth, 0% discount, 0% fees
    # Result should be exactly 1,200,000
    results = calculate_npv(12, 1200000, 0.0, 0.0, 0.0)
    assert round(results["realizable_value"]) == 1200000

def test_friction_fees():
    # Test: 10% fee on 1,200,000 should equal 120,000
    results = calculate_npv(12, 1200000, 0.0, 0.0, 10.0)
    assert round(results["friction_cost"]) == 120000
