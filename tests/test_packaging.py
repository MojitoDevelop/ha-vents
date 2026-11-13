"""Check the artifacts HACS and manual installers actually consume."""

import hashlib
import json
import zipfile
from pathlib import Path

from custom_components.vents_a21.binary_sensor import FLAGS
from custom_components.vents_a21.number import NUMBERS
from custom_components.vents_a21.sensor import SENSORS
from scripts.build_release import build

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/vents_a21"


def test_all_declared_entities_have_both_translations():
    translations = [
        json.loads((COMPONENT / f"translations/{lang}.json").read_text())
        for lang in ("en", "pl")
    ]
    for doc in translations:
        for spec in SENSORS:
            assert doc["entity"]["sensor"][spec.key]["name"]
        for spec in NUMBERS:
            assert doc["entity"]["number"][spec.key]["name"]
        for key, *_ in FLAGS:
            assert doc["entity"]["binary_sensor"][key]["name"]
    assert json.loads((COMPONENT / "strings.json").read_text()) == translations[0]
    assert (
        translations[0]["entity"]["sensor"]["active_alarm"]["state"].keys()
        == translations[1]["entity"]["sensor"]["active_alarm"]["state"].keys()
    )


def test_release_is_reproducible_complete_and_installable(tmp_path):
    first, checksum, tag = build(tmp_path / "first")
    second, _, _ = build(tmp_path / "second")
    assert first.read_bytes() == second.read_bytes()
    assert (
        checksum.read_text().split()[0]
        == hashlib.sha256(first.read_bytes()).hexdigest()
    )
    assert tag == "v" + json.loads((COMPONENT / "manifest.json").read_text())["version"]
    with zipfile.ZipFile(first) as package:
        names = package.namelist()
        assert "custom_components/vents_a21/manifest.json" in names
        assert "custom_components/vents_a21/brand/icon.png" in names
        assert "custom_components/vents_a21/translations/pl.json" in names
        assert not any("__pycache__" in name or name.endswith(".pyc") for name in names)
        assert package.testzip() is None
