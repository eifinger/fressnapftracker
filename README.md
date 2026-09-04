# fressnapftracker

Asynchronous Python client for the Fressnapf Tracker GPS API

[![GitHub Actions](https://github.com/eifinger/fressnapftracker/workflows/CI/badge.svg)](https://github.com/eifinger/fressnapftracker/actions?workflow=CI)
[![PyPi](https://img.shields.io/pypi/v/fressnapftracker.svg)](https://pypi.python.org/pypi/fressnapftracker)
[![License](https://img.shields.io/pypi/l/fressnapftracker.svg)](https://github.com/eifinger/fressnapftracker/blob/main/LICENSE)

## Installation

```bash
uv add fressnapftracker
```

## Usage

### Email Authentication Flow

Use your Fressnapf account credentials to request a sign-in link by email:

```python
import asyncio

from fressnapftracker import AuthClient


async def main() -> None:
    """Show the email authentication flow."""
    async with AuthClient() as auth:
        # Step 1: Request the email sign-in link
        response = await auth.request_magic_link("<EMAIL>", "<PASSWORD>")
        user_id = response.user.id
        access_token = response.user_token.access_token
        customer_id = response.customer_id

        # Step 2: Open the link in the email, then check its status
        input("Open the sign-in link, then press Enter: ")
        if not await auth.check_magic_link_was_clicked(access_token):
            raise RuntimeError("The sign-in link has not been opened")

        # Step 3: Complete authentication and get the tracker devices
        await auth.complete_magic_link(user_id, access_token, customer_id)
        devices = await auth.get_devices(user_id, access_token)
        for device in devices:
            print(f"Device: {device.serialnumber} - Token: {device.token}")


if __name__ == "__main__":
    asyncio.run(main())
```

`check_magic_link_was_clicked()` performs one status request. Applications that poll should choose an appropriate interval and timeout.

### Legacy SMS Authentication Flow

Phone-number authentication remains available for existing accounts:

```python
async with AuthClient() as auth:
    sms_response = await auth.request_sms_code("+49123456789")
    sms_code = input("Enter SMS code: ")
    response = await auth.verify_phone_number(sms_response.id, sms_code)
    devices = await auth.get_devices(sms_response.id, response.user_token.access_token)
```

### Getting Tracker Data

```python
import asyncio

from fressnapftracker import ApiClient


async def main() -> None:
    """Show example of getting tracker data."""
    async with ApiClient(
        serial_number="<YOUR_SERIAL_NUMBER>",
        device_token="<YOUR_DEVICE_TOKEN>",
    ) as api:
        tracker = await api.get_tracker()
        print(f"Pet name: {tracker.name}")
        print(f"Battery: {tracker.battery}%")
        if tracker.position:
            print(f"Location: {tracker.position.lat}, {tracker.position.lng}")


if __name__ == "__main__":
    asyncio.run(main())
```

### Controlling the Tracker

```python
import asyncio

from fressnapftracker import ApiClient


async def main() -> None:
    """Show example of controlling the tracker."""
    async with ApiClient(
        serial_number="<YOUR_SERIAL_NUMBER>",
        device_token="<YOUR_DEVICE_TOKEN>",
    ) as api:
        # Set LED brightness (0-100)
        await api.set_led_brightness(75)

        # Enable/disable deep sleep mode
        await api.set_deep_sleep(True)


if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

### AuthClient

Client for handling authentication with the Fressnapf Tracker API.

#### Constructor Parameters

- `request_timeout` (int, optional): Request timeout in seconds (default: 10)
- `client` (httpx.AsyncClient, optional): Custom httpx client to use
- `user_agent` (str, optional): Custom user agent string

#### Methods

- `request_magic_link(email: str, password: str, locale: str = "en")` -> `MagicLinkResponse`: Request an email sign-in link
- `check_magic_link_was_clicked(user_access_token: str)` -> `bool`: Check once whether the email sign-in link has been opened
- `complete_magic_link(user_id: int, user_access_token: str, customer_id: str)` -> `TrackerUser`: Complete email authentication
- `request_sms_code(phone_number: str, locale: str = "en")` -> `SmsCodeResponse`: Request an SMS verification code
- `verify_phone_number(user_id: int, sms_code: str)` -> `PhoneVerificationResponse`: Verify a phone number with its SMS code
- `get_devices(user_id: int, user_access_token: str)` -> `list[Device]`: Get the authenticated user's devices

### ApiClient

Client for interacting with the Fressnapf Tracker device API.

#### Constructor Parameters

- `serial_number` (str): The serial number of your tracker device (required)
- `device_token` (str): The device token for API authentication (required)
- `request_timeout` (int, optional): Request timeout in seconds (default: 10)
- `client` (httpx.AsyncClient, optional): Custom httpx client to use
- `user_agent` (str, optional): Custom user agent string

#### Methods

- `get_tracker()` -> `Tracker`: Get current tracker data
- `set_led_brightness(brightness: int)`: Set LED brightness (0-100)
- `set_deep_sleep(enabled: bool)`: Enable/disable deep sleep mode

### Models

#### Tracker

- `name`: Pet/device name
- `battery`: Battery percentage
- `charging`: Whether the device is charging
- `position`: Position data (lat, lng, accuracy)
- `tracker_settings`: Device settings and features
- `led_brightness`: LED brightness settings
- `deep_sleep`: Deep sleep settings

#### MagicLinkResponse

- `user`: Tracker user ID and Fressnapf account email address
- `user_token`: Access token and current magic-link confirmation status
- `customer_id`: Fressnapf customer ID needed to complete authentication

#### TrackerUser

- `id`: Tracker user ID
- `email`: Fressnapf account email address
- `additional_parameters`: Fressnapf-specific account settings

#### Device

- `serialnumber`: Device serial number
- `token`: Device token for API calls

## Exceptions

- `FressnapfTrackerError`: Base exception
- `FressnapfTrackerConnectionError`: Connection/timeout errors
- `FressnapfTrackerAuthenticationError`: Authentication errors
- `FressnapfTrackerInvalidTokenError`: Invalid auth token
- `FressnapfTrackerInvalidDeviceTokenError`: Invalid device token
- `FressnapfTrackerInvalidSerialNumberError`: Invalid serial number
