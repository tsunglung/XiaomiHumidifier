"""Support for Xiaomi Smart Humidifier/Dehumidifier number entities."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.const import CONF_HOST

from .coordinator import XiaomiHumidifierEntity
from .const import (
    CONF_MODEL,
    DOMAIN,
    HUMIDIFIER_NUMBERS_DELAY,
    MODELS_DELAY,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigType, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Smart Humidifier/Dehumidifier number entities."""
    model = entry.options[CONF_MODEL]
    coordinator = hass.data[DOMAIN][entry.options[CONF_HOST]]

    if model not in MODELS_DELAY:
        return

    async_add_entities(
        XiaomiHumidifierNumber(coordinator, description)
        for description in HUMIDIFIER_NUMBERS_DELAY
    )


class XiaomiHumidifierNumber(XiaomiHumidifierEntity, NumberEntity):
    """A number entity of a Xiaomi Smart Humidifier/Dehumidifier."""
    entity_description: NumberEntityDescription

    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._key = description.key
        self._attr_unique_id = f"{coordinator.unique_id}_{description.key}"
        self._attr_name = f"{coordinator.device_name} {description.name}"

    @property
    def native_value(self):
        """Return the current value."""
        if self.status is None:
            return None
        return getattr(self.status, self._key, None)

    async def async_set_native_value(self, value: float) -> None:
        """Set a new value on the device."""
        await self._coordinator.async_command(
            self._coordinator.device.set_value, self._key, int(value),
            optimistic={self._key: int(value)},
        )
