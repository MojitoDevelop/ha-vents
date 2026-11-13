"""Build a reproducible manual-install archive and SHA-256 checksum."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/vents_a21"


def build(output: Path) -> tuple[Path, Path, str]:
    version = json.loads((COMPONENT / "manifest.json").read_text())["version"]
    tag = f"v{version}"
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"vents-a21-{tag}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
        for path in sorted(COMPONENT.rglob("*")):
            if (
                not path.is_file()
                or "__pycache__" in path.parts
                or path.suffix == ".pyc"
            ):
                continue
            info = zipfile.ZipInfo(
                path.relative_to(ROOT).as_posix(), date_time=(2026, 1, 1, 0, 0, 0)
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            package.writestr(info, path.read_bytes())
    checksum = archive.with_suffix(".zip.sha256")
    checksum.write_text(
        f"{hashlib.sha256(archive.read_bytes()).hexdigest()}  {archive.name}\n"
    )
    return archive, checksum, tag


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    archive, checksum, tag = build(args.output)
    print(f"Built {archive.name}")
    if args.github_output:
        with args.github_output.open("a") as handle:
            handle.write(
                f"tag={tag}\narchive={archive}\nchecksum={checksum}\nnotes={ROOT / 'RELEASE_NOTES.md'}\n"
            )
