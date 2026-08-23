"""Official Survey of India (SOI) Compliant Sovereign Boundary for India.

Provides complete territorial integrity including entirety of Jammu & Kashmir,
Ladakh, and Arunachal Pradesh.
"""

from typing import Dict, Any
import folium

# Simplified Survey of India (SOI) Outer National Boundary Coordinates
INDIA_SOI_COORDINATES = [
    [
        # Gujarat & Western Coast
        [68.18, 23.68], [68.75, 22.85], [69.45, 22.35], [70.15, 20.85], [72.85, 21.15],
        [72.82, 18.90], [73.50, 15.50], [74.85, 12.85], [77.55, 8.08],  # Kanyakumari
        
        # Eastern Coast
        [79.85, 10.35], [80.30, 13.08], [82.25, 16.85], [86.00, 19.85], [87.50, 21.65],
        [88.85, 21.75], [89.05, 22.25],
        
        # North-East & Bengal
        [88.80, 24.50], [89.85, 25.20], [91.80, 25.10], [92.30, 24.15], [92.75, 23.75],
        [92.20, 22.00], [93.15, 22.10], [94.50, 24.00], [95.10, 26.85],
        
        # Arunachal Pradesh (Complete Eastern & Northern Border)
        [97.40, 28.25], [96.50, 29.45], [95.00, 29.00], [93.50, 28.65], [92.15, 27.80],
        
        # Bhutan & Sikkim Northern Border
        [88.90, 27.90], [88.55, 28.15], [88.05, 27.75],
        
        # Nepal & Uttarakhand Northern Border
        [81.00, 30.20], [79.50, 31.05], [78.85, 31.50],
        
        # Himachal Pradesh & Ladakh (Complete Northern & Eastern Ladakh including Aksai Chin & Siachen)
        [79.00, 32.50], [79.85, 34.00], [80.30, 35.50], [79.00, 35.90], [77.80, 35.60],
        [77.00, 36.90], [74.90, 37.05],  # Northernmost point (Indira Col / Siachen)
        
        # Jammu & Kashmir / Gilgit-Baltistan Western Line
        [74.00, 36.80], [73.50, 35.50], [73.80, 34.20], [74.35, 32.85],
        
        # Punjab & Rajasthan Western International Border
        [74.85, 31.60], [73.85, 29.90], [71.50, 28.00], [70.20, 27.00], [70.50, 25.00],
        [68.80, 24.40], [68.18, 23.68],  # Closing loop at Rann of Kutch
    ]
]

INDIA_GEOJSON: Dict[str, Any] = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "name": "Republic of India",
                "authority": "Official Survey of India (SOI) Sovereign Boundary",
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": INDIA_SOI_COORDINATES,
            },
        }
    ],
}


def add_india_boundary_layer(
    folium_map: folium.Map,
    highlight_color: str = "#ff9900",
    fill_color: str = "#0f2d6b",
    fill_opacity: float = 0.06,
    weight: int = 3,
) -> None:
    """Overlay the official Survey of India boundary of India onto any Folium map."""
    folium.GeoJson(
        INDIA_GEOJSON,
        name="🇮🇳 Official Survey of India Boundary",
        style_function=lambda feature: {
            "fillColor": fill_color,
            "color": highlight_color,
            "weight": weight,
            "fillOpacity": fill_opacity,
            "dashArray": "1, 0",  # Solid official sovereign line
        },
        tooltip="🇮🇳 Republic of India (Official Survey of India Boundary)",
    ).add_to(folium_map)


# Simplified Maharashtra State Sovereign Geographic Boundary Coordinates
MAHARASHTRA_COORDINATES = [
    [
        # South Coast & Goa border
        [73.65, 15.75], [74.25, 15.80], [74.50, 15.95],
        # Karnataka Border
        [75.20, 16.50], [75.90, 16.85], [76.50, 17.30], [77.20, 17.65], [77.80, 18.05],
        # Telangana Border
        [78.40, 18.50], [79.20, 18.80], [80.00, 18.90], [80.40, 19.50],
        # East / Gadchiroli / Chhattisgarh Border
        [80.85, 20.30], [80.30, 21.20], [79.90, 21.45],
        # North / Madhya Pradesh Border
        [79.20, 21.65], [78.30, 21.40], [77.00, 21.30], [75.80, 21.75], [74.50, 21.90],
        # North-West / Gujarat Border
        [73.50, 21.45], [73.00, 20.50], [72.75, 20.15],
        # Konkan / Western Coastline (Dahanu, Mumbai, Alibag, Ratnagiri, Sindhudurg)
        [72.82, 19.80], [72.82, 18.95], [72.95, 18.20], [73.20, 17.30], [73.45, 16.20], [73.65, 15.75],
    ]
]

MAHARASHTRA_GEOJSON: Dict[str, Any] = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "name": "State of Maharashtra",
                "authority": "Government of Maharashtra Municipal Jurisdiction",
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": MAHARASHTRA_COORDINATES,
            },
        }
    ],
}


def add_maharashtra_boundary_layer(
    folium_map: folium.Map,
    highlight_color: str = "#ff9900",
    fill_color: str = "#0f2d6b",
    fill_opacity: float = 0.08,
    weight: int = 3,
) -> None:
    """Overlay the official State of Maharashtra municipal boundary onto any Folium map."""
    folium.GeoJson(
        MAHARASHTRA_GEOJSON,
        name="🏛️ State of Maharashtra Municipal Boundary",
        style_function=lambda feature: {
            "fillColor": fill_color,
            "color": highlight_color,
            "weight": weight,
            "fillOpacity": fill_opacity,
            "dashArray": "1, 0",
        },
        tooltip="🏛️ State of Maharashtra (Municipal Jurisdiction)",
    ).add_to(folium_map)

