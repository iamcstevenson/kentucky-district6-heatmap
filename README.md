# Kentucky 6th Congressional District - Soybean Sales Heat Map

Interactive, embeddable heat map visualization showing 2022 soybean sales data for Kentucky's 6th Congressional District using official US Census TIGER geographic boundaries.

## 🌐 Live Demo

**[View Interactive Map](https://iamcstevenson.github.io/kentucky-district6-heatmap/)**

## 📋 Overview

This project creates an interactive SVG-based heat map that visualizes soybean sales across the 16 counties (14 full, 2 partial) within Kentucky's 6th Congressional District. The map features precise geographic boundaries from US Census TIGER shapefiles and responsive design optimized for both desktop and mobile viewing.

## ✨ Features

### 🗺️ **Geographic Accuracy**
- **Official US Census TIGER Shapefiles**: Uses 2024 congressional district and county boundary data
- **Precise District Boundaries**: Black solid perimeter line showing exact 6th District limits
- **All 120 Kentucky Counties**: Complete state coverage with district-specific highlighting

### 🎨 **Interactive Visualization**
- **Heat Map Coloring**: White ($0) to dark green ($10.5M) gradient based on sales volume
- **Selective Interaction**: Mouse hover effects only for counties within the district
- **Royal Blue County Borders**: District counties outlined in blue with darker hover state
- **Formatted Popups**: Display county name and formatted dollar amounts (e.g., "$10,516,000")

### 📱 **Responsive Design**
- **Mobile Optimization**: Collapsible header on screens ≤768px for better map visibility
- **Touch-Friendly**: Clickable title with ▼/▲ toggle icon for mobile text expansion
- **Desktop Full View**: Always displays complete content on larger screens
- **Smooth Animations**: CSS transitions for expand/collapse actions

### 📊 **Data Integration**
- **2022 Soybean Sales**: US Census of Agriculture data
- **District Coverage**: 16 counties with $43.7M total sales
- **Sales Range**: $0 (Jessamine, Clark, Madison) to $10,516,000 (Mercer)

## 🏗️ Technical Specifications

### **File Structure**
```
├── kentucky-district6-embeddable.html    # Main interactive map (3.9MB)
├── generate_district6_map.py             # Python generator script
├── kentucky-soybean-sales-2022.csv       # Full state sales data
├── district6-soybean-sales.csv           # District-specific data
├── ky_counties.json                      # County boundary data (178KB)
├── ky_county_list.txt                    # County reference list
├── ky_counties_summary.txt               # Processing documentation
├── process_ky_counties.py                # Shapefile processing script
└── index.html                            # GitHub Pages redirect
```

**Note**: US Census TIGER shapefiles are excluded from the repository due to file size limits. Download separately from [US Census Bureau](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html).

### **Technologies Used**
- **Python**: GeoPandas, ogr2ogr for GIS processing
- **Frontend**: Pure HTML5, CSS3, vanilla JavaScript
- **SVG Graphics**: 1000×500 viewBox, responsive scaling
- **Data Format**: US Census TIGER shapefiles → GeoJSON → SVG paths

### **Browser Compatibility**
- Modern browsers supporting SVG, CSS Grid, and ES6 JavaScript
- Mobile-responsive design tested on iOS Safari and Android Chrome
- Template literal string concatenation for cross-browser compatibility

## 📈 District 6 Coverage

### **Counties Included (16 total)**
**Full Counties (14):**
Anderson, Bath, Bourbon, Clark, Estill, Fayette, Fleming, Garrard, Jessamine, Madison, Mercer, Montgomery, Nicholas, Powell, Scott, Woodford

**Partial Counties (2):**
*Note: Anderson and Bath counties have portions extending outside the district boundary*

### **Sales Distribution**
- **Highest Sales**: Mercer County ($10,516,000)
- **Lowest Sales**: Jessamine, Clark, Madison ($0)
- **District Total**: ~$43.7 million (2022)

## 🔧 Usage

### **Embedding**
The map is designed for easy embedding:

```html
<iframe src="https://iamcstevenson.github.io/kentucky-district6-heatmap/"
        width="100%" height="600" frameborder="0">
</iframe>
```

### **Standalone Use**
Download `kentucky-district6-embeddable.html` for self-contained deployment.

### **Regeneration**
To update data or modify the visualization:

```bash
python3 generate_district6_map.py
```

**Dependencies:**
- Python 3.7+
- GeoPandas, ogr2ogr (GDAL)
- US Census TIGER shapefiles

## 📊 Data Sources

- **Geographic Boundaries**: US Census Bureau TIGER/Line Shapefiles (2024)
- **Congressional Districts**: `tl_2024_21_cd119.shp` (119th Congress)
- **County Boundaries**: `tl_2024_us_county.shp` (Kentucky subset)
- **Agricultural Data**: US Census of Agriculture (2022)

## 🎯 Design Specifications

### **Color Scheme**
- **Heat Map**: HSL gradient from white to dark green (120° hue, 60-90% saturation, 15-80% lightness)
- **District Counties**: Royal blue borders (#4169E1)
- **District Boundary**: Black solid line (2px)
- **Non-District**: Light gray fill (#f5f5f5)

### **Typography**
- **Primary Font**: Arial, sans-serif
- **Header**: 1.5em (desktop), 1.2em (mobile)
- **Attribution**: 0.75em, italicized

### **Responsive Breakpoints**
- **Mobile**: ≤768px (collapsible header)
- **Desktop**: >768px (full content display)

## 🚀 Development

### **Generator Script Features**
1. **TIGER Data Extraction**: Automated shapefile processing
2. **Coordinate Transformation**: Geographic → SVG coordinate system
3. **Color Calculation**: Dynamic heat map scaling
4. **HTML Generation**: Complete embeddable output
5. **Data Validation**: County verification and sales mapping

### **Performance Optimizations**
- **Simplified Geometries**: Optimized for web performance
- **Embedded Assets**: Self-contained HTML file
- **Efficient SVG**: Optimized path data
- **Responsive Images**: Vector graphics scale perfectly

## 📝 Attribution

- **Data Source**: US Census of Agriculture (2022)
- **Geographic Data**: US Census Bureau TIGER/Line Shapefiles
- **Processing**: GeoPandas, GDAL/OGR tools
- **Generated with**: [Claude Code](https://claude.ai/code)

## 📄 License

This project uses public domain US Census data. The visualization code and processing scripts are available for educational and non-commercial use.

---

**Repository**: https://github.com/iamcstevenson/kentucky-district6-heatmap
**Live Demo**: https://iamcstevenson.github.io/kentucky-district6-heatmap/
**Last Updated**: September 2025