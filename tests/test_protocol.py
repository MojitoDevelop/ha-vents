"""Verify real Modbus TCP requests against an independent loopback peer."""

import asyncio

import pytest

from custom_components.vents_a21.protocol import (
    Command,
    Snapshot,
    UnsupportedController,
    VentsClient,
    VentsError,
)


def test_signed_measurements_and_fault_sentinels():
    data = Snapshot(inputs={1: 65491, 2: 215, 3: 0x8000, 4: 0x7FFF})
    assert data.temperature(1) == -4.5
    assert data.temperature(2) == 21.5
    assert data.temperature(3) is None
    assert data.temperature(4) is None
    assert data.temperature(5) is None


async def test_full_read_and_packed_clocks(peer):
    client = VentsClient("127.0.0.1", peer.port, 1, connect_delay=0)
    try:
        await client.async_validate()
        data = await client.async_read()
        assert data.inputs[37] == 1
        assert data.inputs[52] == 45
        assert data.temperature(1) == -4.5
        assert data.holding[44] == 23
        assert data.duration_hours(27) == 2138.5
        assert data.duration_hours(29) == 2883.25
        assert data.timer_remaining == 4205
        assert peer.requests[0] == (4, 37, 1, 1)
        assert peer.writes == []
    finally:
        await client.async_close()


async def test_write_acknowledgement_and_actual_readback(peer):
    client = VentsClient("127.0.0.1", peer.port, 1, connect_delay=0)
    try:
        data = await client.async_execute(
            [Command("holding", 44, 24), Command("coil", 2, True)]
        )
        assert peer.writes == [(6, 44, 24), (5, 2, 0xFF00)]
        assert data.holding[44] == 24
        assert data.coils[2] is True
        assert peer.requests[-1] == (4, 51, 3, 1)
    finally:
        await client.async_close()


async def test_old_firmware_can_omit_only_the_extension(peer):
    peer.extension_supported = False
    client = VentsClient("127.0.0.1", peer.port, 1, connect_delay=0)
    try:
        for _ in range(2):
            data = await client.async_read()
            assert 51 not in data.inputs
            assert data.holding[44] == 23
        assert sum(1 for request in peer.requests if request[:2] == (4, 51)) == 1
    finally:
        await client.async_close()


async def test_wrong_controller_is_rejected(peer):
    peer.inputs[37] = 2
    client = VentsClient("127.0.0.1", peer.port, 1, connect_delay=0)
    try:
        with pytest.raises(UnsupportedController):
            await client.async_validate()
        assert peer.writes == []
    finally:
        await client.async_close()


async def test_reconnect_rechecks_status_extensions(peer):
    peer.extension_supported = False
    client = VentsClient("127.0.0.1", peer.port, 1, connect_delay=0)
    try:
        assert 51 not in (await client.async_read()).inputs
        await client.async_close()
        peer.extension_supported = True
        assert (await client.async_read()).inputs[51] == 25
    finally:
        await client.async_close()


@pytest.mark.parametrize(
    "failure", ["reject_write", "drop_write_reply", "wrong_write_ack"]
)
async def test_failed_or_ambiguous_writes_are_not_retried(peer, failure):
    setattr(peer, failure, True)
    client = VentsClient("127.0.0.1", peer.port, 1, timeout=0.1, connect_delay=0)
    try:
        with pytest.raises(VentsError):
            await client.async_execute(
                [Command("holding", 44, 25), Command("coil", 0, True)]
            )
        assert len([r for r in peer.requests if r[0] == 6]) == 1
        assert not any(r[0] == 5 for r in peer.requests)
    finally:
        await client.async_close()


async def test_truncated_reads_cannot_become_a_snapshot(peer):
    peer.short_read = True
    client = VentsClient("127.0.0.1", peer.port, 1, timeout=0.1, connect_delay=0)
    try:
        with pytest.raises(VentsError):
            await client.async_read()
    finally:
        await client.async_close()


async def test_scans_and_command_sequences_do_not_interleave(peer):
    client = VentsClient("127.0.0.1", peer.port, 1, connect_delay=0)
    try:
        await asyncio.gather(
            client.async_read(),
            client.async_execute(
                [
                    Command("holding", 17, 60),
                    Command("holding", 2, 255),
                    Command("coil", 0, True),
                ]
            ),
            client.async_read(),
        )
        indices = [i for i, r in enumerate(peer.requests) if r[0] in (5, 6)]
        assert indices == list(range(indices[0], indices[0] + 3))
        assert max(len(peer.writers), 1) == 1
    finally:
        await client.async_close()
