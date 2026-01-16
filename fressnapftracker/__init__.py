"""Asynchronous Python client for the Fressnapf Tracker GPS API."""

from .exceptions import (
    FressnapfTrackerError,
    FressnapfTrackerConnectionError,
    FressnapfTrackerAuthenticationError,
    FressnapfTrackerInvalidPhoneNumberError,
    FressnapfTrackerInvalidTokenError,
    FressnapfTrackerInvalidDeviceTokenError,
    FressnapfTrackerInvalidSerialNumberError,
    FressnapfTrackerInvalidTrackerResponseError,
)
from .fressnapftracker import ApiClient, AuthClient
from .models import (
    Device,
    Position,
    TrackerFeatures,
    TrackerSettings,
    LedBrightness,
    DeepSleep,
    EnergySaving,
    LedActivatable,
    ServiceBooking,
    Tracker,
    UserToken,
    PhoneVerificationResponse,
    SmsCodeResponse,
)

__all__ = [
    "ApiClient",
    "AuthClient",
    "FressnapfTrackerError",
    "FressnapfTrackerConnectionError",
    "FressnapfTrackerAuthenticationError",
    "FressnapfTrackerInvalidPhoneNumberError",
    "FressnapfTrackerInvalidTokenError",
    "FressnapfTrackerInvalidDeviceTokenError",
    "FressnapfTrackerInvalidSerialNumberError",
    "FressnapfTrackerInvalidTrackerResponseError",
    "Device",
    "Position",
    "TrackerFeatures",
    "TrackerSettings",
    "LedBrightness",
    "DeepSleep",
    "EnergySaving",
    "LedActivatable",
    "ServiceBooking",
    "Tracker",
    "UserToken",
    "PhoneVerificationResponse",
    "SmsCodeResponse",
]
