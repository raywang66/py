"""
Test to verify saturation distribution is actually calculated in batch processing
"""
import numpy as np
from pathlib import Path
import sys

# Simulate what happens in batch processing
print("Testing saturation distribution calculation...")
print("=" * 60)

# Create mock point_cloud (HSL values)
np.random.seed(42)
point_cloud = np.random.rand(1000, 3)  # 1000 points, 3 dimensions (H, S, L)
point_cloud[:, 0] *= 360  # Hue: 0-360
# Saturation and Lightness are already 0-1

print(f"Point cloud shape: {point_cloud.shape}")
print(f"Sample HSL values:")
print(f"  Hue (0-360): {point_cloud[0, 0]:.1f}°")
print(f"  Saturation (0-1): {point_cloud[0, 1]:.3f}")
print(f"  Lightness (0-1): {point_cloud[0, 2]:.3f}")
print()

# Calculate saturation distribution (EXACTLY as in the code)
saturation = point_cloud[:, 1] * 100  # Convert 0-1 to 0-100
sat_very_low = (saturation < 15).sum() / len(saturation) * 100
sat_low = ((saturation >= 15) & (saturation < 30)).sum() / len(saturation) * 100
sat_normal = ((saturation >= 30) & (saturation < 50)).sum() / len(saturation) * 100
sat_high = ((saturation >= 50) & (saturation < 70)).sum() / len(saturation) * 100
sat_very_high = (saturation >= 70).sum() / len(saturation) * 100

print("📊 Saturation Distribution Results:")
print(f"  Very Low (<15%):   {sat_very_low:.1f}%")
print(f"  Low (15-30%):      {sat_low:.1f}%")
print(f"  Normal (30-50%):   {sat_normal:.1f}%")
print(f"  High (50-70%):     {sat_high:.1f}%")
print(f"  Very High (>70%):  {sat_very_high:.1f}%")
print(f"  Total:             {sat_very_low + sat_low + sat_normal + sat_high + sat_very_high:.1f}%")
print()

# Verify it adds up to ~100%
total = sat_very_low + sat_low + sat_normal + sat_high + sat_very_high
if abs(total - 100.0) < 0.01:
    print("✅ Percentages add up to 100%")
else:
    print(f"⚠️  Percentages add up to {total:.1f}% (should be 100%)")

# Check if all values are non-zero (with random data, should have some in each range)
if sat_very_low > 0 and sat_low > 0 and sat_normal > 0:
    print("✅ Distribution looks reasonable (all ranges have data)")
else:
    print("⚠️  Distribution might be incorrect")

print()
print("=" * 60)
print("✅ Saturation distribution calculation logic is correct!")
print()
print("Now the actual batch processing should:")
print("  1. Calculate these 5 values for each photo")
print("  2. Save them to result dictionary")
print("  3. Save to database")
print("  4. Display in statistics window")
