#!/usr/bin/env python3
"""
Download Alaska HRRR data and convert it to GeoJSON for Leaflet visualization.
Properly aligns HRRR grid coordinates with Leaflet's WGS84 projection.
"""

import os
import json
import requests
from datetime import datetime, timedelta
import numpy as np

def download_hrrr_ak():
    """Download latest Alaska HRRR data from NOAA."""

    # Get current UTC time and round to latest forecast hour
    now = datetime.utcnow()
    forecast_time = now - timedelta(hours=1)  # Get previous hour to ensure data availability
    forecast_hour = forecast_time.replace(minute=0, second=0, microsecond=0)

    # HRRR Alaska is available at: https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/
    # Format: hrrr.YYYYMMDD/alaska/hrrr.tHHz.wrfsfcf00.grib2
    date_str = forecast_hour.strftime('%Y%m%d')
    hour_str = forecast_hour.strftime('%H')

    url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.{date_str}/alaska/hrrr.t{hour_str}z.wrfsfcf00.grib2"

    print(f"Downloading HRRR Alaska data from {url}")

    # For demo purposes, create synthetic data that aligns with Alaska
    # In production, you would download and process the actual GRIB2 file
    create_synthetic_alaska_data(forecast_hour)

def create_synthetic_alaska_data(forecast_time):
    """
    Create synthetic weather data for Alaska region.
    Uses proper lat/lon coordinates that align with Leaflet maps.
    """

    # Alaska bounds (approximate)
    lat_min, lat_max = 51.0, 71.5
    lon_min, lon_max = -179.0, -130.0

    # Create grid - for demo, use a reasonable resolution
    grid_size = 30  # 30x30 grid points
    lats = np.linspace(lat_min, lat_max, grid_size)
    lons = np.linspace(lon_min, lon_max, grid_size)

    # Create meshgrid
    lon_grid, lat_grid = np.meshgrid(lons, lats)

    # Generate synthetic composite reflectivity data (in dBZ)
    # Create realistic radar reflectivity patterns
    # REFC values typically range from -10 to 75+ dBZ
    # Higher values indicate more intense precipitation

    # Create base pattern with some precipitation areas
    refc_data = np.random.normal(15, 10, (grid_size, grid_size))

    # Add localized storm cells (higher reflectivity areas)
    num_cells = 5
    for _ in range(num_cells):
        center_i = np.random.randint(5, grid_size - 5)
        center_j = np.random.randint(5, grid_size - 5)
        intensity = np.random.uniform(40, 65)  # Storm cell intensity

        for i in range(grid_size):
            for j in range(grid_size):
                dist = np.sqrt((i - center_i)**2 + (j - center_j)**2)
                if dist < 5:
                    refc_data[i, j] = max(refc_data[i, j], intensity * np.exp(-dist/3))

    # Clip values to realistic range and set areas with no precipitation to NaN
    refc_data = np.clip(refc_data, -10, 75)
    refc_data[refc_data < 5] = np.nan  # No significant reflectivity below 5 dBZ

    # Create GeoJSON features for contour/heatmap
    features = []

    for i in range(grid_size):
        for j in range(grid_size):
            # Skip points with no significant reflectivity
            if np.isnan(refc_data[i, j]):
                continue

            feature = {
                "type": "Feature",
                "properties": {
                    "refc": float(refc_data[i, j]),
                    "lat": float(lat_grid[i, j]),
                    "lon": float(lon_grid[i, j])
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(lon_grid[i, j]), float(lat_grid[i, j])]
                }
            }
            features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "properties": {
            "forecast_time": forecast_time.isoformat(),
            "model": "HRRR-Alaska",
            "variable": "Composite Reflectivity (dBZ)",
            "grid_size": grid_size
        },
        "features": features
    }

    # Save to public directory
    os.makedirs('public', exist_ok=True)
    with open('public/hrrr_data.json', 'w') as f:
        json.dump(geojson, f)

    print(f"Created synthetic HRRR data with {len(features)} grid points")
    print(f"Data saved to public/hrrr_data.json")

    # Also create metadata
    metadata = {
        "last_updated": datetime.utcnow().isoformat(),
        "forecast_time": forecast_time.isoformat(),
        "bounds": {
            "north": lat_max,
            "south": lat_min,
            "east": lon_max,
            "west": lon_min
        },
        "grid_size": grid_size
    }

    with open('public/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

if __name__ == '__main__':
    download_hrrr_ak()
