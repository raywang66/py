import numpy as np
import json


def categorize_packet_stats(durations, power_levels):
    # Ensure input arrays are numpy arrays
    durations = np.array(durations)
    power_levels = np.array(power_levels)

    # Initialize the result dictionary
    stats = {}

    # Define categories based on packet durations
    categories = {
        'short': (0, 100),  # Example category: short durations between 0 and 100
        'medium': (100, 500),  # Example category: medium durations between 100 and 500
        'long': (500, np.inf)  # Example category: long durations above 500
    }

    for category, (lower_bound, upper_bound) in categories.items():
        # Find indices that fall into the current category
        indices = np.where((durations >= lower_bound) & (durations < upper_bound))

        # Extract corresponding power levels for the current category
        category_durations = durations[indices]
        category_power_levels = power_levels[indices]

        # Calculate statistics
        stats[category] = {
            'count': len(category_durations),
            'average_duration': np.mean(category_durations) if len(category_durations) > 0 else 0,
            'max_duration': np.max(category_durations) if len(category_durations) > 0 else 0,
            'min_duration': np.min(category_durations) if len(category_durations) > 0 else 0,
            'average_power': np.mean(category_power_levels) if len(category_power_levels) > 0 else 0,
            'max_power': np.max(category_power_levels) if len(category_power_levels) > 0 else 0,
            'min_power': np.min(category_power_levels) if len(category_power_levels) > 0 else 0
        }

    return stats


# Example usage:
durations = [50, 150, 300, 450, 600, 700, 50, 150]
power_levels = [10, 20, 30, 40, 50, 60, 15, 25]

stats = categorize_packet_stats(durations, power_levels)
print(stats)
