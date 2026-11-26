"""Support for Xiaomi Smart Humidifier/Dehumidifier buttons."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import CONF_HOST

from .coordinator import XiaomiHumidifierEntity
from .const import (
    CONF_MODEL,
    DOMAIN,
    HUMIDIFIER_BUTTONS_V1,
    MODELS_MIOT
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigType, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Smart Humidifier/Dehumidifier buttons."""
    model = entry.options[CONF_MODEL]
    coordinator = hass.data[DOMAIN][entry.options[CONF_HOST]]

    if model not in MODELS_MIOT:
        return

    async_add_entities(
        XiaomiHumidifierButton(coordinator, description)
        for description in HUMIDIFIER_BUTTONS_V1
    )


class XiaomiHumidifierButton(XiaomiHumidifierEntity, ButtonEntity):
    """A button of a Xiaomi Smart Humidifier/Dehumidifier."""
    entity_description: ButtonEntityDescription

    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._key = description.key
        self._attr_unique_id = f"{coordinator.unique_id}_{description.key}"
        self._attr_name = f"{coordinator.device_name} {description.name}"

    @property
    def available(self) -> bool:
        """Buttons stay usable even if the last poll failed."""
        return True

    async def async_press(self) -> None:
        """Press the button."""
        if await self._coordinator.async_command(
            self._coordinator.device.call_action, self._key
        ):
            await self._coordinator.async_request_refresh()
