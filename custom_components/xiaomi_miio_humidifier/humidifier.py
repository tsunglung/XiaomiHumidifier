"""Humidifier of the Xiaomi Smart Humidifier/Dehumidifier component."""
# pylint: disable=import-error
import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.components.humidifier import (
    PLATFORM_SCHEMA,
    HumidifierEntity,
)
from homeassistant.components.humidifier.const import HumidifierEntityFeature
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import (
    CONF_DEVICE,
    CONF_HOST,
    CONF_TOKEN,
    CONF_MAC
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.util import slugify
from homeassistant.components.xiaomi_miio.const import (
    CONF_FLOW_TYPE
)
from .coordinator import XiaomiHumidifierEntity
from .humidifier_miot import PowerMode_V1

from .const import (
    ATTR_TEMPERATURE,
    ATTR_MODEL,
    ATTR_POWER_MODE,
    ATTR_WIFI_LED,
    CONF_MODEL,
    DATA_KEY,
    DOMAIN,
    MODELS_MIOT,
    MODELS_ALL_DEVICES
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): vol.All(cv.string, vol.Length(min=32, max=32)),
        vol.Optional(CONF_MODEL): vol.In(MODELS_ALL_DEVICES),
    }
)

SUCCESS = ["ok"]

FEATURE_SET_POWER_MODE = 1
FEATURE_SET_WIFI_LED = 2
FEATURE_SET_BUZZER = 4
FEATURE_SET_CHILDREN_LOCK = 8

FEATURE_FLAGS_GENERIC = 0

FEATURE_FLAGS_HUMIDIFIER_V1 = (
    FEATURE_SET_POWER_MODE | FEATURE_SET_WIFI_LED | FEATURE_SET_BUZZER | FEATURE_SET_CHILDREN_LOCK
)

FEATURE_FLAGS_GENERIC = 0

TARGET_HUMIDITY_MAX_V1 = 70
TARGET_HUMIDITY_MIN_V1 = 40

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Import Xiaomi Smart Humidifier/Dehumidifier configuration from YAML."""
    _LOGGER.warning(
        "Loading Xiaomi Smart Humidifier/Dehumidifier via platform setup is deprecated; Please remove it from your configuration"
    )
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config,
        )
    )


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the humidifier from a config entry."""
    model = config_entry.options[CONF_MODEL]

    if config_entry.options[CONF_FLOW_TYPE] != CONF_DEVICE:
        return

    if model not in MODELS_MIOT:
        _LOGGER.error(
            "Unsupported device found! Please create an issue at "
            "https://github.com/tsunglung/XiaomiHumidifier/issues "
            "and provide the following data: %s",
            model,
        )
        return

    coordinator = hass.data[DOMAIN][config_entry.options[CONF_HOST]]
    async_add_entities([XiaomiHumidifierMiot(coordinator)])


class XiaomiHumidifierMiot(XiaomiHumidifierEntity, HumidifierEntity):
    """Representation of a Xiaomi Smart Humidifier/Dehumidifier (MIoT)."""

    _attr_icon = "mdi:air-humidifier"
    _attr_available_modes = [mode.name for mode in PowerMode_V1]
    _attr_min_humidity = TARGET_HUMIDITY_MIN_V1
    _attr_max_humidity = TARGET_HUMIDITY_MAX_V1
    _attr_supported_features = HumidifierEntityFeature.MODES

    def __init__(self, coordinator):
        """Initialize the humidifier."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.unique_id
        self._attr_name = coordinator.device_name

    @property
    def is_on(self):
        """Return true if humidifier is on."""
        if self.status is None:
            return None
        return bool(self.status.data.get("status"))

    @property
    def mode(self):
        """Return the current mode."""
        if self.status is None:
            return None
        try:
            return self.status.mode
        except ValueError:
            return None

    @property
    def target_humidity(self):
        """Return the target humidity."""
        return None if self.status is None else self.status.data.get("target_humidity")

    @property
    def current_humidity(self):
        """Return the measured humidity."""
        return None if self.status is None else self.status.data.get("relative_humidity")

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes of the device."""
        attrs = {ATTR_MODEL: self._coordinator.model}
        if self.status is not None:
            attrs[ATTR_TEMPERATURE] = self.status.data.get("temperature")
            attrs[ATTR_POWER_MODE] = self.mode
        return attrs

    async def async_turn_on(self, **kwargs):
        """Turn the humidifier on."""
        await self._coordinator.async_command(
            self._coordinator.device.on, optimistic={"status": True}
        )

    async def async_turn_off(self, **kwargs):
        """Turn the humidifier off."""
        await self._coordinator.async_command(
            self._coordinator.device.off, optimistic={"status": False}
        )

    async def async_set_humidity(self, humidity: int) -> None:
        """Set new target humidity."""
        await self._coordinator.async_command(
            self._coordinator.device.set_humidity, humidity,
            optimistic={"target_humidity": humidity},
        )

    async def async_set_mode(self, mode: str) -> None:
        """Set new mode."""
        value = PowerMode_V1[mode].value
        await self._coordinator.async_command(
            self._coordinator.device.set_power_mode, value,
            optimistic={"mode": value},
        )
