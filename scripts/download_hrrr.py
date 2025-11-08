#!/usr/bin/env python3
"""
Download Alaska HRRR refc data and convert it to a PNG image overlay for Leaflet.
Creates properly aligned image overlays with geographic bounds.
"""

import os
import json
import requests
from datetime import datetime, timedelta
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib import colors

def get_radar_colormap():
    """Create a radar-style colormap for reflectivity data."""
    # Define colors for different reflectivity levels (in dBZ)
    # Based on standard NEXRAD color scheme
    bounds = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75]

    radar_colors = [
        '#99FF99',  # 5-10: Light Green - Trace
        '#00CC00',  # 10-15: Dark Green - Very Light
        '#00FF00',  # 15-20: Green - Light
        '#FFFF00',  # 20-25: Yellow - Light-Moderate
        '#FFFF00',  # 25-30: Yellow - Moderate
        '#FFCC00',  # 30-35: Gold - Moderate-Heavy
        '#FFCC00',  # 35-40: Gold - Moderate-Heavy
        '#FF6600',  # 40-45: Orange - Heavy
        '#FF6600',  # 45-50: Orange - Heavy
        '#FF0000',  # 50-55: Red - Very Heavy
        '#FF0000',  # 55-60: Red - Very Heavy
        '#CC0000',  # 60-65: Dark Red - Severe
        '#FF00FF',  # 65-70: Magenta - Extreme
        '#FF00FF',  # 70-75: Magenta - Extreme
        '#9900FF',  # 75+: Purple - Extreme
    ]

    cmap = colors.ListedColormap(radar_colors)
    norm = colors.BoundaryNorm(bounds, cmap.N)
    return cmap, norm, bounds

def download_hrrr_refc():
    """Download latest Alaska HRRR refc data from NOAA."""

    # Get current UTC time and round to latest forecast hour
    now = datetime.utcnow()
    forecast_time = now - timedelta(hours=1)  # Get previous hour to ensure data availability
    forecast_hour = forecast_time.replace(minute=0, second=0, microsecond=0)

    date_str = forecast_hour.strftime('%Y%m%d')
    hour_str = forecast_hour.strftime('%H')

    # HRRR Alaska refc URL
    # Format: hrrr.YYYYMMDD/alaska/hrrr.tHHz.wrfsfcf00.grib2
    url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.{date_str}/alaska/hrrr.t{hour_str}z.wrfsfcf00.grib2"

    print(f"Attempting to download HRRR Alaska data from {url}")

    try:
        # Try to download the actual GRIB2 file
        response = requests.get(url, timeout=30, stream=True)

        if response.status_code == 200:
            # Save GRIB2 file
            grib_path = 'public/hrrr_alaska.grib2'
            os.makedirs('public', exist_ok=True)

            with open(grib_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"Downloaded GRIB2 file successfully")

            # Try to process with cfgrib
            try:
                import xarray as xr
                import cfgrib

                # Open GRIB2 file and extract refc
                ds = xr.open_dataset(grib_path, engine='cfgrib',
                                     backend_kwargs={'filter_by_keys': {'typeOfLevel': 'atmosphereSingleLayer'}})

                if 'refc' in ds:
                    create_refc_image(ds, forecast_hour)
                    return
                else:
                    print("refc field not found in GRIB2 file, trying alternative...")

            except Exception as e:
                print(f"Error processing GRIB2: {e}")
                print("Falling back to synthetic data")
        else:
            print(f"Failed to download GRIB2 (status {response.status_code})")

    except Exception as e:
        print(f"Error downloading HRRR data: {e}")

    # Fallback to synthetic data
    print("Using synthetic data for demo")
    create_synthetic_refc_image(forecast_hour)

def create_refc_image(ds, forecast_time):
    """Create image overlay from actual HRRR refc data."""
    refc = ds['refc'].values
    lats = ds['latitude'].values
    lons = ds['longitude'].values

    # Get bounds
    lat_min, lat_max = np.nanmin(lats), np.nanmax(lats)
    lon_min, lon_max = np.nanmin(lons), np.nanmax(lons)

    # Create image with radar colormap
    cmap, norm, bounds = get_radar_colormap()

    # Mask out low values (< 5 dBZ)
    refc_masked = np.ma.masked_where(refc < 5, refc)

    # Create image
    fig, ax = plt.subplots(figsize=(10, 10), dpi=150)
    ax.set_position([0, 0, 1, 1])
    ax.axis('off')

    im = ax.imshow(refc_masked, cmap=cmap, norm=norm,
                   origin='lower', interpolation='nearest',
                   extent=[lon_min, lon_max, lat_min, lat_max])

    # Save as PNG with transparency
    os.makedirs('public', exist_ok=True)
    plt.savefig('public/refc_overlay.png', transparent=True,
                bbox_inches='tight', pad_inches=0, dpi=150)
    plt.close()

    # Save metadata
    save_metadata(forecast_time, lat_min, lat_max, lon_min, lon_max)

    print(f"Created refc image overlay from actual HRRR data")

def create_synthetic_refc_image(forecast_time):
    """Create synthetic refc data as image overlay for demo."""

    # Alaska bounds (approximate)
    lat_min, lat_max = 51.0, 71.5
    lon_min, lon_max = -179.0, -130.0

    # Create high-resolution grid for image
    grid_size = 500
    lats = np.linspace(lat_min, lat_max, grid_size)
    lons = np.linspace(lon_min, lon_max, grid_size)

    lon_grid, lat_grid = np.meshgrid(lons, lats)

    # Generate synthetic composite reflectivity data (in dBZ)
    # Create base pattern with some precipitation areas
    refc_data = np.random.normal(10, 8, (grid_size, grid_size))

    # Add localized storm cells (higher reflectivity areas)
    num_cells = 8
    for _ in range(num_cells):
        center_i = np.random.randint(50, grid_size - 50)
        center_j = np.random.randint(50, grid_size - 50)
        intensity = np.random.uniform(35, 70)  # Storm cell intensity
        radius = np.random.uniform(15, 40)

        for i in range(grid_size):
            for j in range(grid_size):
                dist = np.sqrt((i - center_i)**2 + (j - center_j)**2)
                if dist < radius:
                    refc_data[i, j] = max(refc_data[i, j],
                                         intensity * np.exp(-dist/(radius/3)))

    # Clip values to realistic range
    refc_data = np.clip(refc_data, -10, 75)

    # Mask out areas with no significant reflectivity
    refc_masked = np.ma.masked_where(refc_data < 5, refc_data)

    # Create image with radar colormap
    cmap, norm, bounds = get_radar_colormap()

    fig, ax = plt.subplots(figsize=(12, 10), dpi=150)
    ax.set_position([0, 0, 1, 1])
    ax.axis('off')

    # Plot with extent matching geographic bounds
    im = ax.imshow(refc_masked, cmap=cmap, norm=norm,
                   origin='lower', interpolation='bilinear',
                   extent=[lon_min, lon_max, lat_min, lat_max])

    # Save as PNG with transparency
    os.makedirs('public', exist_ok=True)
    plt.savefig('public/refc_overlay.png', transparent=True,
                bbox_inches='tight', pad_inches=0, dpi=150)
    plt.close()

    # Save metadata
    save_metadata(forecast_time, lat_min, lat_max, lon_min, lon_max)

    print(f"Created synthetic refc image overlay")
    print(f"Image saved to public/refc_overlay.png")
    print(f"Bounds: [{lat_min}, {lat_max}] x [{lon_min}, {lon_max}]")

def save_metadata(forecast_time, lat_min, lat_max, lon_min, lon_max):
    """Save metadata about the overlay."""
    metadata = {
        "last_updated": datetime.utcnow().isoformat(),
        "forecast_time": forecast_time.isoformat(),
        "bounds": {
            "north": float(lat_max),
            "south": float(lat_min),
            "east": float(lon_max),
            "west": float(lon_min)
        },
        "overlay_file": "refc_overlay.png",
        "variable": "Composite Reflectivity (dBZ)",
        "model": "HRRR-Alaska"
    }

    with open('public/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"Metadata saved to public/metadata.json")

if __name__ == '__main__':
    download_hrrr_refc()
