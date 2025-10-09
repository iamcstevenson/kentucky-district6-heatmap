#!/usr/bin/env python3
import json
import csv
import subprocess
import os
import tempfile

def extract_tiger_data():
    """Extract and process TIGER shapefile data for Kentucky District 6"""

    # Create temp files
    counties_geojson = '/tmp/claude/ky_counties.geojson'
    district_geojson = '/tmp/claude/district6.geojson'

    # Extract Kentucky counties
    cmd_counties = [
        'ogr2ogr', '-f', 'GeoJSON', counties_geojson,
        'census-data/tl_2024_us_county/tl_2024_us_county.shp',
        '-where', "STATEFP = '21'"
    ]

    # Extract District 6 boundary
    cmd_district = [
        'ogr2ogr', '-f', 'GeoJSON', district_geojson,
        'census-data/tl_2024_21_cd119/tl_2024_21_cd119.shp',
        '-where', "CD119FP = '06'"
    ]

    print("Extracting county boundaries...")
    result1 = subprocess.run(cmd_counties, capture_output=True, text=True)
    if result1.returncode != 0:
        print(f"Error extracting counties: {result1.stderr}")
        return None, None

    print("Extracting District 6 boundary...")
    result2 = subprocess.run(cmd_district, capture_output=True, text=True)
    if result2.returncode != 0:
        print(f"Error extracting district: {result2.stderr}")
        return None, None

    return counties_geojson, district_geojson

def load_soybean_data():
    """Load and clean soybean sales data - prioritize district CSV for accuracy"""
    sales_data = {}

    # First load main CSV data
    with open('kentucky-soybean-sales-2022.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            county = row['County'].strip()
            sales = int(row['Soybean Sales'])
            sales_data[county] = sales

    # Override with district-specific data for accuracy
    with open('district6-soybean-sales.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            county = row['County'].strip()
            sales_str = row['Sales'].replace('$', '').replace(',', '')
            if sales_str:
                sales_data[county] = int(sales_str)
            else:
                sales_data[county] = 0

    print(f"Loaded soybean data for {len(sales_data)} counties")
    return sales_data

def identify_district_counties(counties_geojson, district_geojson):
    """Identify which counties are in District 6"""

    # Load the district county list from existing CSV
    district_counties = set()

    with open('district6-soybean-sales.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            county = row['County'].strip()
            district_counties.add(county)

    print(f"District 6 contains {len(district_counties)} counties:")
    for county in sorted(district_counties):
        print(f"  - {county}")

    return district_counties

def convert_to_svg(counties_geojson, district_geojson, district_counties, sales_data):
    """Convert GeoJSON to SVG paths with proper coordinate transformation"""

    # Kentucky bounding box
    bounds = {
        'min_lon': -89.571203,
        'max_lon': -81.964788,
        'min_lat': 36.497058,
        'max_lat': 39.147732
    }

    def transform_coord(lon, lat):
        x = ((lon - bounds['min_lon']) / (bounds['max_lon'] - bounds['min_lon'])) * 1000
        y = ((bounds['max_lat'] - lat) / (bounds['max_lat'] - bounds['min_lat'])) * 500
        return round(x, 1), round(y, 1)

    # Process counties
    with open(counties_geojson, 'r') as f:
        counties_data = json.load(f)

    county_svg_data = {}

    for feature in counties_data['features']:
        county_name = feature['properties']['NAMELSAD'].replace(' County', '')
        fips = feature['properties']['GEOID']

        # Get coordinates - handle both Polygon and MultiPolygon
        if feature['geometry']['type'] == 'Polygon':
            coords_list = [feature['geometry']['coordinates'][0]]
        else:  # MultiPolygon
            coords_list = [ring[0] for ring in feature['geometry']['coordinates']]

        # Convert all coordinate rings to SVG paths
        svg_paths = []
        for coords in coords_list:
            path_parts = []
            for i, coord in enumerate(coords):
                x, y = transform_coord(coord[0], coord[1])
                path_parts.append(f"{'M' if i == 0 else 'L'} {x},{y}")
            path_parts.append("Z")
            svg_paths.append(" ".join(path_parts))

        county_svg_data[county_name] = {
            'name': county_name,
            'fips': fips,
            'svg_path': " ".join(svg_paths),
            'in_district': county_name in district_counties,
            'sales': sales_data.get(county_name, 0)
        }

    # Process District 6 boundary
    with open(district_geojson, 'r') as f:
        district_data = json.load(f)

    district_svg_paths = []

    for feature in district_data['features']:
        if feature['geometry']['type'] == 'Polygon':
            coords_list = [feature['geometry']['coordinates'][0]]
        else:  # MultiPolygon
            coords_list = [ring[0] for ring in feature['geometry']['coordinates']]

        for coords in coords_list:
            path_parts = []
            for i, coord in enumerate(coords):
                x, y = transform_coord(coord[0], coord[1])
                path_parts.append(f"{'M' if i == 0 else 'L'} {x},{y}")
            path_parts.append("Z")
            district_svg_paths.append(" ".join(path_parts))

    return county_svg_data, district_svg_paths

def calculate_color_scale(district_counties, sales_data):
    """Calculate color scale for heat map"""

    district_sales = []
    for county in district_counties:
        sales = sales_data.get(county, 0)
        district_sales.append(sales)

    min_sales = 0  # Start at $0
    max_sales = max(district_sales) if district_sales else 0

    print(f"Sales range: ${min_sales:,} to ${max_sales:,}")

    def get_color(sales_value):
        if sales_value == 0:
            return "#ffffff"  # White for $0

        # Calculate intensity (0 to 1)
        intensity = sales_value / max_sales if max_sales > 0 else 0

        # Darker green color scale: white -> dark forest green
        # HSL: hue=120 (green), high saturation, lower lightness for darker tones
        saturation = min(90, 60 + (intensity * 30))  # 60% -> 90%
        lightness = max(15, 80 - (intensity * 65))   # 80% -> 15%

        return f"hsl(120, {saturation}%, {lightness}%)"

    return get_color, min_sales, max_sales

def generate_html(county_svg_data, district_svg_paths, get_color, min_sales, max_sales):
    """Generate the embeddable HTML map"""

    # Create county SVG elements - ONLY district counties
    county_elements = []

    for county_name, data in county_svg_data.items():
        if data['in_district']:
            color = get_color(data['sales'])
            # Counties in district - with hover effects, royal blue borders
            county_elements.append(f'''
        <path class="county district-county"
              data-county="{county_name}"
              data-sales="{data['sales']}"
              d="{data['svg_path']}"
              fill="{color}"
              stroke="#4169E1"
              stroke-width="0.5"/>''')
        # Non-district counties are NOT rendered

    # Create district boundary elements
    district_elements = []
    for path in district_svg_paths:
        district_elements.append(f'''
        <path class="district-boundary"
              d="{path}"
              fill="none"
              stroke="#000000"
              stroke-width="2.0"/>''')

    # Generate complete HTML
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kentucky 6th Congressional District - Soybean Sales Heat Map</title>
    <style>
        .map-container {{
            max-width: 100%;
            margin: 0 auto;
            font-family: Arial, sans-serif;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .map-header {{
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }}

        .map-title {{
            font-size: 1.5em;
            font-weight: bold;
            color: #343a40;
            margin: 0 0 10px 0;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .collapse-toggle {{
            font-size: 0.8em;
            color: #6c757d;
            user-select: none;
            transition: transform 0.3s ease;
        }}

        .collapse-toggle.collapsed {{
            transform: rotate(-90deg);
        }}

        .collapsible-content {{
            transition: max-height 0.3s ease, opacity 0.3s ease;
            overflow: hidden;
        }}

        .collapsible-content.collapsed {{
            max-height: 0;
            opacity: 0;
        }}

        .map-description {{
            color: #6c757d;
            font-size: 0.9em;
            line-height: 1.4;
            margin: 0;
        }}

        .svg-container {{
            position: relative;
            width: 100%;
            height: 0;
            padding-bottom: 50%; /* 2:1 aspect ratio */
        }}

        .map-svg {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }}

        .county.district-county {{
            cursor: pointer;
            transition: stroke-width 0.2s;
        }}

        .county.district-county:hover {{
            stroke: #1e40af;
            stroke-width: 1.5;
        }}

        .district-boundary {{
            pointer-events: none;
        }}

        .popup {{
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            display: none;
        }}

        .legend {{
            padding: 15px 20px;
            background: #f8f9fa;
            border-top: 1px solid #dee2e6;
            font-size: 0.85em;
        }}

        .legend-title {{
            font-weight: bold;
            margin-bottom: 8px;
            color: #343a40;
        }}

        .legend-scale {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 5px;
        }}

        .legend-gradient {{
            width: 150px;
            height: 15px;
            background: linear-gradient(to right, #ffffff, hsl(120, 60%, 80%), hsl(120, 75%, 60%), hsl(120, 90%, 40%), hsl(120, 90%, 15%));
            border: 1px solid #ccc;
        }}

        .legend-labels {{
            display: flex;
            justify-content: space-between;
            width: 150px;
            font-size: 0.8em;
            color: #6c757d;
        }}

        @media (max-width: 768px) {{
            .map-header {{
                padding: 15px;
            }}

            .map-title {{
                font-size: 1.2em;
            }}

            .collapsible-content {{
                max-height: 0;
                opacity: 0;
            }}

            .collapsible-content.expanded {{
                max-height: 500px;
                opacity: 1;
            }}

            .collapse-toggle {{
                display: inline;
            }}

            .legend {{
                padding: 10px 15px;
            }}

            .legend-scale {{
                flex-direction: column;
                align-items: flex-start;
                gap: 5px;
            }}
        }}

        @media (min-width: 769px) {{
            .collapsible-content {{
                max-height: none !important;
                opacity: 1 !important;
            }}

            .collapse-toggle {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="map-container">
        <div class="map-header">
            <h1 class="map-title" onclick="toggleContent()">
                Kentucky 6th Congressional District - Agricultural Significance of Soybeans
                <span class="collapse-toggle" id="toggleIcon">▼</span>
            </h1>
            <div class="collapsible-content" id="collapsibleContent" style="font-size: 0.9em; color: #495057; line-height: 1.6; text-align: left;">
                <p style="margin: 0 0 12px 0;">
                    Soybeans are among Kentucky's most important crops, and they play a meaningful role in the agricultural economy of the 6th Congressional District. In 2022, farms in the district sold approximately $43.7 million worth of soybeans. Soybeans remain one of the most versatile and marketable crops for farmers in the 6th Congressional District.
                </p>
                <p style="margin: 0;">
                    In the 6th District, soybeans are especially important because they provide a consistent cash crop that balances the more variable returns from livestock, tobacco, and specialty crops. Many farms rely on soybeans as part of diversified rotations, which improves soil health and sustainability. Additionally, proximity to interstates and rail connections in Lexington, Winchester, and Richmond supports soybean movement to processing and export channels, making them a reliable revenue stream for district farmers.
                </p>
            </div>
        </div>

        <div class="svg-container">
            <svg class="map-svg" viewBox="0 0 1000 500" xmlns="http://www.w3.org/2000/svg">
                <!-- Counties -->
                {"".join(county_elements)}

                <!-- District 6 Boundary -->
                {"".join(district_elements)}
            </svg>

            <div class="popup" id="popup"></div>
        </div>

        <div class="legend">
            <div class="legend-title">Soybean Sales (2022)*</div>
            <div class="legend-scale">
                <div class="legend-gradient"></div>
            </div>
            <div class="legend-labels">
                <span>${min_sales:,}</span>
                <span>${max_sales:,}</span>
            </div>
            <div style="margin-top: 8px; color: #6c757d; font-size: 0.75em; font-style: italic;">
                *US Census of Agriculture
            </div>
        </div>
    </div>

    <script>
        // Collapsible content functionality
        function toggleContent() {{
            const content = document.getElementById('collapsibleContent');
            const icon = document.getElementById('toggleIcon');

            // Only toggle on mobile devices
            if (window.innerWidth <= 768) {{
                content.classList.toggle('expanded');
                icon.classList.toggle('collapsed');

                // Update icon
                if (content.classList.contains('expanded')) {{
                    icon.textContent = '▲';
                }} else {{
                    icon.textContent = '▼';
                }}
            }}
        }}

        // Ensure proper state on window resize
        window.addEventListener('resize', function() {{
            const content = document.getElementById('collapsibleContent');
            const icon = document.getElementById('toggleIcon');

            if (window.innerWidth > 768) {{
                // Desktop: always show content, hide toggle
                content.classList.remove('expanded', 'collapsed');
                icon.classList.remove('collapsed');
                icon.textContent = '▼';
            }} else {{
                // Mobile: start collapsed
                if (!content.classList.contains('expanded')) {{
                    icon.textContent = '▼';
                }}
            }}
        }});

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {{
            if (window.innerWidth <= 768) {{
                // Start collapsed on mobile
                const content = document.getElementById('collapsibleContent');
                content.classList.remove('expanded');
            }}
        }});

        // Popup functionality for district counties only
        const popup = document.getElementById('popup');
        const districtCounties = document.querySelectorAll('.county.district-county');

        districtCounties.forEach(county => {{
            county.addEventListener('mouseenter', function(e) {{
                const countyName = this.getAttribute('data-county');
                const sales = parseInt(this.getAttribute('data-sales'));
                const fips = this.getAttribute('data-fips');

                popup.innerHTML = `
                    <strong>${{countyName}} County</strong><br>
                    Soybean Sales: $` + sales.toLocaleString() + `
                `;
                popup.style.display = 'block';
            }});

            county.addEventListener('mousemove', function(e) {{
                const rect = e.target.closest('.svg-container').getBoundingClientRect();
                popup.style.left = (e.clientX - rect.left + 10) + 'px';
                popup.style.top = (e.clientY - rect.top - 10) + 'px';
            }});

            county.addEventListener('mouseleave', function() {{
                popup.style.display = 'none';
            }});
        }});
    </script>
</body>
</html>'''

    return html_content

def load_existing_county_data(sales_data, district_counties):
    """Load pre-processed county SVG data from ky_counties.json"""
    print("Using existing ky_counties.json data...")

    with open('ky_counties.json', 'r') as f:
        existing_data = json.load(f)

    county_svg_data = {}
    for county_name, data in existing_data.items():
        county_svg_data[county_name] = {
            'name': county_name,
            'fips': data['fips'],
            'svg_path': data['svg_path'],
            'in_district': county_name in district_counties,
            'sales': sales_data.get(county_name, 0)
        }

    # Empty district boundary paths since we're not extracting from TIGER
    district_svg_paths = []

    return county_svg_data, district_svg_paths

def main():
    # Create temp directory
    os.makedirs('/tmp/claude', exist_ok=True)

    print("=== Kentucky 6th Congressional District Heat Map Generator ===")

    # Phase 1: Check for TIGER data or use existing processed data
    print("\nPhase 1: Checking for data sources...")

    # Check if TIGER shapefiles exist
    tiger_counties = 'census-data/tl_2024_us_county/tl_2024_us_county.shp'
    tiger_district = 'census-data/tl_2024_21_cd119/tl_2024_21_cd119.shp'

    use_existing = False
    if not (os.path.exists(tiger_counties) and os.path.exists(tiger_district)):
        if os.path.exists('ky_counties.json'):
            print("TIGER shapefiles not found. Using existing ky_counties.json...")
            use_existing = True
        else:
            print("Error: Neither TIGER shapefiles nor ky_counties.json found!")
            print("Please download TIGER shapefiles or ensure ky_counties.json exists.")
            return

    # Phase 2: Load soybean data
    print("\nPhase 2: Loading soybean sales data...")
    sales_data = load_soybean_data()

    # Phase 3: Identify district counties
    print("\nPhase 3: Identifying District 6 counties...")

    if use_existing:
        # Load district counties from CSV
        district_counties = set()
        with open('district6-soybean-sales.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                county = row['County'].strip()
                district_counties.add(county)

        print(f"District 6 contains {len(district_counties)} counties")

        # Phase 4: Load existing SVG data
        print("\nPhase 4: Loading existing SVG data...")
        county_svg_data, district_svg_paths = load_existing_county_data(sales_data, district_counties)
    else:
        # Extract from TIGER shapefiles
        print("Extracting TIGER shapefile data...")
        counties_geojson, district_geojson = extract_tiger_data()
        if not counties_geojson or not district_geojson:
            return

        district_counties = identify_district_counties(counties_geojson, district_geojson)

        # Phase 4: Convert to SVG
        print("\nPhase 4: Converting to SVG format...")
        county_svg_data, district_svg_paths = convert_to_svg(
            counties_geojson, district_geojson, district_counties, sales_data
        )

    # Phase 5: Calculate color scale
    print("\nPhase 5: Calculating heat map colors...")
    get_color, min_sales, max_sales = calculate_color_scale(district_counties, sales_data)

    # Phase 6: Generate HTML
    print("\nPhase 6: Generating embeddable HTML...")
    html_content = generate_html(county_svg_data, district_svg_paths, get_color, min_sales, max_sales)

    # Save output
    output_file = 'kentucky-district6-embeddable.html'
    with open(output_file, 'w') as f:
        f.write(html_content)

    print(f"\n✅ Success! Generated: {output_file}")
    print(f"📊 District counties: {len(district_counties)}")
    print(f"💰 Sales range: ${min_sales:,} to ${max_sales:,}")
    print(f"📄 File size: {len(html_content):,} bytes")
    print("\nThe map is ready for embedding in your web page!")

if __name__ == "__main__":
    main()