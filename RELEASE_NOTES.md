# Vents 0.1.0

Initial local Home Assistant integration for Vents A21, prepared for the VUT 400 HBE EC A21 register map.

Install through HACS as a custom Integration repository, restart Home Assistant, and add **Vents** from Devices & services. Stop the previous YAML Modbus hub before connecting.

Includes ventilation, temperature, bypass, native timer and schedule controls; filter and alarm maintenance; diagnostic readings; optional air-quality and airflow sensors. English names by default, Polish translation, English entity IDs.

The attached ZIP supports manual installation; its SHA-256 checksum is provided separately. HACS uses the integration directory in this release tag.

Validated with Home Assistant and an independent local Modbus TCP simulator. A live Vents unit was not available for commissioning. Compare timer and clock values with the physical controller during installation.
