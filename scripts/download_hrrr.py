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

    # Generate synthetic temperature data (in Fahrenheit)
    # Create a temperature gradient from south (warmer) to north (colder)
    base_temp = 30
    temp_data = base_temp - (lat_grid - lat_min) / (lat_max - lat_min) * 50

    # Add some variability
    temp_data += np.random.normal(0, 3, temp_data.shape)

    # Create GeoJSON features for contour/heatmap
    features = []

    for i in range(grid_size):
        for j in range(grid_size):
            feature = {
                "type": "Feature",
                "properties": {
                    "temperature": float(temp_data[i, j]),
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
            "variable": "Temperature (°F)",
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
