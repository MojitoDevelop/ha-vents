# Migration from a Modbus YAML hub

1. Back up the existing configuration and dashboard.
2. Disable automations writing to hub `reku`. Remove only that hub's YAML configuration and restart HA. A21 permits one TCP client per interface.
3. Install Vents and configure the same host, port, and unit ID in the UI.
4. Replace dashboard references using the table below. Confirm actual entity IDs in **Settings → Devices & services → Vents**; HA adds suffixes if names are occupied.
5. Replace helper-to-Modbus automations with the native services below. Remove obsolete helpers after the dashboard and automations have been checked.

The integration does not rewrite dashboards, remove old entities, or adopt another integration's registry records automatically. Names can be translated, but the new IDs are always based on English keys.

| Previous entity | New entity |
| --- | --- |
| `sensor.temperatura_czerpnia` | `sensor.vents_outdoor_air_temperature` |
| `sensor.temperatura_nawiew` | `sensor.vents_supply_air_temperature` |
| `sensor.temperatura_wywiew` | `sensor.vents_extract_air_temperature` |
| `sensor.temperatura_wyrzutnia` | `sensor.vents_exhaust_air_temperature` |
| `sensor.speed_mode` | `sensor.vents_speed_mode` (raw mirror), `fan.vents_ventilation` (control) |
| `sensor.bypass_mode` | `sensor.vents_bypass_mode_raw` (raw mirror), `select.vents_bypass_mode` (control) |
| `sensor.nastawa_speed` | `sensor.vents_manual_speed_setpoint` |
| `sensor.nastawa_bypass` | `sensor.vents_bypass_setpoint` |
| `sensor.nastawa_temperatury` | `sensor.vents_temperature_setpoint` |
| `input_number.speed_nastawa` | `number.vents_manual_speed` |
| `input_number.bypass_nastawa` | `number.vents_bypass_position_setpoint` (analogue actuator only) |
| `input_number.temperatura_nastawa` | `number.vents_target_temperature` or `climate.vents_climate` |
| `climate.rekuperator` | `climate.vents_climate` |

| Previous action | Replacement action |
| --- | --- |
| Write Holding 2 = 1/2/3 | `fan.set_preset_mode`, preset `speed_1` / `speed_2` / `speed_3` |
| Write Holding 2 = 255 | `fan.set_preset_mode`, preset `manual` |
| Set manual speed and start | `fan.set_percentage`, `percentage: 50` |
| Change stored manual speed without starting | `number.set_value` on `number.vents_manual_speed` |
| Write Holding 74 = 2 | `select.select_option` on `select.vents_bypass_mode`, option `auto` |
| Write Holding 74 = 1 | Same select, option `manual` for analogue, `open` for discrete actuator |
| Write Holding 75 | `number.set_value` on `number.vents_bypass_position_setpoint` |
| Write Holding 44 | `climate.set_temperature`, `temperature: 23`, or `number.set_value` on `number.vents_target_temperature` |

The percentage numbers change stored setpoints without implicitly turning on the unit or changing the bypass mode. The fan service changes mode and starts the unit explicitly. Bypass protection remains under controller authority.

The climate uses the controller-selected sensor (Input 0); the old YAML used supply air (Input 2). Its temperature target is 15–30 °C, step 1, with no scaling on Holding 44. Current temperatures use signed tenths of a degree.

Do not run the previous `modbus.write_register` actions against `reku` after removing that hub. Existing history is retained under the previous entity IDs; moving history between IDs is a separate HA database/registry task.
