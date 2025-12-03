"""A module to query the Fressnapf Tracker GPS API."""

import asyncio
from importlib import metadata
from typing import Any, Self

import httpx

from .exceptions import (
    FressnapfTrackerAuthenticationError,
    FressnapfTrackerConnectionError,
    FressnapfTrackerError,
    FressnapfTrackerInvalidDeviceTokenError,
    FressnapfTrackerInvalidSerialNumberError,
    FressnapfTrackerInvalidTokenError,
    FressnapfTrackerInvalidPhoneNumberError,
)
from .models import (
    Device,
    PhoneVerificationResponse,
    SmsCodeResponse,
    Tracker,
)

API_HOST = "itsmybike.cloud"
AUTH_HOST = "user.iot-pet-tracking.cloud"
API_BASE_URL = f"https://{API_HOST}/api/pet_tracker/v2"
AUTH_BASE_URL = f"https://{AUTH_HOST}/api/app/v1"

# Static cloud auth token used by the Fressnapf app
CLOUD_AUTH_TOKEN = "FgvX_UJ7!BQRLU((1WhwFoOp"  # noqa: S105

LIB_VERSION = metadata.version(__package__ or "fressnapftracker")


class _BaseClient:
    """Base class for API clients with shared HTTP functionality."""

    def __init__(
        self,
        *,
        request_timeout: int = 10,
        client: httpx.AsyncClient | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Initialize the base client.

        Args:
            request_timeout: Request timeout in seconds.
            client: Optional httpx AsyncClient to use.
            user_agent: Optional custom user agent string.

        """
        self._client = client
        self._close_client = False
        self.request_timeout = request_timeout
        self.user_agent = user_agent or f"fressnapftracker/{LIB_VERSION}"

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the httpx client."""
        if self._client is None:
            self._client = httpx.AsyncClient()
            self._close_client = True
        return self._client

    async def _request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, str] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> Any:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PUT).
            url: Full URL to request.
            headers: Request headers.
            params: Optional query parameters.
            json_data: Optional JSON body data.

        Returns:
            The JSON response (dict or list).

        Raises:
            FressnapfTrackerConnectionError: Connection or timeout error.
            FressnapfTrackerError: Other API errors.

        """
        client = await self._get_client()

        try:
            response = await asyncio.wait_for(
                client.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json_data,
                ),
                timeout=self.request_timeout,
            )
        except TimeoutError as exception:
            raise FressnapfTrackerConnectionError(
                "Timeout occurred while connecting to the Fressnapf Tracker API."
            ) from exception
        except httpx.HTTPError as exception:
            raise FressnapfTrackerConnectionError(
                "Error occurred while communicating with the Fressnapf Tracker API."
            ) from exception

        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            raise FressnapfTrackerError(f"Unexpected response type: {content_type}")

        return response.json()

    async def close(self) -> None:
        """Close open client session."""
        if self._client and self._close_client:
            await self._client.aclose()

    async def __aenter__(self) -> Self:
        """Async enter."""
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit."""
        await self.close()


class AuthClient(_BaseClient):
    """Client for handling authentication with the Fressnapf Tracker API."""

    def _get_auth_headers(self) -> dict[str, str]:
        """Get headers for auth API requests."""
        return {
            "accept": "application/json",
            "accept-encoding": "gzip",
            "Connection": "keep-alive",
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
            "Authorization": f"Bearer {CLOUD_AUTH_TOKEN}",
        }

    async def request_sms_code(self, phone_number: str, locale: str = "en") -> SmsCodeResponse:
        """Request an SMS verification code.

        Args:
            phone_number: Phone number in E.164 format (e.g., +49123456789).
            locale: Locale for the SMS message (default: "en").

        Returns:
            SmsCodeResponse with user ID for verification.

        """
        url = f"{AUTH_BASE_URL}/users/request_sms_code"
        headers = self._get_auth_headers()
        body = {
            "user": {
                "phone": phone_number,
                "locale": locale,
            },
            "tracker_service": "fressnapf",
        }

        result = await self._request("POST", url, headers, json_data=body)

        if (errors := result.get("errors")) is not None:
            if errors.get("phone", [{}])[0].get("error") == "invalid":
                raise FressnapfTrackerInvalidPhoneNumberError()
            else:
                raise FressnapfTrackerError(result)

        return SmsCodeResponse.model_validate(result)

    async def verify_phone_number(self, user_id: int, sms_code: int) -> PhoneVerificationResponse:
        """Verify phone number with SMS code.

        Args:
            user_id: User ID returned from request_sms_code.
            sms_code: The SMS verification code.

        Returns:
            PhoneVerificationResponse with user access token.

        """
        url = f"{AUTH_BASE_URL}/users/verify_phone_number"
        headers = self._get_auth_headers()
        body = {
            "user": {
                "id": user_id,
                "smscode": sms_code,
                "user_token": {
                    "push_token": "",
                    "app_version": "2.9.0_11",
                    "app_platform": "android",
                    "platform_version": 30,
                    "phone_name": "fressnapftracker",
                },
            },
        }

        result = await self._request("POST", url, headers, json_data=body)

        if "error" in result:
            error = result["error"]
            if "code did not match" in error:
                raise FressnapfTrackerInvalidTokenError(error)
            raise FressnapfTrackerError(error)

        return PhoneVerificationResponse.model_validate(result)

    async def get_devices(self, user_id: int, user_access_token: str) -> list[Device]:
        """Get list of devices for the authenticated user.

        Args:
            user_id: User ID from verification.
            user_access_token: Access token from verification.

        Returns:
            List of Device objects.

        """
        url = f"{AUTH_BASE_URL}/devices/"
        headers = self._get_auth_headers()
        params = {
            "user_id": user_id,
            "user_access_token": user_access_token,
        }

        result = await self._request("GET", url, headers, params=params)

        # The API returns a list of devices
        if isinstance(result, list):
            return [Device.model_validate(device) for device in result]

        if isinstance(result, dict) and "error" in result:
            error = result["error"]
            if "user_access_token" in error:
                raise FressnapfTrackerAuthenticationError(error)
            raise FressnapfTrackerError(error)

        raise FressnapfTrackerError("Unexpected response format from devices endpoint")


class ApiClient(_BaseClient):
    """Client for interacting with the Fressnapf Tracker device API."""

    def __init__(
        self,
        serial_number: str,
        device_token: str,
        *,
        request_timeout: int = 10,
        client: httpx.AsyncClient | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Initialize connection with Fressnapf Tracker.

        Args:
            serial_number: The serial number of the tracker device.
            device_token: The device token for API authentication.
            request_timeout: Request timeout in seconds.
            client: Optional httpx AsyncClient to use.
            user_agent: Optional custom user agent string.

        """
        super().__init__(request_timeout=request_timeout, client=client, user_agent=user_agent)
        self._serial_number = serial_number
        self._device_token = device_token

    def _get_device_headers(self) -> dict[str, str]:
        """Get headers for device API requests."""
        return {
            "accept": "application/json",
            "accept-encoding": "gzip",
            "authorization": f"Token token={CLOUD_AUTH_TOKEN}",
            "Connection": "keep-alive",
            "Host": API_HOST,
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
        }

    def _handle_device_error(self, result: dict[str, Any]) -> None:
        """Handle errors from device API responses.

        Args:
            result: The API response dictionary.

        Raises:
            FressnapfTrackerInvalidTokenError: Invalid auth token.
            FressnapfTrackerInvalidDeviceTokenError: Invalid device token.
            FressnapfTrackerInvalidSerialNumberError: Invalid serial number.
            FressnapfTrackerError: Other errors.

        """
        if "error" not in result:
            return

        error = result["error"]
        if "Access denied" in error:
            raise FressnapfTrackerInvalidTokenError(error)
        if "Invalid devicetoken" in error:
            raise FressnapfTrackerInvalidDeviceTokenError(error)
        if "Device not found" in error:
            raise FressnapfTrackerInvalidSerialNumberError(error)
        raise FressnapfTrackerError(error)

    async def _device_request(
        self,
        method: str,
        path: str,
        json_data: dict[str, Any] | None = None,
    ) -> Any:
        """Make a request to the device API.

        Args:
            method: HTTP method (GET, PUT).
            path: API path to append to device URL.
            json_data: Optional JSON body data.

        Returns:
            The JSON response dictionary.

        """
        url = f"{API_BASE_URL}/devices/{self._serial_number}{path}"
        params = {"devicetoken": self._device_token}
        result = await self._request(method, url, self._get_device_headers(), params=params, json_data=json_data)
        self._handle_device_error(result)
        return result

    async def get_tracker(self) -> Tracker:
        """Get tracker data from the API.

        Returns:
            Tracker object with all device data.

        """
        result = await self._device_request("GET", "")
        return Tracker.model_validate(result)

    async def set_led_brightness(self, brightness: int) -> None:
        """Set the LED brightness of the tracker.

        Args:
            brightness: Brightness value (0-100). 0 turns off the LED.

        Raises:
            ValueError: If brightness is not between 0 and 100.

        """
        if not 0 <= brightness <= 100:
            raise ValueError("Brightness must be between 0 and 100")
        await self._device_request("PUT", "/change_led_brightness", {"value": brightness})

    async def set_deep_sleep(self, enabled: bool) -> None:
        """Set the deep sleep mode of the tracker.

        Args:
            enabled: True to enable deep sleep, False to disable.

        """
        await self._device_request("PUT", "/change_deep_sleep", {"value": int(enabled)})

    async def set_energy_saving(self, enabled: bool) -> None:
        """Set the energy saving mode of the tracker.

        Args:
            enabled: True to enable energy saving, False to disable.

        """
        state = "enable" if enabled else "disable"
        await self._device_request("PATCH", f"/energy_saving/{state}")
