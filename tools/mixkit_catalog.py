"""Base de musiques libres Mixkit pour les vidéos (licence « Mixkit Stock Music Free License » :
usage commercial autorisé, sans attribution, https://mixkit.co/license/#musicFree).

  python tools/mixkit_catalog.py crawl            # parcourt les catégories et (re)écrit assets/music/library.json
  python tools/mixkit_catalog.py fetch <id> ...   # télécharge des titres de la base dans assets/music/ (+ analyse si librosa)

library.json : un titre par identifiant Mixkit (titre, artiste, durée, étiquettes, catégories d'origine) et le champ
« use » : true = sélectionné pour les shorts (entraînant, positif, assez long ; recalculé à chaque crawl ;
« force »: true/false posé à la main l'emporte). Le rendu télécharge le mp3 à la demande
(wooplans/music.py) : les mp3 ne sont pas obligatoires dans le dépôt, seule l'analyse du tempo (tracks.json) l'est.
"""
import html as htmllib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "assets" / "music" / "library.json"
UA = {"User-Agent": "Mozilla/5.0"}
# catégories parcourues : ambiance « maison de rêve », positive et rythmée (pages 1 à PAGES)
SOURCES = ["discover/africa", "world", "pop", "house", "hip-hop", "funk", "dance", "electronica", "corporate",
           "mood/happy", "mood/energetic", "mood/lively", "mood/uplifting", "mood/upbeat", "mood/inspiring",
           "tag/motivational", "tag/summer", "tag/tropical"]
PAGES = 3
EXCLUDE = {"Sad", "Dark", "Horror", "Scary", "Suspense", "Children", "Comedy", "Humorous", "Christmas", "Halloween",
           "Romantic", "Melancholic", "Dramatic", "Tense", "Mysterious", "Relaxing", "Calm", "Sleep", "Meditation",
           "Disturbing", "Serious", "Modern Christmas", "Country", "Country Rock", "Western", "Rock", "Classic Rock",
           "Blues Rock", "Folk", "Arabic", "Game Show"}
EXCLUDE_TITLE = re.compile(r"christmas|new year|married|kids", re.I)
WANT = {"Happy", "Energetic", "Lively", "Uplifting", "Upbeat", "Inspiring", "Motivational", "Groovy", "Summer",
        "Tropical", "Positive", "Fun", "Cheerful", "Excited", "Dance", "House", "Pop", "Funk", "World", "Hip Hop"}
MIN_S = 60                                                                     # assez long pour 20-30 s utiles


def get(url: str) -> str:
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode("utf-8", "replace")


def parse(page: str):
    """Cartes de la grille : id, titre, artiste, étiquettes, durée."""
    for block in page.split('data-audio-player-item-id-value="')[1:]:
        mid = block.split('"', 1)[0]
        title = re.search(r'item-grid-card__title">\s*(.*?)\s*</h2>', block, re.S)
        artist = re.search(r'music-preview__author">\s*by\s*(.*?)\s*</p>', block, re.S)
        dur = re.search(r'data-test-id="duration">\s*(\d+):(\d+)', block)
        if not (mid.isdigit() and title and dur):
            continue
        tags = [htmllib.unescape(t) for t in re.findall(r'meta-links__link"[^>]*href="/free-stock-music/[^"]*">([^<]+)</a>',
                                                         block.split("download-button", 1)[0])]
        yield {"id": int(mid), "title": htmllib.unescape(title.group(1)).strip(),
               "artist": htmllib.unescape(artist.group(1)).strip() if artist else "",
               "duration": int(dur.group(1)) * 60 + int(dur.group(2)), "tags": tags}


def selected(t: dict) -> bool:
    """Choix automatique, sauf si « force » (true/false) a été posé à la main dans library.json."""
    if "force" in t:
        return bool(t["force"])
    tags = set(t["tags"])
    return (t["duration"] >= MIN_S and not tags & EXCLUDE and not EXCLUDE_TITLE.search(t["title"])
            and len(tags & WANT) >= 2)


def crawl():
    old = {t["id"]: t for t in json.loads(LIB.read_text(encoding="utf-8"))["tracks"]} if LIB.exists() else {}
    found = {}
    for src in SOURCES:
        for pg in range(1, PAGES + 1):
            url = f"https://mixkit.co/free-stock-music/{src}/" + (f"?page={pg}" if pg > 1 else "")
            try:
                items = list(parse(get(url)))
            except Exception as e:                                             # page absente : catégorie suivante
                print("  ignoré", url, e)
                break
            for t in items:
                t = found.setdefault(t["id"], {**t, "sources": []})
                if src not in t["sources"]:
                    t["sources"].append(src)
            print(f"{src} p{pg} : {len(items)} titres")
            if len(items) < 10:
                break
            time.sleep(0.5)
    tracks = []
    for mid, t in sorted(found.items()):
        if "force" in old.get(mid, {}):                                       # choix manuel conservé
            t["force"] = old[mid]["force"]
        t["use"] = selected(t)
        tracks.append(t)
    LIB.write_text(json.dumps({"license": "Mixkit Stock Music Free License (https://mixkit.co/license/#musicFree)",
                               "source": "https://mixkit.co/free-stock-music/", "tracks": tracks},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(tracks)} titres, {sum(t['use'] for t in tracks)} sélectionnés -> {LIB}")


def fetch(ids):
    sys.path.insert(0, str(ROOT))
    from wooplans.music import ensure_file
    for mid in ids:
        print(ensure_file(int(mid)))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "crawl":
        crawl()
    elif cmd == "fetch":
        fetch(sys.argv[2:])
    else:
        print(__doc__)
