import base64
import hashlib
import hmac
from typing import NamedTuple

from app.config import settings

TRIP_LENGTH = 10
MAX_NAME_LENGTH = 50
MAX_TRIP_PASSWORD_LENGTH = 200


class Identity(NamedTuple):
    name: str
    trip: str | None


def compute_trip(password: str) -> str:
    digest = hmac.new(
        settings.trip_secret.encode(), password.encode(), hashlib.sha256
    ).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")[:TRIP_LENGTH]


def resolve_identity(raw_name: str) -> Identity:
    name, _, trip_password = raw_name.partition("#")
    name = name.strip()[:MAX_NAME_LENGTH] or "名無しさん"

    if not trip_password:
        return Identity(name=name, trip=None)

    trip = compute_trip(trip_password[:MAX_TRIP_PASSWORD_LENGTH])
    return Identity(name=name, trip=trip)
