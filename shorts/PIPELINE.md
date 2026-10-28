# Shorts « rendus 3D » (YouTube Shorts, Facebook Reels, TikTok, 9:16, ~20 s)

Format validé par Tao le 28 oct. 2026 (essai `jobs/D4-004-S1`) : la maison entière d'abord (fond flou), zoom jusqu'au
plein écran, travelling lent sur 4 rendus d'origine, coupes sur le temps de la musique, « Duplex 4 chambres · 313 m² »
pendant 2 s, fin « Plans et devis de ce modèle sur wooplans.com ». Ni voix, ni sous-titres, ni plan coté.
2 logos semi-transparents qui se promènent du début à la fin.

## Produire
1. **Rendus d'origine** (1920x1080 ou plus, SANS le filigrane du site : les images de wooplans.com font 960 px et portent
   déjà le motif) dans `shorts/rendus/<CODE>/`, la plus belle façade en premier (ordre des noms).
2. `python tools/new_short.py <CODE> [n°]` → `shorts/jobs/<CODE>-S<n>/short.json` (ou `--images a.png b.png ...`).
3. Créer `shorts/jobs/<id>/RENDER` (plusieurs jobs dans le même push = un lot) et pousser → workflow **`short-render`**
   (un rendu par job, en parallèle) → `shorts/out/<id>.mp4`, `<id>_thumb.jpg` (vignette), `<id>.json` (musique utilisée).
   En local : `python tools/make_short.py shorts/jobs/<id>`.
4. Contrôle (planche-contact dans l'artefact du run), **Tao valide**, puis publication (Zernio pour Facebook + YouTube,
   WoopSocial pour TikTok) seulement sur son ordre. Lien : https://wooplans.com/catalogue-premium avec UTM.

## Musique : base Mixkit
- `assets/music/library.json` : ~600 titres Mixkit (licence gratuite, usage commercial, sans attribution), avec
  étiquettes ; `use: true` = sélectionné pour les shorts (positif, entraînant, ≥ 60 s ; pas de Noël, country, rock,
  ambiances tristes ou sombres). Exclure / ajouter un titre à la main : `"force": false` / `"force": true`.
- Rotation automatique (`wooplans/music.py`) : chaque short prend le titre sélectionné le moins utilisé (journal
  `shorts/out/*.json`) ; dans un même lot, jamais deux fois la même musique. Imposer une musique : `"music": "mixkit:<id>"`.
- Workflow **`music-library`** : analyse le tempo des titres sélectionnés (au push de library.json) et parcourt Mixkit
  chaque mois (nouveaux titres). Les mp3 ne sont pas commités : téléchargés à la demande au rendu.
