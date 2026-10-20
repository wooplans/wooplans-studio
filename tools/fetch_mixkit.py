"""Télécharge des musiques Mixkit par titre (exécuté sur GitHub Actions) : python tools/fetch_mixkit.py "Titre|Artiste" ...
Cherche la page de résultats, retrouve le lien .mp3 du titre et l'enregistre dans assets/music/."""
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "assets" / "music"
UA = {"User-Agent": "Mozilla/5.0"}


def get(url: str) -> bytes:
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()


def main(specs):
    OUT.mkdir(parents=True, exist_ok=True)
    html = get("https://mixkit.co/free-stock-music/discover/africa/").decode("utf-8", "replace")
    for pg in (2, 3):
        try:
            html += get(f"https://mixkit.co/free-stock-music/discover/africa/?page={pg}").decode("utf-8", "replace")
        except Exception:
            break
    for spec in specs:
        title, artist = spec.split("|")
        i = html.find(f">{title}<")
        if i < 0:
            i = html.find(title.replace("'", "&#39;"))
        block = html[max(0, i - 3000): i + 3000] if i >= 0 else ""
        m = re.findall(r"https://assets\.mixkit\.co/[^\"'\s]*?\.mp3", block)
        print(title, "->", m[:3])
        if not m:
            print("INTROUVABLE", title)
            continue
        mid = re.search(r"mixkit-(\d+)", m[0])
        name = f"{re.sub(r'[^A-Za-z0-9]+', '-', title).strip('-')}_{re.sub(r'[^A-Za-z0-9]+', '-', artist).strip('-')}_mixkit-{mid.group(1) if mid else 'x'}.mp3"
        (OUT / name).write_bytes(get(m[0]))
        print("ok", name)


if __name__ == "__main__":
    main(sys.argv[1:])
