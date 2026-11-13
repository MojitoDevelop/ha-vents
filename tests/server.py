"""Independent minimal Modbus TCP peer exercising real pymodbus framing.

No production conversion helpers are used here. The fixture is a protocol
simulation, not a capture from a physical A21 unit.
"""

import asyncio
import struct


class ModbusPeer:
    def __init__(self):
        self.inputs = [0] * 54
        self.inputs[0:5] = [215, 65491, 205, 220, 80]
        self.inputs[10:18] = [55, 0, 800, 0, 12, 0, 30, 0]
        self.inputs[19:25] = [180, 175, 50, 48, 1500, 1450]
        self.inputs[25:31] = [0x050A, 0x0100, 0x1E02, 89, 0x0F03, 120]
        self.inputs[34:39] = [0x0B01, 0x0611, 2026, 1, 0]
        self.inputs[51:54] = [25, 45, 42]
        self.holding = [0] * 76
        self.holding[0:5] = [0, 3, 1, 20, 100]
        self.holding[7:13] = [40, 38, 70, 68, 100, 95]
        self.holding[17] = 50
        self.holding[23:25] = [50, 540]
        self.holding[27:33] = [150, 145, 300, 290, 540, 520]
        self.holding[43:59] = [
            3,
            23,
            60,
            1200,
            400,
            40,
            3,
            23,
            0x1E00,
            7,
            2,
            1,
            0,
            2,
            2,
            90,
        ]
        self.holding[68:76] = [2, 50, 2, 0, 2, 50, 2, 100]
        self.coils = [False] * 26
        self.coils[0] = True
        self.discrete = [False] * 72
        self.requests = []
        self.writes = []
        self.writers = set()
        self.disconnected = asyncio.Event()
        self.extension_supported = True
        self.reject_write = False
        self.drop_write_reply = False
        self.wrong_write_ack = False
        self.fail_reads = False
        self.short_read = False

    async def start(self):
        self.server = await asyncio.start_server(self.handle, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def close(self):
        self.server.close()
        for writer in list(self.writers):
            writer.close()
            await writer.wait_closed()
        await self.server.wait_closed()

    async def handle(self, reader, writer):
        self.writers.add(writer)
        try:
            while True:
                transaction, protocol, length, unit = struct.unpack(
                    ">HHHB", await reader.readexactly(7)
                )
                pdu = await reader.readexactly(length - 1)
                function, address, value = struct.unpack(">BHH", pdu)
                self.requests.append((function, address, value, unit))
                if protocol != 0 or unit != 1:
                    break
                if function <= 4:
                    if self.fail_reads:
                        response = bytes([function | 0x80, 4])
                    elif (
                        function == 4 and address == 51 and not self.extension_supported
                    ):
                        response = bytes([function | 0x80, 2])
                    else:
                        bank = {
                            1: self.coils,
                            2: self.discrete,
                            3: self.holding,
                            4: self.inputs,
                        }[function]
                        values = bank[address : address + value]
                        if self.short_read:
                            values = values[:1]
                        if function in (1, 2):
                            raw = bytes(
                                sum(
                                    bool(bit) << i
                                    for i, bit in enumerate(values[offset : offset + 8])
                                )
                                for offset in range(0, len(values), 8)
                            )
                        else:
                            raw = b"".join(struct.pack(">H", item) for item in values)
                        response = bytes([function, len(raw)]) + raw
                elif function in (5, 6):
                    if self.reject_write:
                        response = bytes([function | 0x80, 3])
                    else:
                        self.writes.append((function, address, value))
                        if function == 5:
                            self.coils[address] = value == 0xFF00
                            if address == 17:
                                self.inputs[31] = 0
                            if address == 18:
                                self.inputs[38] = 0
                                self.discrete[19:] = [False] * 53
                        else:
                            self.holding[address] = value
                        if self.drop_write_reply:
                            break
                        response = struct.pack(
                            ">BHH", function, address + int(self.wrong_write_ack), value
                        )
                else:
                    response = bytes([function | 0x80, 1])
                writer.write(
                    struct.pack(">HHHB", transaction, 0, len(response) + 1, unit)
                    + response
                )
                await writer.drain()
        except asyncio.IncompleteReadError, ConnectionError:
            pass
        finally:
            self.writers.discard(writer)
            writer.close()
            self.disconnected.set()
