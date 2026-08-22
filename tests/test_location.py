"""Location & Geospatial Unit Tests."""

import pytest
from backend.services.location_service import LocationService
from backend.models.ward import Ward


def test_haversine_distance_calculation():
    """Test Haversine distance between two known points."""
    # MG Road to Indiranagar (approx ~4.5 km)
    mg_road_lat, mg_road_lng = 12.9756, 77.6066
    indiranagar_lat, indiranagar_lng = 12.9784, 77.6408

    distance_m = LocationService.haversine_distance_meters(
        mg_road_lat, mg_road_lng, indiranagar_lat, indiranagar_lng
    )

    assert 3500 < distance_m < 4500


def test_find_nearest_ward():
    """Test finding nearest ward from a coordinates point."""
    loc_service = LocationService()
    w1 = Ward(name="Indiranagar", center_latitude=12.9784, center_longitude=77.6408)
    w2 = Ward(name="Whitefield", center_latitude=12.9698, center_longitude=77.7499)

    # Point very close to Indiranagar
    point_lat, point_lng = 12.9780, 77.6400
    nearest = loc_service.find_nearest_ward(point_lat, point_lng, [w1, w2])

    assert nearest is not None
    assert nearest.name == "Indiranagar"
