import numpy as np
from sklearn.cluster import KMeans
import json


def categorize_packet_stats(durations, power_levels, n_clusters=3):
    # Ensure input arrays are numpy arrays
    durations = np.array(durations).reshape(-1, 1)  # Reshape for K-means
    power_levels = np.array(power_levels)

    # Apply K-means clustering to categorize packet durations
    kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(durations)
    labels = kmeans.labels_

    # Initialize the result dictionary
    stats = {}

    for category in range(n_clusters):
        # Find indices that fall into the current category
        indices = np.where(labels == category)[0]

        # Extract corresponding durations and power levels for the current category
        category_durations = durations[indices].flatten()
        category_power_levels = power_levels[indices]

        # Calculate statistics
        stats[f'category_{category}'] = {
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

stats = categorize_packet_stats(durations, power_levels, n_clusters=3)
print(stats)
y = json.dumps(stats, indent=4)
pass
# print(json.dumps(stats, indent=4))
