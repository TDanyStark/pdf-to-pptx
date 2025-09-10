"""Generate a multi-size Windows .ico from a PNG using Pillow.

Usage:
    python scripts/make_icon.py icon.png icon.ico

If output path is omitted, writes next to input as icon.ico
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image
except Exception as e:  # pragma: no cover
    print("ERROR: Pillow no está instalado. Ejecuta: pip install Pillow")
    raise


SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Uso: python scripts/make_icon.py <input.png> [output.ico]")
        return 2

    in_path = Path(argv[1]).resolve()
    if not in_path.exists():
        print(f"No existe: {in_path}")
        return 2

    if len(argv) >= 3:
        out_path = Path(argv[2]).resolve()
    else:
        out_path = in_path.with_suffix('.ico')

    # Open as RGBA to preserve transparency
    img = Image.open(in_path).convert("RGBA")

    # For ICO, Pillow expects a single image with sizes param
    # Optionally ensure image is square by padding
    w, h = img.size
    if w != h:
        side = max(w, h)
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        offset = ((side - w) // 2, (side - h) // 2)
        canvas.paste(img, offset)
        img = canvas

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, sizes=SIZES)
    print(f"Icono creado: {out_path} ({', '.join(f'{w}x{h}' for w,h in SIZES)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
