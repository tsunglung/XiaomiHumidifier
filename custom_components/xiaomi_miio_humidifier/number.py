"""Support for Xiaomi Smart Humidifier/Dehumidifier number entities."""
import logging
from datetime import timedelta
from functools import partial

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import device_registry as dr
from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_TOKEN
)
from miio import DeviceException

from .const import (
    CONF_MODEL,
    DATA_KEY,
    DOMAIN,
    HUMIDIFIER_NUMBERS_DELAY,
    MODELS_DELAY,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigType, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Smart Humidifier/Dehumidifier number entities."""

    host = entry.options[CONF_HOST]
    model = entry.options[CONF_MODEL]
    name = entry.title
    unique_id = entry.unique_id

    humidifier = hass.data[DOMAIN][host]

    entities = []
    if model in MODELS_DELAY:
        for description in HUMIDIFIER_NUMBERS_DELAY:
            entities.append(
                XiaomiHumidifierNumber(entry.options, description, name, unique_id, humidifier)
            )

    async_add_entities(entities)


class XiaomiHumidifierNumber(NumberEntity):
    """Implementation of a Xiaomi Smart Humidifier/Dehumidifier number entity."""
    entity_description: NumberEntityDescription

    def __init__(self, entry_data, description, name, unique_id, humidifier):
        self.entity_description = description
        self._name = name
        self._model = entry_data[CONF_MODEL]
        self._unique_id = unique_id
        self._attr = description.key
        self._mac = entry_data[CONF_TOKEN]
        self._host = entry_data[CONF_HOST]
        self._humidifier = humidifier
        self._available = True
        self._skip_update = False
        self._state = None

    @property
    def name(self):
        """Return the name of the entity."""
        return "{} {}".format(self._name, self.entity_description.name)

    @property
    def unique_id(self):
        """Return the unique id of the entity."""
        return "{}_{}".format(self._unique_id, self.entity_description.key)

    @property
    def available(self) -> bool:
        """Return true when the device is reachable."""
        return self._available

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
    def native_value(self):
        """Return the current value."""
        return self._state

    async def async_set_native_value(self, value: float) -> None:
        """Set a new value on the device."""
        try:
            result = await self.hass.async_add_executor_job(
                partial(self._humidifier.set_value, self._attr, int(value))
            )
            _LOGGER.debug("Response received from humidifier: %s", result)
        except DeviceException as exc:
            _LOGGER.error("Setting %s failed: %s", self._attr, exc)
            return

        if result and result[0].get("code", -1) == 0:
            self._state = int(value)
            self._skip_update = True
            self.async_write_ha_state()
        else:
            _LOGGER.error("Setting %s to %s was rejected: %s", self._attr, value, result)

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            if getattr(self.hass.data[DATA_KEY][self._host], "status", None):
                state = self.hass.data[DATA_KEY][self._host].status
            else:
                state = await self.hass.async_add_executor_job(self._humidifier.status)

            self._available = True
            self._state = getattr(state, self._attr, None)

        except DeviceException as ex:
            if self._available:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)
