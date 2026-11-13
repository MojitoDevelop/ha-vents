"""Render an original generic airflow icon; this is not the Vents trademark."""

from pathlib import Path

from PIL import Image, ImageDraw

target = Path(__file__).resolve().parents[1] / "custom_components/vents_a21/brand"
target.mkdir(exist_ok=True)
for size, suffix in ((256, ""), (512, "@2x")):
    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((16, 16, 496, 496), radius=112, fill="#087e8b")
    draw.line(((110, 188), (391, 188)), fill="white", width=28)
    draw.line(
        ((331, 128), (391, 188), (331, 248)), fill="white", width=28, joint="curve"
    )
    draw.line(((402, 324), (121, 324)), fill="white", width=28)
    draw.line(
        ((181, 264), (121, 324), (181, 384)), fill="white", width=28, joint="curve"
    )
    canvas.resize((size, size), Image.Resampling.LANCZOS).save(
        target / f"icon{suffix}.png"
    )
