# hass-anthemav

This integration add the latest Anthem AV features to home assistant
It is a copy of the official Anthem AV integration but contains additional features under development/test or not yet merged in home assistant.

https://www.home-assistant.io/integrations/anthemav/

# Installation

* Download source code ([Code -> Download Zip](https://github.com/Hyralex/hass-anthemav/archive/refs/heads/master.zip)) 
* Copy the folder ./anthemav_custom to your home assistant installation under ./config/custom_components
* Make sure to remove any existing anthemav configuration (to avoid conflict)
* Restart Home Assistant
* Then add the integration via UI `Anthem A/V Receivers Custom` or click here

[![Add Integration to your Home Assistant instance.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=anthemav_custom)

# Additional features
List of additional features compare to Anthem AV integration
* Add integration via UI (Home Assistant PR merged. Release 2022.08: https://github.com/home-assistant/core/pull/53268)
* Add support for MRX-540, MRX-740 and MRX-1140 (Home Assistant PR merged. Release 2022.08: https://github.com/home-assistant/core/pull/53268)
* Add multi zone support (1 entity for each zone) (Home Assistant PR in progress: https://github.com/home-assistant/core/pull/74779)
* Add support for MDX-8, MDX-16 and Martin Logan equivalent MDA-8 and MDA-16 (Home Assistant PR in progress: https://github.com/home-assistant/core/pull/74779)
* Add step volume (volume up and down)
* Add audio listening mode

# Credits
This package was originally created by David McNett (https://github.com/nugget) as part of Home Assistant Anthem Av integration.

It has been taken over by Alex Henry (https://github.com/hyralex)


<a href="https://www.buymeacoffee.com/hyralex" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-red.png" alt="Buy Me A Drink" style="height: 40px !important;width: 170px !important;" ></a>
