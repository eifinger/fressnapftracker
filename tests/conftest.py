"""Global fixtures for fressnapftracker tests."""

import pytest


@pytest.fixture
def serial_number() -> str:
    """Return test serial number."""
    return "test_serialnumber"


@pytest.fixture
def device_token() -> str:
    """Return test device token."""
    return "test_device_token"


@pytest.fixture
def auth_token() -> str:
    """Return test auth token."""
    return "test_auth_token"
