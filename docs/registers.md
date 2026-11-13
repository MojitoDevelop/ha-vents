# Register coverage

Zero-based A21 addresses. FC1 coils, FC2 discrete inputs, FC3 holding registers, FC4 input registers; writes use FC5 and FC6.

Display labels follow the HA system language. The IDs below show the first unit with device name Vents; HA can append numeric suffixes.

## Sensors

| English entity ID | Register / conversion | Optional feature |
| --- | --- | --- |
| `sensor.vents_control_temperature` | Input 0; signed int16 × 0.1; 0x8000/0x7fff unavailable | — |
| `sensor.vents_outdoor_air_temperature` | Input 1; signed int16 × 0.1; 0x8000/0x7fff unavailable | — |
| `sensor.vents_supply_air_temperature` | Input 2; signed int16 × 0.1; 0x8000/0x7fff unavailable | — |
| `sensor.vents_extract_air_temperature` | Input 3; signed int16 × 0.1; 0x8000/0x7fff unavailable | — |
| `sensor.vents_exhaust_air_temperature` | Input 4; signed int16 × 0.1; 0x8000/0x7fff unavailable | — |
| `sensor.vents_manual_speed_setpoint` | Holding 17 | — |
| `sensor.vents_temperature_setpoint` | Holding 44 | — |
| `sensor.vents_bypass_setpoint` | Holding 75 | — |
| `sensor.vents_speed_mode` | Holding 2 | — |
| `sensor.vents_bypass_mode_raw` | Holding 74 | — |
| `sensor.vents_bypass_position` | Input 51 | — |
| `sensor.vents_supply_fan_output` | Input 52 | — |
| `sensor.vents_extract_fan_output` | Input 53 | — |
| `sensor.vents_heater_control_signal` | Input 44 | — |
| `sensor.vents_filter_status` | Input 31 | — |
| `sensor.vents_filter_time_remaining` | Input 27; packed time across two registers | — |
| `sensor.vents_operating_time` | Input 29; packed time across two registers | — |
| `sensor.vents_timer_time_remaining` | Input 25; packed time across two registers | — |
| `sensor.vents_alarm_status` | Input 38 | — |
| `sensor.vents_active_alarm` | Input 38; codes from Discrete Inputs 19–71 | — |
| `sensor.vents_internal_humidity` | Input 10 | humidity |
| `sensor.vents_external_humidity` | Input 11 | humidity |
| `sensor.vents_internal_co2` | Input 12 | co2 |
| `sensor.vents_external_co2` | Input 13 | co2 |
| `sensor.vents_internal_pm25` | Input 14 | pm25 |
| `sensor.vents_external_pm25` | Input 15 | pm25 |
| `sensor.vents_internal_voc` | Input 16 | voc |
| `sensor.vents_external_voc` | Input 17 | voc |
| `sensor.vents_supply_airflow` | Input 19 | airflow |
| `sensor.vents_extract_airflow` | Input 20 | airflow |
| `sensor.vents_supply_pressure` | Input 21 | pressure |
| `sensor.vents_extract_pressure` | Input 22 | pressure |
| `sensor.vents_supply_fan_speed` | Input 23 | rpm |
| `sensor.vents_extract_fan_speed` | Input 24 | rpm |
| `sensor.vents_external_temperature` | Input 5; signed int16 × 0.1; 0x8000/0x7fff unavailable | extra_temperature |
| `sensor.vents_after_preheater_temperature` | Input 6; signed int16 × 0.1; 0x8000/0x7fff unavailable | extra_temperature |
| `sensor.vents_before_reheater_temperature` | Input 7; signed int16 × 0.1; 0x8000/0x7fff unavailable | extra_temperature |

## Numbers

| English entity ID | Holding register | Accepted values |
| --- | --- | --- |
| `number.vents_manual_speed` | 17 | 0–100 % |
| `number.vents_bypass_position_setpoint` | 75 | 0–100 % |
| `number.vents_target_temperature` | 44 | 15–30 °C |
| `number.vents_timer_duration` | 51 | 1–1439 min |
| `number.vents_timer_temperature` | 50 | 0–30 °C |
| `number.vents_filter_timer_period` | 58 | 0–365 d |
| `number.vents_humidity_setpoint` | 45 | 40–80 % |
| `number.vents_co2_setpoint` | 46 | 400–2000 ppm |
| `number.vents_pm25_setpoint` | 47 | 100–1000 µg/m³ |
| `number.vents_voc_setpoint` | 48 | 20–100 % |

Manual speed bounds come from HR3/4. Filter period accepts 0 or 70–365 days; timer temperature accepts 0 or 15–30 °C. Timer duration is shown in total minutes and stored as hours in the low byte, minutes in the high byte of HR51. Timer countdown IR25 stores minutes in the low byte and seconds in the high byte, IR26 stores hours in the high byte. IR27/29 store hours in the low byte and minutes in the high byte, followed by days in the next register. Validate packed fields against the controller during physical commissioning.

Advanced speed settings: HR7–16 for percentage output and HR27–36 for airflow, supply/extract pairs for speeds 1–5. Only speeds allowed by HR1 are created. These entities are disabled by default; the relevant HR0 ventilation mode must match. Airflow limits come from HR23/24.

## Other platforms

| Entity / function | Registers |
| --- | --- |
| `fan.vents_ventilation` | Coil 0 power; HR2 preset (1–5, 255 manual), HR17 manual percent |
| `climate.vents_climate` | Input 0 current temperature ×0.1; HR44 target 15–30 whole °C; HR43 mode 0 ventilation / 1 heat / 2 cool / 3 auto; Coil 0 power |
| `select.vents_bypass_mode` | HR74: 0 closed, 1 open/manual, 2 auto; HR57 actuator capability |
| `select.vents_timer_speed` | HR49: 0 standby, 1–5 speed |
| `switch.vents_timer` | Coil 1 |
| `switch.vents_weekly_schedule` | Coil 2 |
| `button.vents_reset_filter_timer` | Coil 17, write true |
| `button.vents_reset_alarms` | Coil 18, write true |
| `binary_sensor.vents_boost_active` | Coil 3, read only |
| `binary_sensor.vents_fireplace_active` | Coil 4, read only |
| `binary_sensor.vents_heater_active` | Discrete Input 7 |
| `binary_sensor.vents_heater_cooldown` | Discrete Input 9 |
| `binary_sensor.vents_supply_filter_clogged` | Discrete Input 12 |
| `binary_sensor.vents_extract_filter_clogged` | Discrete Input 13 |
| `binary_sensor.vents_alarm` | Input 38 and Discrete Inputs 19–71 |

## Protocol behavior

One scan reads IR0–50, HR0–75, Coils 0–25, DI0–71, and the optional IR51–53 extension. Only an Illegal Data Address exception on that extension suppresses it for the connection. Other Modbus exceptions and incomplete responses fail the scan. Negative temperatures are signed; sensor-fault sentinels and absent air-quality sensors are unavailable.

All requests use one TCP socket and lock. Multi-command actions are serialized but are not transactional at the device: if a later command fails, earlier acknowledged writes may already have taken effect. The integration marks state unavailable rather than claiming a partial sequence succeeded; the next scan reconciles actual device state. No automatic write retry or rollback is attempted.

The integration does not write factory reset, PID coefficients, protection configuration, sensor enable flags, or network settings. Weekly schedule content and hardware commissioning remain in Vents Home.

Sources: [A21 register map](https://ventilation-system.com/download/vutr-ve-ec-manual-1402.pdf), [A21 controller manual](https://www.systemair.nz/wp-content/uploads/2025/11/A21-Manual.pdf).
