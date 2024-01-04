"""Humidifier of the Xiaomi Smart Humidifier/Dehumidifier component."""
# pylint: disable=import-error
import logging
from datetime import timedelta
from functools import partial

from miio import DeviceException
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

SCAN_INTERVAL = timedelta(seconds=60)

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
    entities = []

    host = config_entry.options[CONF_HOST]
    token = config_entry.options[CONF_TOKEN]
    name = config_entry.title
    model = config_entry.options[CONF_MODEL]
    unique_id = config_entry.unique_id

    if config_entry.options[CONF_FLOW_TYPE] == CONF_DEVICE:
        if DATA_KEY not in hass.data:
            hass.data[DATA_KEY] = {}

        humidifier = hass.data[DOMAIN][host]
        if model in MODELS_MIOT:
            device = XiaomiHumidifierMiot(name, humidifier, model, unique_id, config_entry.options)
            entities.append(device)
            hass.data[DATA_KEY][host] = device
        else:
            _LOGGER.error(
                "Unsupported device found! Please create an issue at "
                "https://github.com/tsunglung/XiaomiHumidifier/issues "
                "and provide the following data: %s",
                model,
            )
            return


    async_add_entities(entities, update_before_add=False)


class XiaomiGenericHumidifier(HumidifierEntity):
    """Representation of a Xiaomi Humidifier Generic Entity."""

    def __init__(self, name, humidifier, model, unique_id):
        """Initialize the humidifier."""
        self._name = name
        self._humidifier = humidifier
        self._model = model
        self._unique_id = unique_id
        self._mac = None

        self._icon = "mdi:air-humidifier"
        self._available = False
        self._state = None
        self._status = None
        self._state_attrs = {ATTR_TEMPERATURE: None, ATTR_MODEL: self._model}
        self._device_features = FEATURE_FLAGS_GENERIC
        self._skip_update = False
        self._attr_mode = None

    @property
    def unique_id(self):
        """Return an unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use for device if any."""
        return self._icon

    @property
    def available(self):
        """Return true when state is known."""
        return self._available

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes of the device."""
        return self._state_attrs

    @property
    def is_on(self):
        """Return true if humidifier is on."""
        return self._state

    @property
    def device_info(self):
        """Return the device info."""
        info = self._humidifier.info()
        device_info = {
            "identifiers": {(DOMAIN, self._unique_id)},
            "manufacturer": (self._model or "Xiaomi").split(".", 1)[0].capitalize(),
            "name": self._name,
            "model": self._model,
            "sw_version": info.firmware_version,
            "hw_version": info.hardware_version
        }

        if self._mac is not None:
            device_info["connections"] = {(dr.CONNECTION_NETWORK_MAC, self._mac)}

        return device_info

    @property
    def status(self):
        """ Return the device status """
        return self._status

    async def _try_command(self, mask_error, func, *args, **kwargs):
        """Call a humidifier command handling error messages."""
        try:
            result = await self.hass.async_add_executor_job(
                partial(func, *args, **kwargs)
            )

            _LOGGER.debug("Response received from humidifier: %s", result)

            return result == SUCCESS
        except DeviceException as exc:
            if self._available:
                _LOGGER.error(mask_error, exc)
                self._available = False

            return False

    async def async_turn_on(self, **kwargs):
        """Turn the humidifier on."""
        result = await self._try_command("Turning the humidifier on failed.", self._humidifier.on)

        if result:
            self._state = True
            self._skip_update = True

    async def async_turn_off(self, **kwargs):
        """Turn the humidifier off."""
        result = await self._try_command("Turning the humidifier off failed.", self._humidifier.off)

        if result:
            self._state = False
            self._skip_update = True

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._humidifier.status)
            _LOGGER.debug("Got new state: %s", state)
            self._status = state

            self._available = True
            self._state = state.is_on
            self._state_attrs[ATTR_TEMPERATURE] = state.temperature

        except DeviceException as ex:
            if self._available:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)

    async def async_set_wifi_led_on(self):
        """Turn the wifi led on."""
        if self._device_features & FEATURE_SET_WIFI_LED == 0:
            return

        await self._try_command(
            "Turning the wifi led on failed.", self._humidifier.set_wifi_led, True
        )

    async def async_set_wifi_led_off(self):
        """Turn the wifi led on."""
        if self._device_features & FEATURE_SET_WIFI_LED == 0:
            return

        await self._try_command(
            "Turning the wifi led off failed.", self._humidifier.set_wifi_led, False
        )

    async def async_set_humidity(self, humidity: int) -> None:
        """Set new target humidity."""

        await self._try_command(
            "Setting the power mode of the humidifier failed.",
            self._humidifier.set_humidity,
            humidity,
        )


class XiaomiHumidifierMiot(XiaomiGenericHumidifier):
    """Representation of a Xiaomi Smart Humidifier/Dehumidifier Miot"""

    def __init__(self, name, humidifier, model, unique_id, config):
        """Initialize the humidifier."""
        super().__init__(name, humidifier, model, unique_id)
        self._mac = config.get(CONF_MAC, config.get(CONF_TOKEN))
        self._host = config[CONF_HOST]
        self._status = None

        if self._model in MODELS_MIOT:
            self._device_features = FEATURE_FLAGS_HUMIDIFIER_V1
            self._attr_available_modes = [mode.name for mode in PowerMode_V1]
            self._attr_min_humidity = TARGET_HUMIDITY_MIN_V1
            self._attr_max_humidity = TARGET_HUMIDITY_MAX_V1
        else:
            self._device_features = 0

        if self._device_features & FEATURE_SET_POWER_MODE == 1:
            self._state_attrs[ATTR_POWER_MODE] = None
            self._attr_supported_features = HumidifierEntityFeature.MODES

        if self._device_features & FEATURE_SET_WIFI_LED == 1:
            self._state_attrs[ATTR_WIFI_LED] = None

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._humidifier.status)
            self._status = state
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._state = state.is_on
            self._state_attrs.update(
                {ATTR_TEMPERATURE: state.temperature}
            )

            if self._device_features & FEATURE_SET_POWER_MODE == 1 and state.mode:
                self._state_attrs[ATTR_POWER_MODE] = state.mode
                self._attr_mode = state.mode

            if self._device_features & FEATURE_SET_WIFI_LED == 1 and state.wifi_led:
                self._state_attrs[ATTR_WIFI_LED] = state.wifi_led

            self._attr_target_humidity = state.target_humidity

        except DeviceException as ex:
            if self._available:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)

    async def async_set_mode(self, mode: str) -> None:
        """Set new mode."""
        if self._device_features & FEATURE_SET_POWER_MODE == 0:
            return

        await self._try_command(
            "Setting the power mode of the humidifier failed.",
            self._humidifier.set_power_mode,
            PowerMode_V1[mode].value,
        )

    async def async_set_buzzer(self, mode: bool) -> None:
        """Set new mode."""
        if self._device_features & FEATURE_SET_BUZZER == 0:
            return

        await self._try_command(
            "Setting the buzzer of the humidifier failed.",
            self._humidifier.set_buzzer,
            mode,
        )
