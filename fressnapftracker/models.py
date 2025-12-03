"""Fressnapf Tracker API models."""

from pydantic import BaseModel, Field


class Position(BaseModel):
    """Position data from the tracker."""

    lat: float
    lng: float
    accuracy: int
    timestamp: str | None = None
    created_at: str | None = None
    sampled_at: str | None = None


class TrackerFeatures(BaseModel):
    """Features supported by the tracker."""

    flash_light: bool = False
    sleep_mode: bool = False
    live_tracking: bool = False
    energy_saving_mode: bool = False


class TrackerSettings(BaseModel):
    """Settings for the tracker."""

    generation: str = "1.0"
    type: str | None = None
    features: TrackerFeatures = Field(default_factory=TrackerFeatures)
    sales_channel: str | None = None


class LedBrightness(BaseModel):
    """LED brightness settings."""

    value: int
    status: str | None = None


class DeepSleep(BaseModel):
    """Deep sleep settings."""

    value: int
    status: str | None = None


class EnergySaving(BaseModel):
    """Energy saving settings."""

    value: int
    status: str | None = None


class LedActivatable(BaseModel):
    """LED activatable status."""

    has_led: bool = False
    seen_recently: bool = False
    nonempty_battery: bool = False
    not_charging: bool = False
    overall: bool = False


class ServiceBooking(BaseModel):
    """Service booking information."""

    has_current_servicebooking: bool = False
    servicebooking_until: str | None = None
    days_until_servicebooking_ends: int | None = None


class Tracker(BaseModel):
    """Complete tracker data from the API."""

    name: str
    serialnumber: str | None = None
    additional_parameters: str | None = None
    icon: str | None = None
    last_position_accuracy: int | None = None
    last_position_timestamp: str | None = None
    last_seen_timestamp: str | None = None
    last_seen: str | None = None
    last_position: str | None = None
    battery: int
    charging: bool = False
    position: Position | None = None
    tracker_settings: TrackerSettings = Field(default_factory=TrackerSettings)
    led_brightness: LedBrightness | None = None
    deep_sleep: DeepSleep | None = None
    energy_saving: EnergySaving | None = None
    led_activatable: LedActivatable | None = None
    servicebooking: ServiceBooking | None = None
    inside_geofence: bool | None = None

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
            return self.led_activatable.overall
        return False

    @property
    def deep_sleep_value(self) -> int | None:
        """Get deep sleep value."""
        if self.deep_sleep:
            return self.deep_sleep.value
        return None

    @property
    def energy_saving_value(self) -> int | None:
        """Get energy saving value."""
        if self.energy_saving:
            return self.energy_saving.value
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

    @property
    def supports_energy_saving_mode(self) -> bool:
        """Check if tracker supports energy saving mode."""
        return self.tracker_settings.features.energy_saving_mode


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
