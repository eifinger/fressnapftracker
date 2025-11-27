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

### Authentication Flow

If you don't have credentials yet, you can use the authentication flow:

```python
import asyncio

from fressnapftracker import AuthClient


async def main() -> None:
    """Show example of authentication flow."""
    async with AuthClient() as auth:
        # Step 1: Request SMS code
        # Phone number should be in E.164 format (e.g., +49123456789)
        sms_response = await auth.request_sms_code("+49123456789")
        user_id = sms_response.id
        print(f"User ID: {user_id}")

        # Step 2: Verify with SMS code (you'll receive this via SMS)
        sms_code = input("Enter SMS code: ")
        verify_response = await auth.verify_phone_number(user_id, sms_code)
        access_token = verify_response.user_token.access_token
        print(f"Access token: {access_token}")

        # Step 3: Get list of devices
        devices = await auth.get_devices(user_id, access_token)
        for device in devices:
            print(f"Device: {device.serialnumber} - Token: {device.token}")


if __name__ == "__main__":
    asyncio.run(main())
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

- `request_sms_code(phone_number: str, locale: str = "en")` -> `SmsCodeResponse`: Request SMS verification code
- `verify_phone_number(user_id: int, sms_code: int)` -> `PhoneVerificationResponse`: Verify phone with code received via SMS
- `get_devices(user_id: int, user_access_token: str)` -> `list[Device]`: Get list of devices

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

#### Device

- `serialnumber`: Device serial number
- `name`: Device name
- `device_token`: Device token for API calls
- `auth_token`: Auth token for API calls

## Exceptions

- `FressnapfTrackerError`: Base exception
- `FressnapfTrackerConnectionError`: Connection/timeout errors
- `FressnapfTrackerAuthenticationError`: Authentication errors
- `FressnapfTrackerInvalidTokenError`: Invalid auth token
- `FressnapfTrackerInvalidDeviceTokenError`: Invalid device token
- `FressnapfTrackerInvalidSerialNumberError`: Invalid serial number
