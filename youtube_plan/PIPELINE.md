# Vidéo YouTube « Présentation de plan » (16:9, ~8 min) : 100 % GitHub

Validé le 27 oct. : rendu de D4-004 sur GitHub = identique à la version PC (494,7 s, 195,7 Mo, -16,5 LUFS).

## Structure
- `engine/` : moteur commun (`common.py`, `widgets.py`, `visitelib.py`, `drive.py`, `run_chunk.py`, `mix.py`, `assemble.py`). Aucun chemin en dur : `YT_JOB` (dossier du job) et `YT_OUT` (sortie).
- `jobs/<id>/` : `code/` (seq_*.py + script.py : propre au modèle : pièces, polygones, chiffres, ancrages), `assets/` (rendus R0..R9, plans 3D/2D, jingle, segment catalogue, logos, polices, vignette), `voix/` (<seq>.wav + .chunks.json), `JOB.json`, `RENDER`.
- Musique : `assets/music` (pistes B, C, D du mixage).

## Rendre
Pousser `youtube_plan/jobs/<id>/RENDER` (modifier son contenu) → workflow `youtube-render` : 10 shards parallèles → assemblage + audio + planche-contact → artefact `youtube-<id>` (14 jours). Aucune publication automatique.
Contrôle obligatoire : ouvrir la planche-contact (`*_planche.jpg`) et vérifier toute la vidéo avant d'envoyer à Tao.

## Nouveau modèle
Copier `jobs/D4-004` → `jobs/<nouvel id>`, adapter `code/seq_*.py`/`script.py`, régénérer les voix (`code/gtts.py`, `gen_all.py`), remplacer R*.png, plans, vignette. Règles : pas de prix catalogue ni nombre de plans, jamais « l'offre expire », pas de sous-titres, image jamais déformée, rien d'opaque sur la maison, afficher chaque rendu R avec son numéro avant de l'associer au script.
## Publication
Seulement après l'accord de Tao (Zernio `posts_create`, YouTube @wooplans). Vignette et écran de fin : Tao, dans YouTube Studio.
