"""Fressnapf Tracker API models."""

from pydantic import BaseModel, Field


class Position(BaseModel):
    """Position data from the tracker."""

    lat: float
    lng: float
    accuracy: int
    timestamp: str | None = None


class TrackerFeatures(BaseModel):
    """Features supported by the tracker."""

    flash_light: bool = False
    sleep_mode: bool = False
    live_tracking: bool = False


class TrackerSettings(BaseModel):
    """Settings for the tracker."""

    generation: str = "1.0"
    features: TrackerFeatures = Field(default_factory=TrackerFeatures)


class LedBrightness(BaseModel):
    """LED brightness settings."""

    value: int
    status: str | None = None


class DeepSleep(BaseModel):
    """Deep sleep settings."""

    value: bool
    status: str | None = None


class Tracker(BaseModel):
    """Complete tracker data from the API."""

    name: str
    battery: int
    charging: bool = False
    position: Position | None = None
    tracker_settings: TrackerSettings = Field(default_factory=TrackerSettings)
    led_brightness: LedBrightness | None = None
    deep_sleep: DeepSleep | None = None
    led_activatable: dict | None = None

    # Flattened convenience properties
    @property
    def led_brightness_value(self) -> int | None:
        """Get LED brightness value."""
        if self.led_brightness:
            return self.led_brightness.value
        return None

    @property
    def led_activatable_overall(self) -> bool:
        """Get whether LED is activatable overall."""
        if self.led_activatable:
            return bool(self.led_activatable.get("overall", False))
        return False

    @property
    def deep_sleep_value(self) -> bool | None:
        """Get deep sleep value."""
        if self.deep_sleep:
            return self.deep_sleep.value
        return None

    @property
    def supports_flash_light(self) -> bool:
        """Check if tracker supports flash light."""
        return self.tracker_settings.features.flash_light

    @property
    def supports_sleep_mode(self) -> bool:
        """Check if tracker supports sleep mode."""
        return self.tracker_settings.features.sleep_mode

    @property
    def supports_live_tracking(self) -> bool:
        """Check if tracker supports live tracking."""
        return self.tracker_settings.features.live_tracking


class Device(BaseModel):
    """Device information from the devices list."""

    serialnumber: str
    token: str


class UserToken(BaseModel):
    """User token information."""

    access_token: str
    refresh_token: str | None = None


class PhoneVerificationResponse(BaseModel):
    """Response from phone number verification."""

    user_token: UserToken


class SmsCodeResponse(BaseModel):
    """Response from SMS code request."""

    id: int
