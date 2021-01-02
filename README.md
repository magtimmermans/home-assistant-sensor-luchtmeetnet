## Home Assistant sensor component for Air Quality in the Netherlands (based on Luchtmeetnet data)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

If you like my work, please buy me a coffee. This will keep me awake :)

<a href="https://www.buymeacoffee.com/mtimmermans" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png"></a>



#### Provides Home Assistant sensors for the Luchtkwaliteits Index van luchtmeetnet.


### Install:
- Copy the files in the /custom_components/luchtmeetnet/ folder to: [homeassistant]/config/custom_components/luchtmeetnet/


Example config:

```Configuration.yaml:
sensor:
  - platform: luchtmeetnet
    name: 'LuchtMeetNet'
    latitude: 51.7
    longitude: 5.5
```

