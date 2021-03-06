"""Support for luchtmeetnet.nl weather service."""
import logging
import voluptuous as vol


from luchtmeetnet.luchtmeetnet import LuchtmeetNet

from datetime import timedelta
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
)
import homeassistant.helpers.config_validation as cv

from luchtmeetnet.urls import json_station_lki_data

from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

DOMAIN = "luchtmeetnet"

_LOGGER = logging.getLogger(__name__)

# Supported sensor types:
# Key: ['label', unit, icon]
SENSOR_TYPES = {
    "stationname": ["Air Quality Stationname", None, None],
    "lki": ["Air Quality Index", None, "mdi:gauge"],
    "lki_text": ["Air Quality Status", None, None],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Inclusive(
            CONF_LATITUDE, "coordinates", "Latitude and longitude must exist together"
        ): cv.latitude,
        vol.Inclusive(
            CONF_LONGITUDE, "coordinates", "Latitude and longitude must exist together"
        ): cv.longitude,
        vol.Optional(CONF_NAME, default="LuchtmeetNet"): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Create the luchtmeetnet sensor."""
    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)

    if None in (latitude, longitude):
        _LOGGER.error("Latitude or longitude not set in Home Assistant config")
        return False

    coordinates = {CONF_LATITUDE: float(latitude), CONF_LONGITUDE: float(longitude)}

    _LOGGER.debug("Initializing luchtmeet sensor coordinate %s", coordinates)

    coordinator = LMNUpdateCoordinator(hass, coordinates)
    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    sensors = []
    for sensor_type in SENSOR_TYPES:
        sensors.append(LMNSensor(coordinator, sensor_type, config.get(CONF_NAME)))

    async_add_entities(sensors)


class LMNUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, coordinates):
        """Initialize."""

        self._lmn = LuchtmeetNet(coordinates["latitude"], coordinates["longitude"])
        self._station = None

        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=300)
        )

    async def _async_update_data(self):
        """Update data """
        if self._station is None:
            result = await self._lmn.get_nearest_station()
            if result is not None:
                self._station = result["number"]

        data = await self._lmn.get_station_measurement(self._station)
        lki = data["LKI"]
        quality = "Geen data beschikbaar"
        if lki <= 3:
            quality = "goed"
        elif lki <= 6:
            quality = "matig"
        elif lki <= 8:
            quality = "onvoldoende"
        elif lki <= 10:
            quality = "slecht"
        elif lki <= 11:
            quality = "zeer slecht"
        try:
            return {
                "stationname": self._station,
                "lki": lki,
                "lki_text": quality,
                "timestamp": data["timestamp"],
            }
        except Exception as err:
            raise UpdateFailed(err)


class LMNSensor(CoordinatorEntity):
    """Representation of an LuchtmeetNet sensor."""

    def __init__(self, coordinator, sensor_type, client_name):
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.client_name = client_name
        self._name = SENSOR_TYPES[sensor_type][0]
        self.type = sensor_type
        self._state = None
        self._unit_of_measurement = SENSOR_TYPES[self.type][1]

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self.client_name} {self._name}"

    @property
    def state(self):
        """Return the state of the device."""
        return self.coordinator.data[self.type]

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Return possible sensor specific icon."""
        return SENSOR_TYPES[self.type][2]
