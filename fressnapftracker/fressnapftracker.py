"""A module to query the Fressnapf Tracker GPS API."""

import asyncio
import logging
from collections.abc import Mapping
from importlib import metadata
from typing import Any, Self
from urllib.parse import quote

import httpx
from pydantic import ValidationError

from .exceptions import (
    FressnapfTrackerAuthenticationError,
    FressnapfTrackerConnectionError,
    FressnapfTrackerError,
    FressnapfTrackerInvalidDeviceTokenError,
    FressnapfTrackerInvalidSerialNumberError,
    FressnapfTrackerInvalidTokenError,
    FressnapfTrackerInvalidPhoneNumberError,
    FressnapfTrackerInvalidTrackerResponseError,
)
from .models import (
    AdditionalParameters,
    Device,
    MagicLinkResponse,
    MagicLinkStatusResponse,
    PhoneVerificationResponse,
    SmsCodeResponse,
    Tracker,
    TrackerUser,
)

API_HOST = "itsmybike.cloud"
AUTH_HOST = "user.iot-pet-tracking.cloud"
API_BASE_URL = f"https://{API_HOST}/api/pet_tracker/v2"
AUTH_BASE_URL = f"https://{AUTH_HOST}/api/app/v1"
SHOP_API_BASE_URL = "https://api.os.fressnapf.com"
SHOP_SITE = "FressnapfDE"

# Static credentials used by the Fressnapf app
CLOUD_AUTH_TOKEN = "FgvX_UJ7!BQRLU((1WhwFoOp"  # noqa: S105
SHOP_CLIENT_ID = "fn_tracker"
SHOP_CLIENT_SECRET = "LSfQlevg3uMAyU"  # noqa: S105

LIB_VERSION = metadata.version(__package__ or "fressnapftracker")

_TRACKER_APP_VERSION = "2.9.5_2"
_TRACKER_PLATFORM_VERSION = 34
_TRACKER_PHONE_NAME = f"fressnapftracker {LIB_VERSION}"

log = logging.getLogger(__name__)


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
        params: Mapping[str, str | int] | None = None,
        json_data: dict[str, Any] | None = None,
        data: Mapping[str, str] | None = None,
    ) -> Any:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method.
            url: Full URL to request.
            headers: Request headers.
            params: Optional query parameters.
            json_data: Optional JSON body data.
            data: Optional form-encoded body data.

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
                    data=data,
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

        result = response.json()
        log.debug("Response from %s: [%s] - %s", url, response.status_code, result)

        return result

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

    def _get_json_headers(self, authorization: str) -> dict[str, str]:
        """Get JSON request headers with the provided authorization value."""
        return {
            "accept": "application/json",
            "accept-encoding": "gzip",
            "Connection": "keep-alive",
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
            "Authorization": authorization,
        }

    def _get_auth_headers(self) -> dict[str, str]:
        """Get headers for legacy phone authentication requests."""
        return self._get_json_headers(f"Bearer {CLOUD_AUTH_TOKEN}")

    def _get_cloud_auth_headers(self) -> dict[str, str]:
        """Get headers authenticated with the static tracker cloud token."""
        return self._get_json_headers(f"Token token={CLOUD_AUTH_TOKEN}")

    @staticmethod
    def _build_additional_parameters(customer_id: str) -> dict[str, Any]:
        """Build the Fressnapf-specific user settings sent during authentication."""
        return AdditionalParameters(
            accepted_privacy_policy=True,
            region="DE",
            fressnapf_id=customer_id,
            accepted_newsletter=False,
            online_shop_rating_has_been_showed=False,
            online_shop_rating_popup_last_showed_date=None,
        ).model_dump(by_alias=True)

    @staticmethod
    def _raise_email_authentication_error(result: Any) -> None:
        """Raise an authentication error for a recognized email-auth error response."""
        if not isinstance(result, dict) or "error" not in result:
            return

        error = result.get("error_description") or result["error"]
        raise FressnapfTrackerAuthenticationError(str(error))

    async def _get_shop_access_token(self, email: str, password: str) -> str:
        """Authenticate with the Fressnapf shop and return its access token."""
        url = f"{SHOP_API_BASE_URL}/authorizationserver/oauth/token"
        headers = {
            "accept": "application/json",
            "User-Agent": self.user_agent,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        }
        data = {
            "grant_type": "password",
            "username": email,
            "password": password,
            "client_id": SHOP_CLIENT_ID,
            "client_secret": SHOP_CLIENT_SECRET,
        }

        result = await self._request("POST", url, headers, data=data)
        self._raise_email_authentication_error(result)

        access_token = result.get("access_token") if isinstance(result, dict) else None
        if not isinstance(access_token, str):
            raise FressnapfTrackerAuthenticationError("Fressnapf shop response did not contain an access token")
        return access_token

    async def _get_customer_id(self, email: str, shop_access_token: str) -> str:
        """Get the Fressnapf customer ID associated with an email address."""
        encoded_email = quote(email, safe="")
        url = f"{SHOP_API_BASE_URL}/rest/v2/{SHOP_SITE}/users/{encoded_email}"
        headers = self._get_json_headers(f"Bearer {shop_access_token}")

        result = await self._request("GET", url, headers)
        self._raise_email_authentication_error(result)

        customer_id = result.get("customerId") if isinstance(result, dict) else None
        if not isinstance(customer_id, str):
            raise FressnapfTrackerAuthenticationError("Fressnapf shop response did not contain a customer ID")
        return customer_id

    async def request_magic_link(self, email: str, password: str, locale: str = "en") -> MagicLinkResponse:
        """Request an email magic link for Fressnapf Tracker authentication.

        Args:
            email: Fressnapf account email address.
            password: Fressnapf account password.
            locale: Locale used for the magic-link email (default: "en").

        Returns:
            Magic-link response containing the tracker user and access token.

        """
        shop_access_token = await self._get_shop_access_token(email, password)
        customer_id = await self._get_customer_id(email, shop_access_token)
        body = {
            "user": {
                "email": email,
                "locale": locale,
                "tracker_service": "fressnapf",
                "user_token": {
                    "push_token": "",
                    "app_version": _TRACKER_APP_VERSION,
                    "app_platform": "android",
                    "platform_version": _TRACKER_PLATFORM_VERSION,
                    "phone_name": _TRACKER_PHONE_NAME,
                },
                "additional_parameters": self._build_additional_parameters(customer_id),
            }
        }

        result = await self._request(
            "POST",
            f"{AUTH_BASE_URL}/magic_link_auth",
            self._get_cloud_auth_headers(),
            json_data=body,
        )
        self._raise_email_authentication_error(result)
        try:
            return MagicLinkResponse.model_validate({**result, "customer_id": customer_id})
        except (TypeError, ValidationError) as exception:
            raise FressnapfTrackerAuthenticationError("Failed to parse magic-link response") from exception

    async def check_magic_link_was_clicked(self, user_access_token: str) -> bool:
        """Check once whether the requested email magic link has been opened.

        Args:
            user_access_token: Access token returned by request_magic_link.

        Returns:
            True when the magic link has been opened, otherwise False.

        """
        headers = self._get_json_headers(f'Token token="{user_access_token}"')
        result = await self._request(
            "GET",
            f"{AUTH_BASE_URL}/magic_link_auth",
            headers,
        )
        self._raise_email_authentication_error(result)
        try:
            return MagicLinkStatusResponse.model_validate(result).user_token.token_valid
        except ValidationError as exception:
            raise FressnapfTrackerAuthenticationError("Failed to parse magic-link status response") from exception

    async def complete_magic_link(
        self,
        user_id: int,
        user_access_token: str,
        customer_id: str,
    ) -> TrackerUser:
        """Complete email authentication after the magic link has been opened.

        Args:
            user_id: User ID returned by request_magic_link.
            user_access_token: Access token returned by request_magic_link.
            customer_id: Fressnapf customer ID returned by request_magic_link.

        Returns:
            Updated Fressnapf Tracker user.

        """
        params: dict[str, str | int] = {
            "user_id": user_id,
            "user_access_token": user_access_token,
        }
        body = {
            "user": {
                "additional_parameters": self._build_additional_parameters(customer_id),
                "notification_enabled": False,
            }
        }
        result = await self._request(
            "PATCH",
            f"{AUTH_BASE_URL}/users/update",
            self._get_cloud_auth_headers(),
            params=params,
            json_data=body,
        )
        self._raise_email_authentication_error(result)
        try:
            return TrackerUser.model_validate(result)
        except ValidationError as exception:
            raise FressnapfTrackerAuthenticationError("Failed to parse updated user response") from exception

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

    async def verify_phone_number(self, user_id: int, sms_code: str) -> PhoneVerificationResponse:
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
        headers = self._get_cloud_auth_headers()
        params: dict[str, str | int] = {
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
        try:
            return Tracker.model_validate(result)
        except ValidationError as exception:
            raise FressnapfTrackerInvalidTrackerResponseError("Failed to parse tracker data") from exception

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
