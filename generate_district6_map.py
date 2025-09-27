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
    intersected_geojson = '/tmp/claude/counties_intersected.geojson'

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
        return None, None, None

    print("Extracting District 6 boundary...")
    result2 = subprocess.run(cmd_district, capture_output=True, text=True)
    if result2.returncode != 0:
        print(f"Error extracting district: {result2.stderr}")
        return None, None, None

    # Create intersection of counties with district boundary
    print("Computing spatial intersection...")
    cmd_intersect = [
        'ogr2ogr', '-f', 'GeoJSON', intersected_geojson,
        counties_geojson, '-clipsrc', district_geojson
    ]

    result3 = subprocess.run(cmd_intersect, capture_output=True, text=True)
    if result3.returncode != 0:
        print(f"Error computing intersection: {result3.stderr}")
        return None, None, None

    return counties_geojson, district_geojson, intersected_geojson

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

def convert_to_svg(counties_geojson, district_geojson, intersected_geojson, district_counties, sales_data):
    """Convert GeoJSON to SVG paths with proper coordinate transformation and spatial intersection"""

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

    def coords_to_svg_path(coords_list):
        """Convert coordinate list to SVG path string"""
        svg_paths = []
        for coords in coords_list:
            path_parts = []
            for i, coord in enumerate(coords):
                x, y = transform_coord(coord[0], coord[1])
                path_parts.append(f"{'M' if i == 0 else 'L'} {x},{y}")
            path_parts.append("Z")
            svg_paths.append(" ".join(path_parts))
        return " ".join(svg_paths)

    # Process all counties (for non-district counties)
    with open(counties_geojson, 'r') as f:
        counties_data = json.load(f)

    # Process intersected counties (for district portions)
    with open(intersected_geojson, 'r') as f:
        intersected_data = json.load(f)

    county_svg_data = {}
    intersected_counties = set()

    # First, process intersected geometries (portions within district)
    for feature in intersected_data['features']:
        county_name = feature['properties']['NAMELSAD'].replace(' County', '')
        fips = feature['properties']['GEOID']
        intersected_counties.add(county_name)

        # Get coordinates - handle both Polygon and MultiPolygon
        if feature['geometry']['type'] == 'Polygon':
            coords_list = [feature['geometry']['coordinates'][0]]
        elif feature['geometry']['type'] == 'MultiPolygon':
            coords_list = [ring[0] for ring in feature['geometry']['coordinates']]
        else:
            continue

        svg_path = coords_to_svg_path(coords_list)

        county_svg_data[county_name] = {
            'name': county_name,
            'fips': fips,
            'svg_path': svg_path,
            'in_district': True,  # This is the intersected portion
            'sales': sales_data.get(county_name, 0),
            'is_partial': True
        }

    # Then, process full counties
    for feature in counties_data['features']:
        county_name = feature['properties']['NAMELSAD'].replace(' County', '')
        fips = feature['properties']['GEOID']

        # Skip if we already processed the intersected portion
        if county_name in intersected_counties:
            continue

        # Get coordinates - handle both Polygon and MultiPolygon
        if feature['geometry']['type'] == 'Polygon':
            coords_list = [feature['geometry']['coordinates'][0]]
        elif feature['geometry']['type'] == 'MultiPolygon':
            coords_list = [ring[0] for ring in feature['geometry']['coordinates']]
        else:
            continue

        svg_path = coords_to_svg_path(coords_list)

        county_svg_data[county_name] = {
            'name': county_name,
            'fips': fips,
            'svg_path': svg_path,
            'in_district': county_name in district_counties,
            'sales': sales_data.get(county_name, 0),
            'is_partial': False
        }

    # Add non-intersected portions of partial counties as separate entries
    for feature in counties_data['features']:
        county_name = feature['properties']['NAMELSAD'].replace(' County', '')

        # Only for counties that have intersected portions and are in district
        if county_name in intersected_counties and county_name in district_counties:
            fips = feature['properties']['GEOID']

            # Get full county coordinates
            if feature['geometry']['type'] == 'Polygon':
                coords_list = [feature['geometry']['coordinates'][0]]
            elif feature['geometry']['type'] == 'MultiPolygon':
                coords_list = [ring[0] for ring in feature['geometry']['coordinates']]
            else:
                continue

            svg_path = coords_to_svg_path(coords_list)

            # Add as a separate entry for the non-district portion
            county_svg_data[f"{county_name}_outside"] = {
                'name': county_name,
                'fips': fips,
                'svg_path': svg_path,
                'in_district': False,  # This represents the outside portion
                'sales': 0,  # No sales data for outside portion
                'is_partial': True,
                'is_outside_portion': True
            }

    # Process District 6 boundary
    with open(district_geojson, 'r') as f:
        district_data = json.load(f)

    district_svg_paths = []

    for feature in district_data['features']:
        if feature['geometry']['type'] == 'Polygon':
            coords_list = [feature['geometry']['coordinates'][0]]
        elif feature['geometry']['type'] == 'MultiPolygon':
            coords_list = [ring[0] for ring in feature['geometry']['coordinates']]
        else:
            continue

        svg_path = coords_to_svg_path(coords_list)
        district_svg_paths.append(svg_path)

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

    # Create county SVG elements
    county_elements = []

    for county_name, data in county_svg_data.items():
        if data['in_district']:
            color = get_color(data['sales'])
            # Counties/portions in district - with hover effects, royal blue borders
            county_elements.append(f'''
        <path class="county district-county"
              data-county="{data['name']}"
              data-sales="{data['sales']}"
              d="{data['svg_path']}"
              fill="{color}"
              stroke="#4169E1"
              stroke-width="0.5"/>''')
        else:
            # Counties/portions outside district - no hover, gray fill
            fill_color = "#f5f5f5" if not data.get('is_outside_portion', False) else "#e5e5e5"
            county_elements.append(f'''
        <path class="county non-district-county"
              d="{data['svg_path']}"
              fill="{fill_color}"
              stroke="#ccc"
              stroke-width="0.3"/>''')

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

        .county.non-district-county {{
            pointer-events: none;
        }}

        /* Slightly different styling for outside portions of partial counties */
        .county.non-district-county[fill="#e5e5e5"] {{
            opacity: 0.8;
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
            background: linear-gradient(to right, #ffffff, hsl(120, 100%, 40%));
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

            .legend {{
                padding: 10px 15px;
            }}

            .legend-scale {{
                flex-direction: column;
                align-items: flex-start;
                gap: 5px;
            }}
        }}
    </style>
</head>
<body>
    <div class="map-container">
        <div class="map-header">
            <h1 class="map-title">Kentucky 6th Congressional District - Agricultural Significance of Soybeans</h1>
            <div style="font-size: 0.9em; color: #495057; line-height: 1.6; text-align: left;">
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
            <div class="legend-title">Soybean Sales (2022)</div>
            <div class="legend-scale">
                <span>Scale:</span>
                <div class="legend-gradient"></div>
            </div>
            <div class="legend-labels">
                <span>${min_sales:,}</span>
                <span>${max_sales:,}</span>
            </div>
            <div style="margin-top: 8px; color: #6c757d; font-size: 0.8em;">
                Black solid line indicates 6th Congressional District boundary
            </div>
        </div>
    </div>

    <script>
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
                    Soybean Sales: $$${{sales.toLocaleString()}}
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

def main():
    # Create temp directory
    os.makedirs('/tmp/claude', exist_ok=True)

    print("=== Kentucky 6th Congressional District Heat Map Generator ===")

    # Phase 1: Extract TIGER data
    print("\nPhase 1: Extracting TIGER shapefile data...")
    counties_geojson, district_geojson, intersected_geojson = extract_tiger_data()
    if not counties_geojson or not district_geojson or not intersected_geojson:
        return

    # Phase 2: Load soybean data
    print("\nPhase 2: Loading soybean sales data...")
    sales_data = load_soybean_data()

    # Phase 3: Identify district counties
    print("\nPhase 3: Identifying District 6 counties...")
    district_counties = identify_district_counties(counties_geojson, district_geojson)

    # Phase 4: Convert to SVG
    print("\nPhase 4: Converting to SVG format...")
    county_svg_data, district_svg_paths = convert_to_svg(
        counties_geojson, district_geojson, intersected_geojson, district_counties, sales_data
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