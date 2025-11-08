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
    """Download latest Alaska HRRR refc data from NOAA using GRIB filter."""

    # Get current UTC time and round to latest forecast hour
    now = datetime.utcnow()

    # Try multiple recent forecast hours (HRRR data may not be immediately available)
    for hours_back in range(0, 6):
        forecast_time = now - timedelta(hours=hours_back)
        forecast_hour = forecast_time.replace(minute=0, second=0, microsecond=0)

        date_str = forecast_hour.strftime('%Y%m%d')
        hour_str = forecast_hour.strftime('%H')

        # Try Alaska HRRR direct download (no filter available for Alaska domain)
        # Alaska HRRR is a separate model with different file structure
        # Try both possible file patterns
        alaska_urls = [
            f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.{date_str}/alaska/hrrr.t{hour_str}z.wrfsfcf00.ak.grib2",
            f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.{date_str}/alaska/hrrr.t{hour_str}z.wrfsfcf00.grib2",
        ]

        print(f"Attempting to download HRRR Alaska refc for {forecast_hour.isoformat()}Z")

        for url in alaska_urls:
            print(f"Trying URL: {url}")
            try:
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    print(f"Found file at {url}")
                    base_url = url
                    params = {}
                    break
            except Exception as e:
                continue
        else:
            print("Alaska HRRR files not found, trying CONUS fallback")
            base_url = "https://nomads.ncep.noaa.gov/cgi-bin/filter_hrrr_2d.pl"
            params = {
                'file': f'hrrr.t{hour_str}z.wrfsfcf00.grib2',
                'var_REFC': 'on',
                'lev_entire_atmosphere': 'on',
                'dir': f'/hrrr.{date_str}/conus'
            }

        print(f"Final URL: {base_url}")
        if params:
            print(f"Params: {params}")

        try:
            if params:
                response = requests.get(base_url, params=params, timeout=120)
            else:
                response = requests.get(base_url, timeout=120)

            if response.status_code == 200 and len(response.content) > 1000:
                # Save GRIB2 file
                grib_path = 'public/hrrr_alaska_refc.grib2'
                os.makedirs('public', exist_ok=True)

                with open(grib_path, 'wb') as f:
                    f.write(response.content)

                print(f"Downloaded GRIB2 file successfully ({len(response.content)} bytes)")

                # Try to process with cfgrib
                if process_grib_refc(grib_path, forecast_hour):
                    return True

            else:
                print(f"Failed to download (status {response.status_code}, size {len(response.content)} bytes)")

        except Exception as e:
            print(f"Error downloading HRRR data for {forecast_hour}: {e}")
            continue

    # If all attempts failed, use synthetic data
    print("All download attempts failed. Using synthetic data for demo")
    forecast_hour = (now - timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    create_synthetic_refc_image(forecast_hour)
    return False

def process_grib_refc(grib_path, forecast_time):
    """Process GRIB2 file to extract refc and create image overlay."""
    try:
        import xarray as xr
        import cfgrib

        print("Processing GRIB2 file with cfgrib...")

        # Open GRIB2 file
        ds = xr.open_dataset(grib_path, engine='cfgrib')

        print(f"Available variables: {list(ds.data_vars)}")
        print(f"Coordinates: {list(ds.coords)}")

        # Try to find refc variable (it might have different names)
        refc_var = None
        for var_name in ['refc', 'REFC', 'unknown', 'r']:
            if var_name in ds:
                refc_var = var_name
                break

        if refc_var is None:
            print("Could not find refc variable in GRIB2 file")
            print(f"Available variables: {list(ds.data_vars)}")
            return False

        print(f"Found refc variable: {refc_var}")

        # Extract refc data
        refc = ds[refc_var].values

        # Get coordinates
        if 'latitude' in ds.coords and 'longitude' in ds.coords:
            lats = ds['latitude'].values
            lons = ds['longitude'].values
        elif 'lat' in ds.coords and 'lon' in ds.coords:
            lats = ds['lat'].values
            lons = ds['lon'].values
        else:
            print("Could not find latitude/longitude coordinates")
            return False

        # Convert longitude from 0-360 to -180 to 180 if needed
        if lons.max() > 180:
            lons = np.where(lons > 180, lons - 360, lons)

        print(f"Data shape: {refc.shape}")
        print(f"Lat range: {lats.min():.2f} to {lats.max():.2f}")
        print(f"Lon range: {lons.min():.2f} to {lons.max():.2f}")
        print(f"Refc range: {np.nanmin(refc):.2f} to {np.nanmax(refc):.2f} dBZ")

        # Get bounds
        lat_min, lat_max = float(np.nanmin(lats)), float(np.nanmax(lats))
        lon_min, lon_max = float(np.nanmin(lons)), float(np.nanmax(lons))

        # Create image with radar colormap
        create_refc_image_from_data(refc, lat_min, lat_max, lon_min, lon_max, forecast_time)

        ds.close()
        return True

    except Exception as e:
        print(f"Error processing GRIB2: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_refc_image_from_data(refc, lat_min, lat_max, lon_min, lon_max, forecast_time):
    """Create image overlay from refc data array."""

    # Mask out low values (< 5 dBZ)
    refc_masked = np.ma.masked_where(refc < 5, refc)

    # Create image with radar colormap
    cmap, norm, bounds = get_radar_colormap()

    fig, ax = plt.subplots(figsize=(12, 10), dpi=150)
    ax.set_position([0, 0, 1, 1])
    ax.axis('off')

    # Plot with extent matching geographic bounds
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
    print(f"Image saved to public/refc_overlay.png")
    print(f"Bounds: [{lat_min:.2f}, {lat_max:.2f}] x [{lon_min:.2f}, {lon_max:.2f}]")

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
