"""Support for Anthem Network Receivers and Processors."""
from __future__ import annotations

import logging
from typing import Any

from anthemav.connection import Connection
from anthemav.protocol import AVR

import voluptuous as vol

from homeassistant.components.media_player import (
    PLATFORM_SCHEMA,
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
)
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_NAME,
    CONF_PORT,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    ANTHEMAV_UDATE_SIGNAL,
    CONF_MODEL,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DOMAIN,
    MANUFACTURER,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up our socket to the AVR."""
    _LOGGER.warning(
        "AnthemAV configuration is deprecated and has been automatically imported. Please remove the integration from your configuration file"
    )
    await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=config,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entry."""
    name = config_entry.data[CONF_NAME]
    macaddress = config_entry.data[CONF_MAC]
    model = config_entry.data[CONF_MODEL]

    avr: Connection = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for zone in avr.protocol.zones:
        _LOGGER.debug("Initialize Zone %s", zone)
        device = AnthemAVR(avr.protocol, name, macaddress, model, zone)
        entities.append(device)

    async_add_entities(entities)

    _LOGGER.debug("dump_devicedata: %s", device.dump_avrdata)
    _LOGGER.debug("dump_conndata: %s", avr.dump_conndata)


class AnthemAVR(MediaPlayerEntity):
    """Entity reading values from Anthem AVR protocol."""

    _attr_should_poll = False
    _attr_supported_features = (
        MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    def __init__(
        self, avr: AVR, name: str, macaddress: str, model: str, zone_number: int
    ) -> None:
        """Initialize entity with transport."""
        super().__init__()
        self.avr = avr
        self._zone_number = zone_number
        self._zone = avr.zones[zone_number]
        self._device_name = name
        if zone_number > 1:
            self._attr_name = f"{name} Zone {zone_number}"
        else:
            self._attr_name = name

        self._attr_device_class = MediaPlayerDeviceClass.RECEIVER
        self._attr_unique_id = f"{macaddress}_{zone_number}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, macaddress)},
            name=name,
            manufacturer=MANUFACTURER,
            model=model,
        )

    def _lookup(self, propname: str, dval: Any | None = None) -> Any | None:
        return getattr(self.avr, propname, dval)

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{ANTHEMAV_UDATE_SIGNAL}_{self._device_name}",
                self.async_write_ha_state,
            )
        )

    @property
    def state(self) -> str | None:
        """Return state of power on/off."""
        pwrstate = self._zone.power

        if pwrstate is True:
            return STATE_ON
        if pwrstate is False:
            return STATE_OFF
        return None

    @property
    def is_volume_muted(self) -> bool | None:
        """Return boolean reflecting mute state on device."""
        return self._zone.mute

    @property
    def volume_level(self) -> float | None:
        """Return volume level from 0 to 1."""
        return self._zone.volume_as_percentage

    @property
    def media_title(self) -> str | None:
        """Return current input name (closest we have to media title)."""
        return self._zone.input_name

    @property
    def app_name(self) -> str | None:
        """Return details about current video and audio stream."""
        return f"{self.avr.video_input_resolution_text} {self.avr.audio_input_name}"

    @property
    def source(self) -> str | None:
        """Return currently selected input."""
        return self._zone.input_name

    @property
    def source_list(self) -> list[str] | None:
        """Return all active, configured inputs."""
        return self.avr.input_list

    async def async_select_source(self, source: str) -> None:
        """Change AVR to the designated source (by name)."""
        self._zone.input_name = source

    async def async_turn_off(self) -> None:
        """Turn AVR power off."""
        self._zone.power = False

    async def async_turn_on(self) -> None:
        """Turn AVR power on."""
        self._zone.power = True

    async def async_set_volume_level(self, volume: float) -> None:
        """Set AVR volume (0 to 1)."""
        self._zone.volume_as_percentage = volume

    async def async_mute_volume(self, mute: bool) -> None:
        """Engage AVR mute."""
        self._zone.mute = mute

    @property
    def dump_avrdata(self):
        """Return state of avr object for debugging forensics."""
        attrs = vars(self)
        items_string = ", ".join(f"{item}: {item}" for item in attrs.items())
        return f"dump_avrdata: {items_string}"
