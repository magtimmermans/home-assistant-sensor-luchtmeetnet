"""Support for luchtmeetnet.nl weather service."""
import logging
import voluptuous as vol


from luchtmeetnet.luchtmeetnet import LuchtmeetNet

from datetime import timedelta
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorEntity,
    SensorEntityDescription,
    STATE_CLASS_MEASUREMENT
)
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    DEVICE_CLASS_AQI,
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

SENSOR_TYPES = tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="stationname",
        name="Air Quality Stationname",
    ),
    SensorEntityDescription(
        key="lki",
        name="Air Quality Index",
        device_class=DEVICE_CLASS_AQI,
        icon="mdi:gauge"
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    SensorEntityDescription(
        key="lki_text",
        name="Air Quality Status",
    ),
)

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
    await coordinator.async_config_entry_first_refresh()

    sensors = []
    sensors.extend(
        [
            LMNSensor(coordinator, description, config.get(CONF_NAME))
            for description in SENSOR_TYPES
        ]
    )

    async_add_entities(sensors, True)


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


class LMNSensor(CoordinatorEntity, SensorEntity):
    """Representation of an LuchtmeetNet sensor."""

    def __init__(self, coordinator, description, client_name):
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._attr_device_class = description.device_class
        self._attr_icon = description.icon
        self._attr_name = f"{client_name} {description.name}"
        self._attr_state_class = description.state_class
        self.description = description

    @callback
    def _async_process_data(self):
        """Update the entity."""
        self._attr_native_value = self.coordinator.data[self.device_class.key]

        self.async_write_ha_state()
        


