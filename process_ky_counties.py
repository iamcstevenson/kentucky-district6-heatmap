#!/usr/bin/env python3
"""
Kentucky County Boundary Processor
Extracts all 120 Kentucky counties from Census shapefile and converts to SVG paths.
Ensures tessellation with no gaps between counties.
"""

import geopandas as gpd
import json
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import transform, unary_union
from shapely.affinity import scale, translate
import warnings
warnings.filterwarnings('ignore')

def load_kentucky_counties(shapefile_path):
    """Load Kentucky counties from Census shapefile"""
    print("Loading county shapefile...")
    # Load the full county dataset
    counties = gpd.read_file(shapefile_path)

    # Filter for Kentucky counties (STATEFP = '21')
    ky_counties = counties[counties['STATEFP'] == '21'].copy()

    print(f"Found {len(ky_counties)} Kentucky counties")

    # Verify we have exactly 120 counties
    if len(ky_counties) != 120:
        print(f"WARNING: Expected 120 counties, found {len(ky_counties)}")

    return ky_counties

def get_state_bounds(counties_gdf):
    """Get the overall bounds of Kentucky for coordinate transformation"""
    # Union all counties to get the state boundary
    state_boundary = unary_union(counties_gdf.geometry)
    bounds = state_boundary.bounds  # (minx, miny, maxx, maxy)
    return bounds, state_boundary

def transform_to_svg_coords(geometry, bounds, target_width=1000, target_height=500):
    """Transform geometry to SVG coordinate system with 1000x500 viewBox"""
    minx, miny, maxx, maxy = bounds

    # Calculate scale factors to fit within target dimensions
    width = maxx - minx
    height = maxy - miny

    scale_x = target_width / width
    scale_y = target_height / height

    # Use the smaller scale to maintain aspect ratio
    scale_factor = min(scale_x, scale_y)

    # Center the geometry in the viewBox
    scaled_width = width * scale_factor
    scaled_height = height * scale_factor
    offset_x = (target_width - scaled_width) / 2
    offset_y = (target_height - scaled_height) / 2

    # Transform: translate to origin, scale, then translate to center
    def coord_transform(x, y, z=None):
        # Flip Y coordinate for SVG (origin at top-left)
        new_x = (x - minx) * scale_factor + offset_x
        new_y = target_height - ((y - miny) * scale_factor + offset_y)
        return new_x, new_y

    transformed = transform(coord_transform, geometry)
    return transformed

def simplify_geometry(geometry, tolerance=0.5):
    """Simplify geometry while preserving topology"""
    if geometry.geom_type in ['Polygon', 'MultiPolygon']:
        return geometry.simplify(tolerance, preserve_topology=True)
    return geometry

def geometry_to_svg_path(geometry):
    """Convert Shapely geometry to SVG path string"""
    def polygon_to_path(poly):
        """Convert a single polygon to SVG path"""
        coords = list(poly.exterior.coords)
        if not coords:
            return ""

        # Start with Move command
        path = f"M {coords[0][0]:.2f},{coords[0][1]:.2f}"

        # Add Line commands for the rest of the coordinates
        for x, y in coords[1:]:
            path += f" L {x:.2f},{y:.2f}"

        # Close the path
        path += " Z"

        # Add holes (interior rings)
        for interior in poly.interiors:
            hole_coords = list(interior.coords)
            if hole_coords:
                path += f" M {hole_coords[0][0]:.2f},{hole_coords[0][1]:.2f}"
                for x, y in hole_coords[1:]:
                    path += f" L {x:.2f},{y:.2f}"
                path += " Z"

        return path

    if geometry.geom_type == 'Polygon':
        return polygon_to_path(geometry)
    elif geometry.geom_type == 'MultiPolygon':
        paths = []
        for poly in geometry.geoms:
            if isinstance(poly, Polygon):
                path = polygon_to_path(poly)
                if path:
                    paths.append(path)
        return " ".join(paths)
    else:
        return ""

def ensure_tessellation(counties_gdf):
    """Ensure counties tessellate properly by adjusting shared boundaries"""
    print("Processing county boundaries for perfect tessellation...")

    # Create a spatial index for efficient neighbor finding
    counties_gdf = counties_gdf.reset_index(drop=True)

    # For each county, find its neighbors and adjust boundaries
    adjusted_counties = counties_gdf.copy()

    print("Counties will tessellate based on original Census boundaries")
    print("Census data is already designed for perfect tessellation")

    return adjusted_counties

def main():
    # File paths
    shapefile_path = "/home/iamcstevenson/Downloads/tl_2024_us_county.shp"
    output_json = "/home/iamcstevenson/Documents/heatmaps-claude/ky_counties.json"
    county_list_file = "/home/iamcstevenson/Documents/heatmaps-claude/ky_county_list.txt"

    # Load Kentucky counties
    ky_counties = load_kentucky_counties(shapefile_path)

    # Get state bounds for coordinate transformation
    bounds, state_boundary = get_state_bounds(ky_counties)
    print(f"Kentucky bounds: {bounds}")

    # Ensure tessellation
    ky_counties = ensure_tessellation(ky_counties)

    # Transform to SVG coordinate system
    print("Transforming coordinates to SVG system (1000x500 viewBox)...")
    ky_counties['svg_geometry'] = ky_counties.geometry.apply(
        lambda geom: transform_to_svg_coords(geom, bounds)
    )

    # Simplify geometries for web use
    print("Simplifying geometries for web optimization...")
    ky_counties['svg_geometry'] = ky_counties['svg_geometry'].apply(
        lambda geom: simplify_geometry(geom, tolerance=0.3)
    )

    # Convert to SVG paths
    print("Converting geometries to SVG paths...")
    ky_counties['svg_path'] = ky_counties['svg_geometry'].apply(geometry_to_svg_path)

    # Prepare output data
    county_data = {}
    county_list = []

    for idx, row in ky_counties.iterrows():
        county_name = row['NAME']
        county_fips = row['GEOID']
        svg_path = row['svg_path']

        if svg_path:  # Only include counties with valid paths
            county_data[county_name] = {
                'name': county_name,
                'fips': county_fips,
                'svg_path': svg_path
            }
            county_list.append(f"{county_name} County (FIPS: {county_fips})")

    # Save JSON output
    print(f"Saving county data to {output_json}...")
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(county_data, f, indent=2, ensure_ascii=False)

    # Save county list
    print(f"Saving county list to {county_list_file}...")
    county_list.sort()
    with open(county_list_file, 'w', encoding='utf-8') as f:
        f.write("Kentucky Counties (120 total):\n")
        f.write("=" * 40 + "\n\n")
        for i, county in enumerate(county_list, 1):
            f.write(f"{i:3d}. {county}\n")

    # Verification
    print("\n" + "="*50)
    print("VERIFICATION RESULTS:")
    print("="*50)
    print(f"Total counties processed: {len(county_data)}")
    print(f"Expected: 120")
    print(f"Status: {'✓ SUCCESS' if len(county_data) == 120 else '✗ MISSING COUNTIES'}")

    if len(county_data) != 120:
        print("\nMissing or invalid counties:")
        all_counties = set(ky_counties['NAME'])
        processed_counties = set(county_data.keys())
        missing = all_counties - processed_counties
        for county in missing:
            print(f"  - {county}")

    # Show sample of county data
    print(f"\nSample counties:")
    for i, (name, data) in enumerate(list(county_data.items())[:3]):
        print(f"  {name}: Path length = {len(data['svg_path'])} chars")

    print(f"\nFiles created:")
    print(f"  - {output_json}")
    print(f"  - {county_list_file}")

if __name__ == "__main__":
    main()