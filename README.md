# Kentucky 6th Congressional District - Soybean Sales Heat Map

Interactive, embeddable heat map visualization showing 2022 soybean sales data for Kentucky's 6th Congressional District using official US Census TIGER geographic boundaries.

## 🌐 Live Demo

**[View Interactive Map](https://iamcstevenson.github.io/kentucky-district6-heatmap/)**

## 📋 Overview

This project creates an interactive SVG-based heat map that visualizes soybean sales across the 16 counties within Kentucky's 6th Congressional District. The map features a modern, professional design with precise geographic boundaries from US Census TIGER shapefiles and responsive design optimized for desktop, tablet, and mobile viewing with advanced pinch-zoom support.

## ✨ Features

### 🗺️ **Geographic Accuracy**
- **District-Only Visualization**: Shows only the 16 counties within the 6th Congressional District
- **Official US Census TIGER Shapefiles**: Uses 2024 congressional district and county boundary data
- **Precise County Boundaries**: Royal blue borders (#4169E1) for clear county delineation

### 🎨 **Modern Design & Interactivity**
- **Professional UI**: Clean, card-based layout with Inter font and CSS custom properties
- **Heat Map Coloring**: White ($0) to dark forest green ($10.5M) HSL gradient based on sales volume
- **Smart Tooltips**: Pinch-zoom safe tooltips with click-to-pin functionality
- **Hover Effects**: Smooth transitions with brightness adjustments and stroke changes
- **Formatted Data**: Display county names and formatted dollar amounts (e.g., "$10,516,000")

### 📱 **Responsive Design**
- **Phone Optimized (≤600px)**: 3.0x zoom with centered positioning, collapsible description panel
- **Tablet Support (700-1180px)**: 1.65-1.75x zoom with optimized aspect ratios for portrait/landscape
- **Desktop View (≥1181px)**: 2-column layout with map and description side-by-side
- **Touch-Friendly**: Pointer events support, tap-to-pin tooltips, smooth pinch-zoom
- **Accessibility**: ARIA labels, keyboard navigation, and semantic HTML

### 📊 **Data Integration**
- **2022 Soybean Sales**: US Census of Agriculture data
- **District Coverage**: 16 counties with $43.7M total sales
- **Sales Range**: $0 (Jessamine, Clark, Madison) to $10,516,000 (Mercer)

## 🏗️ Technical Specifications

### **File Structure**
```
├── kentucky-district6-embeddable.html    # Main interactive map (46KB)
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
- **Frontend**: Pure HTML5, CSS3 (custom properties), vanilla JavaScript
- **Typography**: Inter font family from Google Fonts
- **SVG Graphics**: 800×400 viewBox with preserveAspectRatio="xMidYMid meet"
- **Responsive Design**: CSS media queries with 3 breakpoints (600px, 700-1180px, 1181px+)
- **Data Format**: US Census TIGER shapefiles → GeoJSON → SVG paths

### **Browser Compatibility**
- Modern browsers supporting SVG, CSS Grid, CSS Custom Properties, and ES6 JavaScript
- Mobile-responsive design tested on iOS Safari and Android Chrome
- Pointer Events API for unified mouse/touch interaction
- MutationObserver for dynamic SVG loading

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
- **Background**: Soft green-tinted gray (#f3f7f4)
- **Card**: Pure white (#ffffff) with subtle shadow
- **Heat Map**: HSL gradient from white to dark forest green (120° hue, 60-90% saturation, 15-80% lightness)
- **County Borders**: Royal blue (#4169E1) with darker hover state (#1e40af)
- **Accent Colors**: Deep green (#0f766e), bright green (#16a34a)
- **Gradients**: Linear gradients for headers and panels

### **Typography**
- **Primary Font**: Inter (Google Fonts), with system fallbacks
- **Header**: 1.25rem (desktop), 1.28rem (mobile)
- **Body**: 0.95rem with line-height 1.5-1.6
- **Weights**: 300 (light), 400 (regular), 600 (semi-bold), 700 (bold)

### **Responsive Breakpoints**
- **Phone**: ≤600px (vertical layout, 3.0x zoom, collapsible description)
- **Tablet**: 700-1180px (vertical layout, 1.65-1.75x zoom)
- **Desktop**: ≥1181px (2-column layout, 2.0x zoom)

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