"""The Xiaomi Smart Humidifier/Dehumidifier component."""
# pylint: disable=import-error
import logging

import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.exceptions import PlatformNotReady
from miio import (  # pylint: disable=import-error
    Device,
    DeviceException
)

from .humidifier_miot import HumidifierMiot

from .const import (
    CONF_MODEL,
    DATA_KEY,
    DOMAIN,
    DOMAINS,
    HUMIDIFIER_BUTTONS_V1,
    HUMIDIFIER_SENSORS,
    HUMIDIFIER_SWITCHS_V1,
    MODELS_MIOT
)

_LOGGER = logging.getLogger(__name__)


def _legacy_unique_id_map(entry: ConfigEntry) -> dict:
    """Map legacy entity unique_ids of this entry to the current format.

    Current format: "<entry.unique_id>_<key>" for sensor/switch/button.
    Legacy formats:
    - "<entry.title>_<key>" (before per-device unique_ids)
    - switch/button: "<entry.unique_id>_<key1>_..._<keyN>_<keyN>", built
      by a loop that kept appending the keys of previous descriptions.
    """
    base = entry.unique_id
    mapping = {}
    if not base:
        return mapping

    descriptions = {
        "sensor": HUMIDIFIER_SENSORS,
        "switch": HUMIDIFIER_SWITCHS_V1,
        "button": HUMIDIFIER_BUTTONS_V1,
    }
    for platform, descs in descriptions.items():
        chained = base.replace(" ", "_")
        for desc in descs:
            new_id = f"{base}_{desc.key}"
            if entry.title:
                mapping[(platform, f"{entry.title}_{desc.key}")] = new_id
            if platform in ("switch", "button"):
                chained = f"{chained}_{desc.key}"
                mapping[(platform, f"{chained}_{desc.key}")] = new_id
    return mapping


def _migrate_unique_ids(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Move registry entries with legacy unique_ids to the current format.

    Keeps entity_ids, names and settings. Skips an entry when an entity
    with the new unique_id already exists.
    """
    mapping = _legacy_unique_id_map(entry)
    if not mapping:
        return
    ent_reg = er.async_get(hass)

    @callback
    def _update(reg_entry: er.RegistryEntry):
        new_id = mapping.get((reg_entry.domain, reg_entry.unique_id))
        if new_id is None or new_id == reg_entry.unique_id:
            return None
        if ent_reg.async_get_entity_id(reg_entry.domain, DOMAIN, new_id):
            _LOGGER.warning(
                "Not migrating %s: unique_id %s already in use",
                reg_entry.entity_id, new_id,
            )
            return None
        _LOGGER.info(
            "Migrating %s unique_id %s -> %s",
            reg_entry.entity_id, reg_entry.unique_id, new_id,
        )
        return {"new_unique_id": new_id}

    er.async_migrate_entries(hass, entry.entry_id, _update)

    # The old switch/button code also registered its chained unique_ids as
    # device identifiers. Reduce the device to its real identifier.
    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get_device(identifiers={(DOMAIN, entry.unique_id)})
    if device is not None:
        own = {i for i in device.identifiers if i[0] == DOMAIN}
        if own != {(DOMAIN, entry.unique_id)}:
            other = {i for i in device.identifiers if i[0] != DOMAIN}
            dev_reg.async_update_device(
                device.id,
                new_identifiers=other | {(DOMAIN, entry.unique_id)},
            )

async def async_setup(hass: HomeAssistant, hass_config: dict):
    """Set up the Smart Humidifier/Dehumidifier Component."""

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    """ Update Optioins if available """
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """ check unload integration """
    return all([
        await hass.config_entries.async_forward_entry_unload(entry, domain)
        for domain in DOMAINS
    ])


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Support Xiaomi Smart Humidifier/Dehumidifier Component."""
    # pylint: disable=too-many-statements, too-many-locals
    # migrate data (also after first setup) to options
    if entry.data:
        hass.config_entries.async_update_entry(entry, data={},
                                               options=entry.data)

    # add update handler
    if not entry.update_listeners:
        entry.add_update_listener(async_update_options)

    if entry.data.get(CONF_HOST, None):
        host = entry.data[CONF_HOST]
        token = entry.data[CONF_TOKEN]
        model = entry.data.get(CONF_MODEL)
    else:
        host = entry.options[CONF_HOST]
        token = entry.options[CONF_TOKEN]
        model = entry.options.get(CONF_MODEL)

    if DATA_KEY not in hass.data:
        hass.data.setdefault(DATA_KEY, {})
        hass.data[DATA_KEY][host] = {}

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    unique_id = None

    if model is None:
        try:
            miio_device = Device(host, token)
            device_info = await hass.async_add_executor_job(miio_device.info)
            model = device_info.model
            unique_id = f"{model}-{device_info.mac_address}"
            _LOGGER.info(
                "%s %s %s detected",
                model,
                device_info.firmware_version,
                device_info.hardware_version,
            )
        except DeviceException as ex:
            raise PlatformNotReady from ex

    if model in MODELS_MIOT:
        humidifier = HumidifierMiot(host, token, model=model)
    else:
        _LOGGER.error(
            "Unsupported device found! Please create an issue at "
            "https://github.com/rytilahti/python-miio/issues "
            "and provide the following data: %s",
            model,
        )
        return False

    hass.data[DOMAIN][host] = humidifier

    _migrate_unique_ids(hass, entry)

    # init setup for each supported domains
    await hass.config_entries.async_forward_entry_setups(entry, DOMAINS)

    return True
