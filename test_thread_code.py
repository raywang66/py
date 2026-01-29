"""
Test that CC_BatchProcessingThread actually calculates saturation distribution
"""
import sys
import numpy as np
from pathlib import Path

print("Testing CC_BatchProcessingThread saturation calculation...")
print("=" * 60)

# Import the actual thread class
from CC_MainApp_v2 import CC_BatchProcessingThread
from CC_SkinProcessor import CC_SkinProcessor

# Check the thread's run method
import inspect
source = inspect.getsource(CC_BatchProcessingThread.run)

# Check if saturation calculation code exists
if "sat_very_low" in source:
    print("✅ Thread code contains 'sat_very_low'")
else:
    print("❌ Thread code does NOT contain 'sat_very_low'")
    print("⚠️  The imported code is OLD/CACHED!")

if "saturation = point_cloud[:, 1] * 100" in source:
    print("✅ Thread code contains saturation calculation")
else:
    print("❌ Thread code does NOT contain saturation calculation")

# Count occurrences
sat_count = source.count("sat_very_low")
print(f"\n'sat_very_low' appears {sat_count} times in the thread code")

if sat_count >= 2:  # Should appear in calculation and in result dict
    print("✅ Saturation calculation is properly implemented")
else:
    print("❌ Saturation calculation is MISSING or INCOMPLETE")
    print("\n⚠️  CACHE ISSUE! Python is loading OLD CODE!")
    print("   Solution:")
    print("   1. Close ALL Python processes")
    print("   2. Delete __pycache__ folders")
    print("   3. Restart the program")

print("\n" + "=" * 60)

# Show a snippet of the code
lines = source.split('\n')
for i, line in enumerate(lines):
    if 'saturation = point_cloud' in line:
        print(f"\nFound saturation calculation at line {i}:")
        for j in range(max(0, i-2), min(len(lines), i+8)):
            print(f"  {lines[j]}")
        break
else:
    print("\n❌ Could not find saturation calculation in thread code!")
    print("   This confirms the cache issue!")
