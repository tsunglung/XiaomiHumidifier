# Xiaomi Smart Humidifier/Dehumidifier Integration for Home Assistant

![GitHub stars](https://img.shields.io/github/stars/tsunglung/XiaomiHumidifier)
![GitHub forks](https://img.shields.io/github/forks/tsunglung/XiaomiHumidifier)
![GitHub watchers](https://img.shields.io/github/watchers/tsunglung/XiaomiHumidifier)
<a href="https://www.buymeacoffee.com/tsunglung" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="30" width="120"></a>

This is a custom component for Home Assistant to integrate the Xiaomi Smart Humidifier/Dehumidifier.

Credits: Thanks to [Rytilahti](https://github.com/rytilahti/python-miio) for all the work.

## Supported devices

| Name                        | Model                  | Model no. |
| --------------------------- | ---------------------- | --------- |
| Xiaomi Smart Humidifier/Dehumidifier    | dmaker.derh.22ht       | |
| Xiaomi Smart Humidifier/Dehumidifier    | dmaker.derh.22l      | |

## Features

### Xiaomi Smart Dehumidifier

Supported models: `dmaker.derh.22ht`, `dmaker.derh.22l`

* Power (on, off)
* Mode (Smart, Sleep, Clothes Drying)
* Wifi LED (on, off)
* Physical Controls Lock (on, off)
* Buzzer (on, off)
* Dry After off switch (on, off)

## Install

You can install component with [HACS](https://hacs.xyz/) custom repo: HACS > Integrations > 3 dots (upper top corner) > Custom repositories > URL: `tsunglung/XiaomiHumidifier` > Category: Integration

Or manually copy `xiaomi_miio_humidifier` folder to `custom_components` folder in your config folder.

Then restart HA.

## Setup


1. With GUI. Configuration > Integration > Add Integration > Xiaomi Smart Humidifier/Dehumidifier
   1. If the integration didn't show up in the list please REFRESH the page
   2. If the integration is still not in the list, you need to clear the browser cache.
2. Enter your Xiaomi Account and Password
3. Select the Humidifier/Dehumidifier device that you want to integrate.

Or you also can manually input Humidifier/Dehumidifier IP address and token

Buy me a Coffee

|  LINE Pay | LINE Bank | JKao Pay |
| :------------: | :------------: | :------------: |
|![LINE Pay](linepay.jpg "LINE Pay")|![Line Bank](linebank.jpg "Line Bank") |![Jko Pay](jkopay.jpg "Jko Pay") |
