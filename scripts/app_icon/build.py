"""Build Signal Viewer app icons (Design A) for Windows, macOS and Linux."""
import shutil
import struct
import subprocess
from pathlib import Path

from PIL import Image

OUT = Path("/home/claude/iconbuild/signal-viewer-icons")
SRC = OUT / "src"
BG, TRACE, MARK = "#0E1A2B", "#3DD6C4", "#FF9F43"

CURVE = ("M72 300 C 110 300, 120 300, 140 290 C 160 280, 168 170, 186 170 "
         "C 204 170, 210 330, 232 330 C 254 330, 262 250, 280 250 "
         "C 298 250, 304 310, 326 310 C 346 310, 356 130, 376 130 "
         "C 396 130, 404 320, 424 320 C 436 320, 440 300, 440 300")


def art(level):
    """Glyph drawn in a 512x512 space. level: full | medium | small | tiny."""
    if level == "full":
        grid = "".join(
            f'<line x1="56" y1="{y}" x2="456" y2="{y}"/>' for y in (176, 256, 336)
        ) + "".join(
            f'<line x1="{x}" y1="88" x2="{x}" y2="424"/>' for x in (176, 256, 336)
        )
        drops = "".join(
            f'<line x1="{x}" y1="{y}" x2="{x}" y2="400"/>'
            for x, y in ((186, 196), (280, 276), (376, 156))
        )
        dots = "".join(
            f'<circle cx="{x}" cy="{y}" r="20"/>' for x, y in ((186, 170), (280, 250), (376, 130))
        )
        return (
            f'<g stroke="#FFFFFF" stroke-opacity="0.08" stroke-width="4">{grid}</g>'
            f'<g stroke="{MARK}" stroke-opacity="0.45" stroke-width="5" stroke-dasharray="10 12" stroke-linecap="round">{drops}</g>'
            f'<path d="{CURVE}" fill="none" stroke="{TRACE}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<g fill="{MARK}" stroke="{BG}" stroke-width="8">{dots}</g>'
        )
    if level == "medium":
        dots = "".join(
            f'<circle cx="{x}" cy="{y}" r="26"/>' for x, y in ((186, 170), (280, 250), (376, 130))
        )
        return (
            f'<path d="{CURVE}" fill="none" stroke="{TRACE}" stroke-width="28" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<g fill="{MARK}" stroke="{BG}" stroke-width="10">{dots}</g>'
        )
    if level == "small":
        return (
            f'<path d="M64 310 L 186 150 L 260 330 L 376 110 L 448 310" fill="none" stroke="{TRACE}" stroke-width="48" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="376" cy="110" r="44" fill="{MARK}"/>'
        )
    return (
        f'<path d="M64 330 L 200 140 L 300 360 L 448 110" fill="none" stroke="{TRACE}" stroke-width="72" stroke-linecap="round" stroke-linejoin="round"/>'
    )


RADIUS = {"full": 114, "medium": 114, "small": 96, "tiny": 80}


def svg_square(level):
    """Full-bleed rounded square (Windows, Linux)."""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">'
        f'<rect width="512" height="512" rx="{RADIUS[level]}" fill="{BG}"/>{art(level)}</svg>'
    )


def svg_mac(level):
    """macOS grid: 1024 canvas, 824x824 body at 100,100, ~185 corner radius, soft shadow."""
    s = 824 / 512
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">'
        '<defs><filter id="sh" x="-20%" y="-20%" width="140%" height="140%">'
        '<feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="#000" flood-opacity="0.30"/></filter></defs>'
        f'<rect x="100" y="100" width="824" height="824" rx="185" fill="{BG}" filter="url(#sh)"/>'
        f'<g transform="translate(100 100) scale({s})">{art(level)}</g></svg>'
    )


def level_for(px):
    if px >= 96:
        return "full"
    if px >= 48:
        return "medium"
    if px >= 28:
        return "small"
    return "tiny"


def render(svg_text, px, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["rsvg-convert", "-w", str(px), "-h", str(px), "-o", str(dest)],
        input=svg_text.encode(), check=True,
    )
    return dest


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    SRC.mkdir(parents=True)
    for lvl in RADIUS:
        (SRC / f"signal-viewer-{lvl}.svg").write_text(svg_square(lvl))
        (SRC / f"signal-viewer-macos-{lvl}.svg").write_text(svg_mac(lvl))
    tmp = OUT / ".tmp"

    # Windows .ico
    ico_sizes = [16, 20, 24, 32, 40, 48, 64, 96, 128, 256]
    ico_imgs = [Image.open(render(svg_square(level_for(p)), p, tmp / f"w{p}.png")).convert("RGBA")
                for p in ico_sizes]
    (OUT / "windows").mkdir(parents=True)
    ico_imgs[-1].save(OUT / "windows" / "signal-viewer.ico", format="ICO",
                      sizes=[(p, p) for p in ico_sizes], append_images=ico_imgs[:-1])

    # macOS .icns + .iconset
    iconset = OUT / "macos" / "SignalViewer.iconset"
    for base in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            px = base * scale
            name = f"icon_{base}x{base}{'@2x' if scale == 2 else ''}.png"
            # small slots use simplified glyphs; padding keeps the mac grid
            render(svg_mac(level_for(px * 824 // 1024)), px, iconset / name)
    # Hand-written ICNS so the 16/32 px @1x slots (icp4/icp5) are included
    slots = [("icp4", "icon_16x16"), ("icp5", "icon_32x32"), ("ic11", "icon_16x16@2x"),
             ("ic12", "icon_32x32@2x"), ("ic07", "icon_128x128"), ("ic13", "icon_128x128@2x"),
             ("ic08", "icon_256x256"), ("ic14", "icon_256x256@2x"), ("ic09", "icon_512x512"),
             ("ic10", "icon_512x512@2x")]
    body = b"".join(
        t.encode() + struct.pack(">I", 8 + len(d)) + d
        for t, d in ((t, (iconset / f"{n}.png").read_bytes()) for t, n in slots)
    )
    (OUT / "macos" / "SignalViewer.icns").write_bytes(b"icns" + struct.pack(">I", 8 + len(body)) + body)

    # Linux hicolor theme
    hicolor = OUT / "linux" / "hicolor"
    for px in (16, 22, 24, 32, 48, 64, 128, 256, 512):
        render(svg_square(level_for(px)), px, hicolor / f"{px}x{px}" / "apps" / "signal-viewer.png")
    scal = hicolor / "scalable" / "apps"
    scal.mkdir(parents=True)
    (scal / "signal-viewer.svg").write_text(svg_square("full"))

    # Generic PNG for Qt window icon
    render(svg_square("full"), 256, OUT / "signal-viewer-256.png")
    shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
