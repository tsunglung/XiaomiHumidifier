"""Support for Xiaomi Smart Humidifier/Dehumidifier binary sensors."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import CONF_HOST

from .coordinator import XiaomiHumidifierEntity
from .const import (
    CONF_MODEL,
    DOMAIN,
    HUMIDIFIER_BINARY_SENSORS,
    MODELS_MIOT,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigType, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Smart Humidifier/Dehumidifier binary sensors."""
    model = entry.options[CONF_MODEL]
    coordinator = hass.data[DOMAIN][entry.options[CONF_HOST]]

    if model not in MODELS_MIOT:
        return

    async_add_entities(
        XiaomiHumidifierBinarySensor(coordinator, description)
        for description in HUMIDIFIER_BINARY_SENSORS
    )


class XiaomiHumidifierBinarySensor(XiaomiHumidifierEntity, BinarySensorEntity):
    """A binary sensor of a Xiaomi Smart Humidifier/Dehumidifier."""
    entity_description: BinarySensorEntityDescription

    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._key = description.key
        self._attr_unique_id = f"{coordinator.unique_id}_{description.key}"
        self._attr_name = f"{coordinator.device_name} {description.name}"

    @property
    def is_on(self):
        """Return true if the condition is active."""
        if self.status is None:
            return None
        return getattr(self.status, self._key, None)
