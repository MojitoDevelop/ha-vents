# Vents for Home Assistant

![Vents](custom_components/vents_a21/brand/logo.png)

Local Modbus TCP integration for **Vents A21** ventilation controllers, prepared for the **VUT 400 HBE EC A21** register map. Configure it in Home Assistant without YAML or a cloud account.

[Polska instrukcja](README.pl.md) · [Entities and registers](docs/registers.md) · [Migration from YAML](docs/migration.md)

## Install with HACS

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=MojitoDevelop&repository=ha-vents&category=integration)

1. In **HACS → ⋮ → Custom repositories**, add `https://github.com/MojitoDevelop/ha-vents` with category **Integration**.
2. Download **Vents** and restart Home Assistant.
3. Open **Settings → Devices & services → Add integration → Vents**.
4. Enter the controller IP address, port (normally `502`), and unit ID (normally `1`).

Requires **Home Assistant 2026.10.0 or later**. This repository can be installed as a HACS custom repository; publication here does not imply inclusion in the HACS default catalog.

For manual installation, extract the release archive into your HA configuration directory so that `/config/custom_components/vents_a21/manifest.json` exists, then restart HA.

## Features

- Ventilation power, supported speed presets, and manual speed with limits read from the controller.
- Temperature control: ventilation only, heating, cooling/free cooling, automatic; integer targets of 15–30 °C and 0.1 °C measurements.
- Bypass modes adapted to the installed actuator; percentage setpoint only for an analogue bypass.
- Built-in timer, timer duration/speed/temperature, and weekly schedule enable/disable. Edit the weekly schedule itself in Vents Home.
- Four air temperatures, selected control temperature, reported fan output and bypass status, heater activity/control signal, filter state, filter countdown, operating time, active alarm codes and descriptions.
- Filter countdown reset and alarm reset buttons.
- Optional humidity, CO₂, PM2.5, VOC, airflow, duct pressure, RPM, and additional temperatures through the integration's **Configure** options.
- Advanced per-speed supply/extract settings, disabled by default. Output settings apply to percentage mode; airflow settings apply to constant-flow mode.
- English display names by default and Polish translations when HA uses Polish. **Entity IDs stay English**, for example `sensor.vents_outdoor_air_temperature`, `fan.vents_ventilation`, and `climate.vents_climate`. Home Assistant can append `_2` etc. when names are already used.

## Connecting and migrating

A21 supports **one Modbus TCP client per interface**. Remove the existing `reku` Modbus YAML hub and stop other clients using the same interface before configuring this integration. Preserve any unrelated Modbus devices. See the [migration table](docs/migration.md) for old entity and dashboard action replacements.

Configuration checks A21 identity (input register 37 = 1) without writing settings. On startup the integration only reads state. Commands and scans share one queue; every successful command is followed by a complete readback. Writes are not automatically retried after an ambiguous timeout. A failed scan makes entities unavailable and later successful scans restore them.

The default scan interval is 10 seconds. Timeout, connection delay, and update interval are configurable. Network settings can be changed using **Reconfigure** on the integration entry. Changing options reloads the integration.

## Interpreting values

- `manual_speed_setpoint` and `bypass_setpoint` are commands/settings; `supply_fan_output`, `extract_fan_output`, and `bypass_position` report separate controller status. A preset has no invented percentage.
- The climate's current temperature is input register 0: the sensor selected for temperature control inside A21. It can differ from supply air temperature.
- Boost and Fireplace are **read-only statuses** in the published Modbus map. The timer provides timed ventilation. Higher-priority modes and protection logic can override normal speed requests; the integration preserves that controller behavior.
- Cooling mode can use outdoor air through the bypass. It does not indicate that an optional active cooler is installed.
- Enable only optional hardware actually fitted. A21 reports zero for missing air-quality sensors; these entities become unavailable. Enabling an option in HA does not enable that sensor's controller input.
- The heater signal is a controller output, not measured electrical power. Values above 100 indicate additional fan assistance. No measured W/kWh or calculated heat-recovery efficiency is fabricated.
- Older firmware can omit status registers 51–53; those three entities are then unavailable while the base map remains usable.

## Validation and support

The suite runs actual Home Assistant services and a real PyModbus TCP client against an independent loopback Modbus simulator. It covers register types, signed temperatures, sensor fault sentinels, command framing/order, timer packing, communication failure/recovery, optional hardware, configuration, unload, and English IDs under both English and Polish HA.

**Physical-device commissioning is still required.** The release was developed from documentation and the supplied YAML mapping, not from a live connection to the user's unit. Packed timer and clock fields should be checked against the controller display during commissioning. Other A21 equipment may expose a different hardware subset.

Download integration diagnostics when reporting a problem. They contain register values and options but omit the private IP address. Do not include credentials or unrelated configuration in an issue.

Development:

```sh
python -m pip install -r requirements_test.txt
python scripts/test.py
ruff check .
ruff format --check .
python scripts/build_release.py
```

GitHub Actions runs the tests on HA 2026.10.0 and 2026.11.1, hassfest, and HACS validation. A successful build on `main` creates the manifest's versioned release and checksum. Increment the manifest version and update release notes before publishing a new release.

## Documentation sources

- [Vents A21 Modbus table, V55-8-1EN-02](https://ventilation-system.com/download/vutr-ve-ec-manual-1402.pdf) ([alternate manufacturer-document host](https://vents.vn/wp-content/uploads/2025/03/vutr-ve-ec-manual-1402.pdf)).
- [Vents A21 controller manual, V55-8EN-03](https://www.systemair.nz/wp-content/uploads/2025/11/A21-Manual.pdf), including alarm codes 0–45. Modbus codes 46–52 are preserved without guessing their meaning.
- [Vents HB/HBE product family](https://vents-group.pl/oferta/wentylacja-profesjonalna-centrale/vut-hb-hbe-ec).

This is an independent community integration and is not an official Vents product.
