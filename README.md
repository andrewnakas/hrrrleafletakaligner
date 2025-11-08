# Alaska HRRR Data Viewer

A real-time visualization of Alaska HRRR (High-Resolution Rapid Refresh) weather data on a Leaflet map, with perfect coordinate alignment.

## Features

- Automatic download of latest Alaska HRRR data
- GitHub Actions workflow that triggers on every branch push
- Interactive Leaflet map with temperature data visualization
- Proper coordinate alignment between HRRR grid and Leaflet's WGS84 projection
- Automatic deployment to GitHub Pages for fast testing

## How It Works

1. **Data Download**: GitHub Actions workflow runs on every push to any branch
2. **Processing**: Python script downloads and processes HRRR data, converting it to GeoJSON
3. **Visualization**: Leaflet map displays the data with color-coded temperature points
4. **Deployment**: Automatically deploys to GitHub Pages for immediate viewing

## Setup

### Enable GitHub Pages (Required)

1. Go to your repository **Settings** on GitHub
2. Navigate to **Pages** (in the left sidebar)
3. Under "Build and deployment":
   - **Source**: Select **GitHub Actions**
4. Save the settings

That's it! Now every push to any branch will automatically deploy to GitHub Pages.

## Fast Testing Workflow

The workflow runs on **every branch push** and automatically deploys to GitHub Pages:

### Method 1: GitHub Pages (Automatic on Every Push)

1. Push to any branch: `git push`
2. Wait ~1-2 minutes for deployment
3. Visit: `https://[your-username].github.io/hrrrleafletakaligner/`
4. See your changes live instantly!

### Method 2: Download Artifacts

1. Go to Actions tab on GitHub
2. Click on your workflow run
3. Download the "hrrr-viewer-[number]-[hash]" artifact
4. Extract and open `index.html` locally

### Method 3: Local Testing

```bash
# Quick start
chmod +x test-local.sh
./test-local.sh

# Or manually:
pip install -r requirements.txt
python scripts/download_hrrr.py
cd public && python -m http.server 8000
```

Then open http://localhost:8000 in your browser.

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions workflow
├── scripts/
│   └── download_hrrr.py        # HRRR data download and processing
├── public/
│   ├── index.html              # Leaflet map visualization
│   ├── hrrr_data.json         # Generated HRRR data (GeoJSON)
│   └── metadata.json          # Data metadata
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Data Alignment

The project ensures perfect alignment between HRRR data and Leaflet maps by:

1. Converting HRRR's Lambert Conformal Conic projection to WGS84 lat/lon
2. Using GeoJSON format with proper coordinate ordering [lon, lat]
3. Validating coordinates fall within Alaska bounds (51°N-71.5°N, 179°W-130°W)

## Customization

- Modify `scripts/download_hrrr.py` to download different variables or forecast hours
- Update `public/index.html` to change map styling, colors, or interactivity
- Adjust `.github/workflows/deploy.yml` to change deployment triggers or add processing steps

## License

MIT
