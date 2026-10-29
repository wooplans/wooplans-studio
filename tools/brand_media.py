"""Originaux propres des rendus → JPEG avec filigranes WooPlans, rangés dans un lot d'images.

  python tools/brand_media.py <dossier_originaux> batches/images/<lot>

<dossier_originaux> contient des fichiers <CODE>_<n>.<ext> (ex. D4-003_1.png, V3-005_3.jpg ; n = 1 pour la couverture).
Écrit <lot>/media/<CODE>/<n>.jpg (côté long ≤ 1600 px). Les originaux ne sont jamais copiés dans le dépôt :
ils viennent de R2 (privé) via le connecteur WooPlans, ou des rendus propres publics du site.
"""
import re
import sys
from pathlib import Path

from wooplans.image_tools import brand_watermark

NAME = re.compile(r"^([DV]\d-\d{3})_(\d+)\.(?:png|jpe?g|webp)$", re.I)


def brand_dir(src: Path, lot: Path) -> int:
    n = 0
    for f in sorted(src.iterdir()):
        m = NAME.match(f.name)
        if not m:
            continue
        out = lot / "media" / m.group(1).upper() / f"{int(m.group(2))}.jpg"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(brand_watermark(f.read_bytes()))
        n += 1
    return n


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    count = brand_dir(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"{count} images filigranées")
    sys.exit(0 if count else 1)
