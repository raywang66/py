"""
Direct test: Check if sat_vl variables would cause NameError
"""

# Simulate what happens in _on_batch_finished
result = {
    'path': 'test.jpg',
    'success': True,
    'sat_very_low': 10.5,
    'sat_low': 20.3,
    'sat_normal': 50.2,
    'sat_high': 15.0,
    'sat_very_high': 4.0
}

print("Testing variable extraction...")

try:
    # This is what the code SHOULD do
    sat_vl = result.get('sat_very_low', 0.0)
    sat_l = result.get('sat_low', 0.0)
    sat_n = result.get('sat_normal', 0.0)
    sat_h = result.get('sat_high', 0.0)
    sat_vh = result.get('sat_very_high', 0.0)

    print(f"✅ Variables extracted: vl={sat_vl}, l={sat_l}, n={sat_n}, h={sat_h}, vh={sat_vh}")

    # Now use them
    analysis_data = {
        'sat_very_low': sat_vl,
        'sat_low': sat_l,
        'sat_normal': sat_n,
        'sat_high': sat_h,
        'sat_very_high': sat_vh
    }

    print(f"✅ analysis_data created: {analysis_data}")

except NameError as e:
    print(f"❌ NameError: {e}")
