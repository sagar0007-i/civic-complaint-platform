"""Location Service, Geocoding, and Distance Calculation."""

import math
from typing import Optional, Dict, Any, List
from geopy.geocoders import Nominatim
from backend.config import settings
from backend.models.ward import Ward
from backend.utils.logging import logger


class LocationService:
    """Geospatial calculations and geocoding operations."""

    def __init__(self):
        self._geolocator = None

    @property
    def geolocator(self) -> Nominatim:
        if self._geolocator is None:
            self._geolocator = Nominatim(user_agent="civicpulse_geocoder")
        return self._geolocator

    @staticmethod
    def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great-circle distance between two points on the Earth
        using the Haversine formula (result in meters).
        """
        R = 6371000.0  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

        return R * c

    def reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Reverse geocode latitude & longitude to address string and components.
        Gracefully falls back if offline or rate-limited.
        """
        try:
            location = self.geolocator.reverse((lat, lon), language="en", timeout=3)
            if location and location.raw:
                address_dict = location.raw.get("address", {})
                display_name = location.address
                road = address_dict.get("road") or address_dict.get("suburb") or ""
                city = (
                    address_dict.get("city")
                    or address_dict.get("town")
                    or address_dict.get("state_district")
                    or settings.DEFAULT_CITY
                )
                pincode = address_dict.get("postcode", "")
                return {
                    "address": display_name,
                    "road": road,
                    "city": city,
                    "pincode": pincode,
                    "success": True,
                }
        except Exception as e:
            logger.warning(f"Reverse geocode lookup error for ({lat}, {lon}): {e}")

        # Fallback
        return {
            "address": f"Near coordinates {lat:.5f}, {lon:.5f}, {settings.DEFAULT_CITY}",
            "road": "",
            "city": settings.DEFAULT_CITY,
            "pincode": "",
            "success": False,
        }

    def find_nearest_ward(self, lat: float, lon: float, wards: List[Ward]) -> Optional[Ward]:
        """Find the geometrically closest ward from a list of wards."""
        if not wards:
            return None

        closest_ward = None
        min_dist = float("inf")

        for ward in wards:
            if ward.center_latitude is not None and ward.center_longitude is not None:
                dist = self.haversine_distance_meters(
                    lat, lon, ward.center_latitude, ward.center_longitude
                )
                if dist < min_dist:
                    min_dist = dist
                    closest_ward = ward

        return closest_ward

    @staticmethod
    def is_within_mumbai_bounds(lat: float, lon: float) -> bool:
        """Verify if coordinates fall within Greater Mumbai (BMC) municipal boundaries."""
        return 18.85 <= lat <= 19.35 and 72.70 <= lon <= 73.10

    @staticmethod
    def is_within_maharashtra_bounds(lat: float, lon: float) -> bool:
        """Verify if coordinates fall within Maharashtra state boundaries."""
        return 15.50 <= lat <= 22.20 and 72.50 <= lon <= 81.00
