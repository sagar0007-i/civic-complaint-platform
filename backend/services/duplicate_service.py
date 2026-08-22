"""Duplicate Complaint Detection Service using geospatial and textual heuristics."""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from backend.config import settings
from backend.models.complaint import Complaint, ComplaintStatus
from backend.services.location_service import LocationService
from backend.utils.logging import logger


class DuplicateDetectionService:
    """Detects possible duplicate civic complaints near a given location and category."""

    def __init__(self, session: Session):
        self.session = session
        self.location_service = LocationService()

    @staticmethod
    def _text_similarity(text1: str, text2: str) -> float:
        """Compute Jaccard token overlap similarity between two text snippets."""
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())

        # Remove very common noise words
        stop_words = {"the", "a", "an", "is", "in", "at", "of", "on", "and", "near", "road", "street", "area"}
        tokens1 = {t.strip(".,!?:;\"'()") for t in tokens1 if len(t) > 2 and t not in stop_words}
        tokens2 = {t.strip(".,!?:;\"'()") for t in tokens2 if len(t) > 2 and t not in stop_words}

        if not tokens1 or not tokens2:
            return 0.0

        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        return len(intersection) / len(union)

    def find_potential_duplicates(
        self,
        category_id: str,
        latitude: float,
        longitude: float,
        title: str,
        description: str,
        max_results: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Search for potential duplicates:
        - Active status (not rejected)
        - Submitted within the configured days window (e.g. 14 days)
        - Within configured proximity radius (e.g. 150 meters)
        - Same category or high text similarity
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=settings.DUPLICATE_DAYS_WINDOW)

        # Query recent active complaints that have location data
        recent_complaints = (
            self.session.query(Complaint)
            .filter(
                Complaint.status.notin_([ComplaintStatus.REJECTED.value, ComplaintStatus.RESOLVED.value]),
                Complaint.created_at >= cutoff_date,
            )
            .all()
        )

        matches = []
        combined_text = f"{title} {description}"

        for comp in recent_complaints:
            if not comp.location:
                continue

            # Calculate Haversine distance in meters
            dist_meters = self.location_service.haversine_distance_meters(
                latitude,
                longitude,
                comp.location.latitude,
                comp.location.longitude,
            )

            if dist_meters <= settings.DUPLICATE_DISTANCE_METERS_THRESHOLD:
                # Proximity match! Check category & text similarity
                is_same_category = comp.category_id == category_id
                comp_text = f"{comp.title} {comp.description}"
                text_sim = self._text_similarity(combined_text, comp_text)

                # Score formulation: proximity weight + category match weight + text similarity weight
                score = (1.0 - (dist_meters / settings.DUPLICATE_DISTANCE_METERS_THRESHOLD)) * 0.4
                if is_same_category:
                    score += 0.4
                score += (text_sim * 0.2)

                if score >= 0.45 or (dist_meters < 50 and is_same_category):
                    matches.append(
                        {
                            "complaint_id": comp.id,
                            "complaint_number": comp.complaint_number,
                            "title": comp.title,
                            "category_name": comp.category.name if comp.category else "Unknown",
                            "status": comp.status,
                            "created_at": comp.created_at,
                            "distance_meters": round(dist_meters, 1),
                            "similarity_score": round(min(score, 1.0), 2),
                            "address": comp.location.address or comp.location.landmark or "Nearby",
                        }
                    )

        # Sort by highest similarity
        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        return matches[:max_results]
