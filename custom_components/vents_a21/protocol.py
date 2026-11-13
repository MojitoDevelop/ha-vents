"""Small serialized Modbus TCP client for the published A21 register map.

All addresses are zero based. Input and holding registers are separate spaces.
No write is retried automatically, including after an ambiguous lost response.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException


class VentsError(Exception):
    """A connection, malformed response, or Modbus exception."""


class UnsupportedController(VentsError):
    """The peer does not identify as A21."""


@dataclass(frozen=True)
class Command:
    """A single explicitly supported write."""

    kind: str
    address: int
    value: int | bool


@dataclass
class Snapshot:
    """One complete scan; optional extension registers can be absent."""

    inputs: dict[int, int] = field(default_factory=dict)
    holding: dict[int, int] = field(default_factory=dict)
    coils: dict[int, bool] = field(default_factory=dict)
    discrete: dict[int, bool] = field(default_factory=dict)

    def temperature(self, address: int) -> float | None:
        raw = self.inputs.get(address)
        if raw is None or raw in (0x8000, 0x7FFF):
            return None
        return (raw - 65536 if raw >= 32768 else raw) / 10

    @property
    def alarms(self) -> list[int]:
        return [
            address - 19
            for address, value in self.discrete.items()
            if address >= 19 and value
        ]

    def duration_hours(self, address: int) -> float | None:
        """A21 packed clock: low byte hours, high byte minutes, then days."""
        first, days = self.inputs.get(address), self.inputs.get(address + 1)
        if first is None or days is None:
            return None
        hours, minutes = first & 255, first >> 8
        if hours > 23 or minutes > 59:
            return None
        return round(days * 24 + hours + minutes / 60, 3)

    @property
    def timer_remaining(self) -> int | None:
        first, second = self.inputs.get(25), self.inputs.get(26)
        if first is None or second is None:
            return None
        minutes, seconds, hours = first & 255, first >> 8, second >> 8
        if minutes > 59 or seconds > 59 or hours > 23:
            return None
        return hours * 3600 + minutes * 60 + seconds


class VentsClient:
    """Own exactly one TCP connection and serialize reads and writes."""

    def __init__(
        self,
        host: str,
        port: int,
        unit_id: int,
        timeout: float = 5,
        connect_delay: float = 2,
    ) -> None:
        self.unit_id = unit_id
        self.connect_delay = connect_delay
        self._client = AsyncModbusTcpClient(
            host, port=port, timeout=timeout, retries=0, reconnect_delay=0
        )
        self._lock = asyncio.Lock()
        self._extensions_supported: bool | None = None

    async def _connect(self) -> None:
        if not self._client.connected:
            if not await self._client.connect():
                raise VentsError("Cannot connect to the Modbus TCP device")
            if self.connect_delay:
                await asyncio.sleep(self.connect_delay)

    async def _request(self, method: str, address: int, **kwargs: Any) -> Any:
        try:
            response = await getattr(self._client, method)(
                address, device_id=self.unit_id, **kwargs
            )
        except (TimeoutError, ModbusException, OSError) as err:
            self._client.close()
            raise VentsError(str(err)) from err
        if response is None or response.isError():
            code = getattr(response, "exception_code", None)
            raise VentsError(f"{method} at {address}: Modbus exception {code}")
        return response

    async def _read(
        self, method: str, address: int, count: int, *, bits: bool = False
    ) -> list:
        response = await self._request(method, address, count=count)
        values = getattr(response, "bits" if bits else "registers", None)
        if values is None or len(values) < count:
            raise VentsError(f"Incomplete response for {method} at {address}")
        return values[:count]

    async def async_validate(self) -> None:
        async with self._lock:
            await self._connect()
            identity = await self._read("read_input_registers", 37, 1)
            if identity[0] != 1:
                raise UnsupportedController(
                    "Input register 37 does not identify an A21 controller"
                )

    async def _snapshot(self) -> Snapshot:
        inputs = await self._read("read_input_registers", 0, 51)
        if inputs[37] != 1:
            raise UnsupportedController("The device is no longer an A21 controller")
        holding = await self._read("read_holding_registers", 0, 76)
        coils = await self._read("read_coils", 0, 26, bits=True)
        discrete = await self._read("read_discrete_inputs", 0, 72, bits=True)
        snapshot = Snapshot(
            dict(enumerate(inputs)),
            dict(enumerate(holding)),
            dict(enumerate(coils)),
            dict(enumerate(discrete)),
        )
        # Some older firmware predates IR51-53. Only an explicit Illegal Data
        # Address response permits omitting them; network failures fail the scan.
        if self._extensions_supported is not False:
            try:
                response = await self._client.read_input_registers(
                    51, count=3, device_id=self.unit_id
                )
            except (TimeoutError, ModbusException, OSError) as err:
                self._client.close()
                raise VentsError(str(err)) from err
            if (
                response is not None
                and response.isError()
                and getattr(response, "exception_code", None) == 2
            ):
                self._extensions_supported = False
            elif response is None or response.isError() or len(response.registers) < 3:
                raise VentsError("Cannot read the A21 status extension")
            else:
                self._extensions_supported = True
                snapshot.inputs.update(
                    {51 + i: v for i, v in enumerate(response.registers[:3])}
                )
        return snapshot

    async def async_read(self) -> Snapshot:
        async with self._lock:
            await self._connect()
            return await self._snapshot()

    async def async_execute(self, commands: list[Command]) -> Snapshot:
        """Write a bounded sequence, then read back all states under one lock."""
        async with self._lock:
            await self._connect()
            for command in commands:
                method = "write_coil" if command.kind == "coil" else "write_register"
                response = await self._request(
                    method, command.address, value=command.value
                )
                expected = (
                    [bool(command.value)]
                    if command.kind == "coil"
                    else [int(command.value)]
                )
                returned = getattr(
                    response, "bits" if command.kind == "coil" else "registers", []
                )
                if (
                    getattr(response, "address", None) != command.address
                    or returned[:1] != expected
                ):
                    raise VentsError(
                        "The write acknowledgement does not match the command"
                    )
            return await self._snapshot()

    async def async_close(self) -> None:
        async with self._lock:
            self._client.close()
