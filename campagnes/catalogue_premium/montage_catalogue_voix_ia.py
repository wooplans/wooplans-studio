"""Vidéo « Catalogue Premium » (9:16) avec une voix ElevenLabs à la place de la voix de Tao (demande de Tao, 23 nov. 2026).

Mêmes images que montage_catalogue.py (plans de Tao déjà découpés dans MEDIA/work), mêmes témoignages (voix des clients
gardées), carte de fin SANS prix (le prix est affiché sur chaque page : 39 000 public, 29 000 réservé).
Voix : ElevenLabs « Gerome - Casual » (Sn8JtaVEizNFwv6xaCCV, eleven_v4), choisie par Tao pour la VSL ; fichiers dans MEDIA/voix.
La voix de Tao est retirée des plans (piste remplacée par la voix générée, la musique reste).

Usage : python campagnes/catalogue_premium/montage_catalogue_voix_ia.py [MEDIA] → MEDIA/out/catalogue-premium-voix-ia.mp4
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import montage_catalogue as m  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from wooplans.guardrails import check_copy  # noqa: E402

VOIX = m.MEDIA / "voix"
W = m.WORK

# Groupes de plans (même étiquette) : un texte lu par groupe. (plans, étiquette, texte lu = sous-titre)
GROUPES = [
    ([0], "Le Catalogue Premium", "Voici le Catalogue Premium : une collection de cent plans de maisons."),
    ([1, 2], "Rendus 3D", "Pour chaque plan, vous avez les images de rendu en 3D."),
    ([3], "Plan de distribution coté", "Le plan de distribution, avec les dimensions de chaque pièce."),
    ([4], "Devis par lot", "Et le devis par lot : la fondation, l'élévation, la dalle… jusqu'aux finitions, avec le coût total de la maison."),
    ([5], "Duplex et villas", "D'un côté, les plans de duplex. De l'autre, les plans de villas."),
    ([6], "Pour choisir votre maison", "C'est le document idéal pour choisir votre maison et lancer votre projet de construction."),
    ([7, 8, 9], "Version numérique", "Ça, c'est le document imprimé. Voici la version numérique du même catalogue : tous les plans, directement sur votre téléphone. Vous parcourez les images de chaque modèle."),
    ([10], "Plan coté sur téléphone", "Le plan de distribution de chaque modèle, avec ses dimensions."),
    ([11], "Devis sur téléphone", "Et le devis de chaque modèle, toujours sur votre téléphone."),
    ([12], "Nouveaux plans inclus", "Nous ajoutons régulièrement de nouveaux plans, et vous y avez accès, sans rien payer de plus."),
]
INTRO = "Voici quelques témoignages de personnes qui ont acheté notre Catalogue Premium."
FIN = "Le Catalogue Premium : paiement unique, accès à vie. Rendez-vous sur wooplans.com."
FIN_D = 7.0
# Texte du sous-titre de la carte « témoignages », tel que montage_catalogue.render() l'écrit.
INTRO_SUB = "Voici quelques témoignages de personnes qui ont acheté notre Catalogue Premium"


def duree(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)


def groupe(g, plans):
    """Plans du groupe (image seule) + voix générée posée à 0,3 s ; la vidéo s'allonge (dernière image figée) si la voix dépasse."""
    lst = W / f"ia_g{g}.txt"
    lst.write_text("".join(f"file '{W / f'c{i:02d}.mp4'}'\n" for i in plans))
    vid = W / f"ia_g{g}_v.mp4"
    m.ff("-f", "concat", "-safe", "0", "-i", lst, "-an", "-c:v", "copy", vid)
    voix = VOIX / f"g{g}.mp3"
    d = max(duree(vid), duree(voix) + 0.8)
    out = W / f"ia_g{g}.mp4"
    m.ff("-i", vid, "-i", voix,
         "-filter_complex", f"[0:v]tpad=stop_mode=clone:stop_duration=5,trim=0:{d:.3f},setpts=PTS-STARTPTS[v];"
                            f"[1:a]{m.AUD},adelay=300|300,apad,atrim=0:{d:.3f}[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{d:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out)
    return out, d


def main():
    problems = [p for t in [x[2] for x in GROUPES] + [INTRO, FIN] for p in check_copy(t)]
    if problems:
        raise SystemExit(f"Texte refusé : {problems}")
    seg = {}
    clips = []
    for g, (plans, label, texte) in enumerate(GROUPES):
        seg[("c", g)] = groupe(g, plans)
        clips.append((None, 0, 0, label, texte))
    m.CLIPS = clips  # render() lit l'étiquette et le sous-titre de chaque plan ici
    # Sous-titres calés sur la voix (qui commence à 0,3 s), pas sur toute la durée du plan.
    voix = {texte: duree(VOIX / f"g{g}.mp3") for g, (_p, _l, texte) in enumerate(GROUPES)}
    voix[INTRO_SUB] = duree(VOIX / "intro.mp3")
    orig = m.sub_chunks
    m.sub_chunks = lambda sub, a, b, *r: orig(sub, a + 0.25, min(b, a + 0.3 + voix[sub]), *r) if sub in voix else orig(sub, a, b, *r)
    p = W / "ia_intro.mp4"; m.card_video(W / "temo.jpg", VOIX / "intro.mp3", p, 6.0); seg[("ti",)] = (p, 6.0)
    for k in range(len(m.TEMO)):
        t = W / f"t{k}.mp4"; seg[("t", k)] = (t, duree(t))
    p = W / "ia_fin.mp4"; m.card_video(W / "fin-sans-prix.jpg", VOIX / "fin.mp3", p, FIN_D); seg[("fin",)] = (p, FIN_D)
    seq = [("c", g) for g in range(len(GROUPES))] + [("ti",)] + [("t", k) for k in range(len(m.TEMO))] + [("fin",)]
    m.render("catalogue-premium-voix-ia", seq, seg)


if __name__ == "__main__":
    main()
