"""Prépare les VSL pour relecture : garde-fous, texte de voix off (LeTao), durées estimées, liens UTM.

usage: python -m vsl.build   -> écrit vsl/SCRIPTS.md et vsl/out/<id>_voix.txt ; code 1 si un garde-fou bloque.
"""
import json
import sys
from pathlib import Path

from wooplans.guardrails import check_copy
from wooplans.settings import FULL_PLANS_FCFA, OFFER_PRICE_FCFA
from wooplans.utm import all_links

HERE = Path(__file__).resolve().parent
WORDS_PER_S = 2.7
# montants sourcés : prix fixes des plans complets et différence après déduction du catalogue
ALLOWED = {*FULL_PLANS_FCFA.values(), *(v - OFFER_PRICE_FCFA for v in FULL_PLANS_FCFA.values())}


def load_scripts():
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((HERE / "scripts").glob("*.json"))]


def problems(script):
    out = []
    for i, b in enumerate(script["beats"], 1):
        for txt in [b["voix"], *b["ecran"]]:
            out += [f"{script['id']} beat {i} : {p}" for p in check_copy(txt, ALLOWED)]
    return out


def voiceover(script):
    return "\n\n".join(b["voix"] for b in script["beats"])


def duration(script):
    return sum(len(b["voix"].split()) / WORDS_PER_S + 0.4 for b in script["beats"]) + 0.8


def main():
    scripts = load_scripts()
    errs = [e for s in scripts for e in problems(s)]
    for e in errs:
        print("BLOQUÉ", e)
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    md = ["# VSL Catalogue Premium : scripts à valider par Tao", "",
          "Voix : ElevenLabs « LeTao ». Rien n'est généré ni programmé avant validation.", ""]
    for s in scripts:
        (out / f"{s['id']}_voix.txt").write_text(voiceover(s) + "\n", encoding="utf-8")
        md += [f"## {s['id']} : {s['titre']}", "", f"*Angle :* {s['angle']}  ",
               f"*Durée estimée :* ≈ {duration(s):.0f} s", "",
               "| # | Voix off | Écran |", "|---|---|---|"]
        for i, b in enumerate(s["beats"], 1):
            md.append(f"| {i} | {b['voix']} | {' / '.join(b['ecran'])} |")
        md += ["", "Liens de suivi :", ""]
        md += [f"- {p} : {u}" for p, u in all_links("V", s["id"]).items()]
        md.append("")
    (HERE / "SCRIPTS.md").write_text("\n".join(md), encoding="utf-8")
    print(f"{len(scripts)} scripts, {len(errs)} problème(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
