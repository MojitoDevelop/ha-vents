"""Prepare HA brand sizes from the original artwork hosted by Vents Group.

Only whitespace cropping, proportional resizing, and white padding are used.
The icon uses the brand emblem; the logo keeps the full Vents wordmark.
"""

from pathlib import Path

from PIL import Image, ImageChops, ImageOps

root = Path(__file__).resolve().parents[1]
target = root / "custom_components/vents_a21/brand"
target.mkdir(exist_ok=True)
source = Image.open(root / "assets/vents/logo-original.png").convert("RGB")
white = Image.new("RGB", source.size, "white")
wordmark = source.crop(ImageChops.difference(source, white).getbbox())
# The source is 800 x 282. Its emblem is left of the wordmark, separated by
# white space. Keep its original geometry rather than redrawing the symbol.
emblem = source.crop((144, 96, 272, 192))
emblem = emblem.crop(
    ImageChops.difference(emblem, Image.new("RGB", emblem.size, "white")).getbbox()
)
for factor, suffix in ((1, ""), (2, "@2x")):
    icon = ImageOps.pad(
        emblem,
        (256 * factor, 256 * factor),
        method=Image.Resampling.LANCZOS,
        color="white",
    )
    icon.save(target / f"icon{suffix}.png")
    logo = Image.new("RGB", (512 * factor, 128 * factor), "white")
    resized = ImageOps.contain(
        wordmark,
        (480 * factor, 112 * factor),
        method=Image.Resampling.LANCZOS,
    )
    logo.paste(
        resized,
        ((logo.width - resized.width) // 2, (logo.height - resized.height) // 2),
    )
    logo.save(target / f"logo{suffix}.png")
