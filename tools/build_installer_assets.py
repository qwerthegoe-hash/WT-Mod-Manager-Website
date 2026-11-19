"""Generate branded wizard imagery from the project's existing logo.

This code runs at build time on Windows. No stock images, new logo or
third-party artwork is needed. Outputs are deterministic for the same logo.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
LOGO = ROOT / "assets" / "icons" / "Logotip" / "LogotipProject.png"
OUT = ROOT / "build" / "installer"


def _font(size: int, bold: bool = False):
    possible = (
        ("C:/Windows/Fonts/segoeuib.ttf" if bold
         else "C:/Windows/Fonts/segoeui.ttf"),
        ("C:/Windows/Fonts/arialbd.ttf" if bold
         else "C:/Windows/Fonts/arial.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for path in possible:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _logo(size: int) -> Image.Image:
    with Image.open(LOGO) as loaded:
        image = loaded.convert("RGBA")
    box = image.getbbox()
    if box:
        image = image.crop(box)
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    square = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    square.alpha_composite(image, ((size-image.width)//2,
                                   (size-image.height)//2))
    return square


def _gradient(width: int, height: int):
    image = Image.new("RGB", (width, height))
    pixel = image.load()
    for y in range(height):
        for x in range(width):
            t = y / max(1, height - 1)
            glow = max(0, 1 - ((x - width*.55)**2 / (width*.9)**2
                                + (y - height*.28)**2 / (height*.36)**2))
            pixel[x, y] = (
                int(10 + 6*t + glow*14),
                int(18 + 6*t + glow*21),
                int(32 + 8*t + glow*38),
            )
    return image


def main():
    if not LOGO.is_file():
        raise SystemExit("Project logo is missing: " + str(LOGO))
    OUT.mkdir(parents=True, exist_ok=True)

    # Official app and Start-menu icon. Transparent logo is preserved.
    _logo(256).save(
        OUT / "WTModManager.ico", format="ICO",
        sizes=[(16,16), (24,24), (32,32), (48,48), (64,64),
               (128,128), (256,256)]
    )

    width, height = 820, 1570
    image = _gradient(width, height).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle((40, 34, width-40, height-40),
                           radius=50, outline=(69, 126, 214, 125), width=4)
    draw.line((80, 115, 230, 115), fill=(76, 168, 255), width=7)
    # Subtle brand rings, all shapes are drawn rather than sourced imagery.
    cx, cy = width//2, 555
    for radius, alpha in [(280,38), (236,54), (197,68)]:
        draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius),
                     outline=(70,165,254,alpha),width=4)
    logo = _logo(425)
    image.alpha_composite(logo, ((width-425)//2, 340))
    draw.text((width//2, 1040), "WT MOD MANAGER",
              font=_font(61, True), fill="#FFFFFF", anchor="mm")
    draw.text((width//2, 1110), "INSTALLATION",
              font=_font(28), fill="#8BBEFF", anchor="mm")
    draw.line((105, 1190, width-105, 1190),
              fill=(62, 102, 153, 220), width=2)
    draw.text((width//2, 1260), "Custom mods. Your setup.",
              font=_font(31), fill="#D1E3FB", anchor="mm")
    draw.text((width//2, 1314), "Windows Edition",
              font=_font(25), fill="#87A6C9", anchor="mm")
    image.convert("RGB").save(OUT / "wizard.png", optimize=True)

    # The old small image covered all 320x320 pixels with an opaque, almost
    # black gradient. Inno then shrank that square to 58x58, exposing harsh
    # black corners on its dark-gray title area. Render a real RGBA rounded
    # card: antialiased transparency outside the radius, clipped logo inside.
    # Inno Setup uses WizardSmallImageBackColor=none, so no corner fill occurs.
    scale = 4
    side = 320
    outer = Image.new("RGBA", (side * scale, side * scale), (0, 0, 0, 0))
    card = _gradient(side * scale, side * scale).convert("RGBA")
    logo = _logo(258 * scale)
    card.alpha_composite(logo, (31 * scale, 31 * scale))
    card_draw = ImageDraw.Draw(card)
    card_draw.rounded_rectangle(
        (5 * scale, 5 * scale, 315 * scale, 315 * scale),
        radius=38 * scale, outline=(79, 159, 245, 255),
        width=4 * scale,
    )
    mask = Image.new("L", (side * scale, side * scale), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        (5 * scale, 5 * scale, 315 * scale, 315 * scale),
        radius=38 * scale, fill=255,
    )
    card.putalpha(mask)
    outer.alpha_composite(card)
    small = outer.resize((side, side), Image.Resampling.LANCZOS)
    small.save(OUT / "wizard-small.png", optimize=True)
    assert small.getpixel((0, 0))[3] == 0
    assert small.getpixel((side // 2, side // 2))[3] == 255
    print("Generated branded Inno Setup assets in", OUT)


if __name__ == "__main__":
    main()
