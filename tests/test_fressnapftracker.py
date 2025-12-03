"""Tests for fressnapftracker."""

import json
import os

import httpx
import pytest
import respx

from fressnapftracker import (
    ApiClient,
    AuthClient,
    FressnapfTrackerAuthenticationError,
    FressnapfTrackerConnectionError,
    FressnapfTrackerError,
    FressnapfTrackerInvalidDeviceTokenError,
    FressnapfTrackerInvalidPhoneNumberError,
    FressnapfTrackerInvalidSerialNumberError,
    FressnapfTrackerInvalidTokenError,
)
from fressnapftracker.fressnapftracker import API_BASE_URL, AUTH_BASE_URL


def load_fixture(filename: str) -> str:
    """Load a fixture file."""
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path, encoding="utf-8") as fptr:
        return fptr.read()


class TestGetTracker:
    """Tests for get_tracker method."""

    @respx.mock
    async def test_get_tracker(self, serial_number: str, device_token: str):
        """Test getting tracker data."""
        respx.get(
            f"{API_BASE_URL}/devices/{serial_number}",
            params={"devicetoken": device_token},
        ).mock(
            return_value=httpx.Response(
                200,
                json=json.loads(load_fixture("get_tracker_response.json")),
            )
        )

        async with ApiClient(
            serial_number=serial_number,
            device_token=device_token,
        ) as api:
            tracker = await api.get_tracker()

        assert tracker.name == "Test Pet"
        assert tracker.battery == 85
        assert tracker.charging is False
        assert tracker.position is not None
        assert tracker.position.lat == 52.520008
        assert tracker.position.lng == 13.404954
        assert tracker.position.accuracy == 10
        assert tracker.position.created_at == "2025-12-02T20:25:31.000+01:00"
        assert tracker.position.sampled_at == "2025-12-02T20:25:30.000+01:00"
        assert tracker.tracker_settings.generation == "2.1"
        assert tracker.tracker_settings.type == "dog"
        assert tracker.supports_flash_light is True
        assert tracker.supports_sleep_mode is True
        assert tracker.supports_energy_saving_mode is False
        assert tracker.supports_live_tracking is False
        assert tracker.led_brightness_value == 50
        assert tracker.deep_sleep_value == 0
        assert tracker.led_activatable_overall is True
        assert tracker.led_activatable is not None
        assert tracker.led_activatable.has_led is True
        assert tracker.led_activatable.seen_recently is False
        assert tracker.led_activatable.nonempty_battery is True
        assert tracker.led_activatable.not_charging is True
        assert tracker.energy_saving is not None
        assert tracker.energy_saving.value == 0
        assert tracker.servicebooking is not None
        assert tracker.servicebooking.has_current_servicebooking is True
        assert tracker.servicebooking.days_until_servicebooking_ends == 184
        assert tracker.inside_geofence is False
        assert tracker.serialnumber == "231511297"
        assert tracker.icon is not None
        assert tracker.last_seen == "about 2 hours"

    @respx.mock
    async def test_get_tracker_minimal(self, serial_number: str, device_token: str):
        """Test getting tracker data with minimal response."""
        respx.get(
            f"{API_BASE_URL}/devices/{serial_number}",
            params={"devicetoken": device_token},
        ).mock(
            return_value=httpx.Response(
                200,
                json=json.loads(load_fixture("get_tracker_response_minimal.json")),
            )
        )

        async with ApiClient(
            serial_number=serial_number,
            device_token=device_token,
        ) as api:
            tracker = await api.get_tracker()

        assert tracker.name == "Test Pet"
        assert tracker.battery == 50
        assert tracker.charging is True
        assert tracker.position is None
        assert tracker.supports_flash_light is False
        assert tracker.supports_sleep_mode is False
        assert tracker.led_brightness_value is None
        assert tracker.deep_sleep_value is None

    @respx.mock
    async def test_get_tracker_access_denied(self, serial_number: str, device_token: str):
        """Test get_tracker raises error on access denied."""
        respx.get(
            f"{API_BASE_URL}/devices/{serial_number}",
            params={"devicetoken": device_token},
        ).mock(
            return_value=httpx.Response(
                401,
                json=json.loads(load_fixture("error_access_denied.json")),
            )
        )

        async with ApiClient(
            serial_number=serial_number,
            device_token=device_token,
        ) as api:
            with pytest.raises(FressnapfTrackerInvalidTokenError):
                await api.get_tracker()

    @respx.mock
    async def test_get_tracker_invalid_device_token(self, serial_number: str, device_token: str):
        """Test get_tracker raises error on invalid device token."""
        respx.get(
            f"{API_BASE_URL}/devices/{serial_number}",
            params={"devicetoken": device_token},
        ).mock(
            return_value=httpx.Response(
                401,
                json=json.loads(load_fixture("error_invalid_devicetoken.json")),
            )
        )

        async with ApiClient(
            serial_number=serial_number,
            device_token=device_token,
        ) as api:
            with pytest.raises(FressnapfTrackerInvalidDeviceTokenError):
                await api.get_tracker()

    @respx.mock
    async def test_get_tracker_device_not_found(self, serial_number: str, device_token: str):
        """Test get_tracker raises error on device not found."""
        respx.get(
            f"{API_BASE_URL}/devices/{serial_number}",
            params={"devicetoken": device_token},
        ).mock(
            return_value=httpx.Response(
                404,
                json=json.loads(load_fixture("error_device_not_found.json")),
            )
        )

        async with ApiClient(
            serial_number=serial_number,
            device_token=device_token,
        ) as api:
            with pytest.raises(FressnapfTrackerInvalidSerialNumberError):
                await api.get_tracker()


class TestSetLedBrightness:
    """Tests for set_led_brightness method."""

    @respx.mock
    async def test_set_led_brightness(self, serial_number: str, device_token: str):
        """Test setting LED brightness."""
        respx.put(
            f"{API_BASE_URL}/devices/{serial_number}/change_led_brightness",
            params={"devicetoken": device_token},
        ).mock(
            return_value=httpx.Response(
                200,
                json=json.loads(load_fixture("put_success_response.json")),
            )
        )

        async with ApiClient(
            serial_number=serial_number,
            device_token=device_token,
        ) as api:
            await api.set_led_brightness(75)

    async def test_set_led_brightness_invalid_value(self, serial_number: str, device_token: str):
        """Test set_led_brightness raises error for invalid value."""
        async with ApiClient(
            serial_number=serial_number,
            device_token=device_token,
        ) as api:
            with pytest.raises(ValueError) as exc_info:
                await api.set_led_brightness(150)
            assert "Brightness must be between 0 and 100" in str(exc_info.value)


class TestSetDeepSleep:
    """Tests for set_deep_sleep method."""

    @respx.mock
    async def test_set_deep_sleep_on(self, serial_number: str, device_token: str):
        """Test enabling deep sleep."""
        respx.put(
            f"{API_BASE_URL}/devices/{serial_number}/change_deep_sleep",
            params={"devicetoken": device_token},
        ).mock(
            return_value=httpx.Response(
                200,
                json=json.loads(load_fixture("put_success_response.json")),
            )
        )

        async with ApiClient(
            serial_number=serial_number,
            device_token=device_token,
        ) as api:
            await api.set_deep_sleep(True)

    @respx.mock
    async def test_set_deep_sleep_off(self, serial_number: str, device_token: str):
        """Test disabling deep sleep."""
        respx.put(
            f"{API_BASE_URL}/devices/{serial_number}/change_deep_sleep",
            params={"devicetoken": device_token},
        ).mock(
            return_value=httpx.Response(
                200,
                json=json.loads(load_fixture("put_success_response.json")),
            )
        )

        async with ApiClient(
            serial_number=serial_number,
            device_token=device_token,
        ) as api:
            await api.set_deep_sleep(False)


class TestSetEnergySaving:
    """Tests for set_energy_saving method."""

    @respx.mock
    async def test_set_energy_saving_on(self, serial_number: str, device_token: str):
        """Test enabling energy saving."""
        respx.patch(
            f"{API_BASE_URL}/devices/{serial_number}/energy_saving/enable",
            params={"devicetoken": device_token},
        ).mock(
            return_value=httpx.Response(
                200,
                json=json.loads(load_fixture("put_success_response.json")),
            )
        )

        async with ApiClient(
            serial_number=serial_number,
            device_token=device_token,
        ) as api:
            await api.set_energy_saving(True)

    @respx.mock
    async def test_set_energy_saving_off(self, serial_number: str, device_token: str):
        """Test disabling energy saving."""
        respx.patch(
            f"{API_BASE_URL}/devices/{serial_number}/energy_saving/disable",
            params={"devicetoken": device_token},
        ).mock(
            return_value=httpx.Response(
                200,
                json=json.loads(load_fixture("put_success_response.json")),
            )
        )

        async with ApiClient(
            serial_number=serial_number,
            device_token=device_token,
        ) as api:
            await api.set_energy_saving(False)


class TestAuthentication:
    """Tests for authentication methods."""

    @respx.mock
    async def test_request_sms_code(self):
        """Test requesting SMS code."""
        respx.post(f"{AUTH_BASE_URL}/users/request_sms_code").mock(
            return_value=httpx.Response(
                200,
                json=json.loads(load_fixture("sms_code_response.json")),
            )
        )

        async with AuthClient() as auth:
            response = await auth.request_sms_code("+49123456789")

        assert response.id == 12345

    @respx.mock
    async def test_request_sms_code_invalid_phone_number(self):
        """Test requesting SMS code with invalid phone number."""
        respx.post(f"{AUTH_BASE_URL}/users/request_sms_code").mock(
            return_value=httpx.Response(
                200,
                json=json.loads(load_fixture("error_invalid_phone_number.json")),
            )
        )

        async with AuthClient() as auth:
            with pytest.raises(FressnapfTrackerInvalidPhoneNumberError):
                await auth.request_sms_code("invalid_phone")

    @respx.mock
    async def test_verify_phone_number(self):
        """Test verifying phone number."""
        respx.post(f"{AUTH_BASE_URL}/users/verify_phone_number").mock(
            return_value=httpx.Response(
                200,
                json=json.loads(load_fixture("verify_phone_response.json")),
            )
        )

        async with AuthClient() as auth:
            response = await auth.verify_phone_number(12345, 123456)

        assert response.user_token.access_token == "test_access_token_12345"
        assert response.user_token.refresh_token == "test_refresh_token_12345"

    @respx.mock
    async def test_verify_phone_number_invalid_code(self):
        """Test verifying phone number with invalid code."""
        respx.post(f"{AUTH_BASE_URL}/users/verify_phone_number").mock(
            return_value=httpx.Response(
                401,
                json=json.loads(load_fixture("error_invalid_sms_code.json")),
            )
        )

        async with AuthClient() as auth:
            with pytest.raises(FressnapfTrackerInvalidTokenError):
                await auth.verify_phone_number(12345, 000000)

    @respx.mock
    async def test_get_devices(self):
        """Test getting devices list."""
        respx.get(f"{AUTH_BASE_URL}/devices/").mock(
            return_value=httpx.Response(
                200,
                json=json.loads(load_fixture("get_devices_response.json")),
            )
        )

        async with AuthClient() as auth:
            devices = await auth.get_devices(12345, "access_token")

        assert len(devices) == 2
        assert devices[0].serialnumber == "ABC123456"
        assert devices[0].token == "device_token_1"
        assert devices[1].serialnumber == "DEF789012"
        assert devices[1].token == "device_token_2"

    @respx.mock
    async def test_get_devices_invalid_token(self):
        """Test get_devices with invalid access token."""
        respx.get(f"{AUTH_BASE_URL}/devices/").mock(
            return_value=httpx.Response(
                401,
                json=json.loads(load_fixture("error_invalid_access_token.json")),
            )
        )

        async with AuthClient() as auth:
            with pytest.raises(FressnapfTrackerAuthenticationError):
                await auth.get_devices("user_12345", "invalid_token")


class TestConnectionErrors:
    """Tests for connection error handling."""

    @respx.mock
    async def test_timeout_error(self, serial_number: str, device_token: str):
        """Test timeout error handling."""
        respx.get(
            f"{API_BASE_URL}/devices/{serial_number}",
            params={"devicetoken": device_token},
        ).mock(side_effect=httpx.TimeoutException("Timeout"))

        async with ApiClient(
            serial_number=serial_number,
            device_token=device_token,
            request_timeout=1,
        ) as api:
            with pytest.raises(FressnapfTrackerConnectionError) as exc_info:
                await api.get_tracker()
            assert "Error occurred while communicating" in str(exc_info.value)

    @respx.mock
    async def test_connection_error(self, serial_number: str, device_token: str):
        """Test connection error handling."""
        respx.get(
            f"{API_BASE_URL}/devices/{serial_number}",
            params={"devicetoken": device_token},
        ).mock(side_effect=httpx.ConnectError("Connection failed"))

        async with ApiClient(
            serial_number=serial_number,
            device_token=device_token,
        ) as api:
            with pytest.raises(FressnapfTrackerConnectionError):
                await api.get_tracker()

    @respx.mock
    async def test_unexpected_content_type(self, serial_number: str, device_token: str):
        """Test handling of unexpected content type."""
        respx.get(
            f"{API_BASE_URL}/devices/{serial_number}",
            params={"devicetoken": device_token},
        ).mock(
            return_value=httpx.Response(
                200,
                content=b"<html>Not JSON</html>",
                headers={"Content-Type": "text/html"},
            )
        )

        async with ApiClient(
            serial_number=serial_number,
            device_token=device_token,
        ) as api:
            with pytest.raises(FressnapfTrackerError) as exc_info:
                await api.get_tracker()
            assert "Unexpected response type" in str(exc_info.value)
