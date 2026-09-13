from datetime import datetime, timezone

from app.services.price_normalizer import compute_itinerary_hash


def test_same_itinerary_produces_same_hash():
    depart = datetime(2026, 11, 17, 9, 35, tzinfo=timezone.utc)
    arrive = datetime(2026, 11, 17, 13, 0, tzinfo=timezone.utc)
    assert compute_itinerary_hash("KE", "KE631", depart, arrive) == compute_itinerary_hash(
        "KE", "KE631", depart, arrive
    )


def test_different_flight_number_produces_different_hash():
    depart = datetime(2026, 11, 17, 9, 35, tzinfo=timezone.utc)
    arrive = datetime(2026, 11, 17, 13, 0, tzinfo=timezone.utc)
    assert compute_itinerary_hash("KE", "KE631", depart, arrive) != compute_itinerary_hash(
        "KE", "KE999", depart, arrive
    )
