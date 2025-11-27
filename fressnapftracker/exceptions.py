"""Exceptions for fressnapftracker."""


class FressnapfTrackerError(Exception):
    """Generic Fressnapf Tracker exception."""


class FressnapfTrackerConnectionError(FressnapfTrackerError):
    """Fressnapf Tracker connection exception."""


class FressnapfTrackerAuthenticationError(FressnapfTrackerError):
    """Fressnapf Tracker authentication exception."""


class FressnapfTrackerInvalidPhoneNumberError(FressnapfTrackerAuthenticationError):
    """Fressnapf Tracker invalid phone number exception."""


class FressnapfTrackerInvalidTokenError(FressnapfTrackerAuthenticationError):
    """Fressnapf Tracker invalid token exception."""


class FressnapfTrackerInvalidDeviceTokenError(FressnapfTrackerAuthenticationError):
    """Fressnapf Tracker invalid device token exception."""


class FressnapfTrackerInvalidSerialNumberError(FressnapfTrackerError):
    """Fressnapf Tracker invalid serial number exception."""
