# Shorts « rendus 3D » (YouTube Shorts, Facebook Reels, TikTok, 9:16, ~20 s)

Format validé par Tao le 28 oct. 2026 (essai `jobs/D4-004-S1`) : la maison entière d'abord (fond flou), zoom jusqu'au
plein écran, travelling lent sur 4 rendus d'origine, coupes sur le temps de la musique, « Duplex 4 chambres · 313 m² »
pendant 2 s, fin « Plans et devis de ce modèle sur wooplans.com ». Ni voix, ni sous-titres, ni plan coté.
2 logos semi-transparents qui se promènent du début à la fin.

## Produire (Tao donne seulement les codes ou le type)
1. Tao, dans la conversation : « fais les shorts de D4-004 et V3-022 », « tous les V4 », « les duplex qui n'en ont pas ».
2. Claude écrit la sélection dans **`shorts/BATCH.txt`** et pousse → workflow **`short-render`** (ou Actions > Run workflow,
   champ `selection`) : `D4-004 V3-022`, `V4`, `villa`, `duplex`, `tous`, + `nouveaux` = seulement les modèles sans
   short ; 40 shorts au plus par lot.
3. Pour chaque modèle, en parallèle : nouveau job `shorts/jobs/<CODE>-S<n>/`, **rendus d'origine pris dans R2** par le
   serveur MCP du site (`list_plan_files` → couverture d'abord puis 3 rendus répartis sur la galerie ; originaux
   absents ou portant la pastille du site écartés), musique choisie dans la base Mixkit, vidéo + vignette.
   Secret GitHub requis : `WOOPLANS_MCP_TOKEN` (voir SECRETS.md).
4. Sorties commitées : `shorts/out/<id>.mp4`, `<id>_thumb.jpg`, `<id>.json` (musique) et `shorts/jobs/<id>/short.json`
   (clés R2 des rendus utilisés). Claude contrôle et envoie les vidéos à Tao.
5. **Tao valide**, puis publication (Zernio : Facebook + YouTube ; WoopSocial : TikTok) seulement sur son ordre.
   Lien : https://wooplans.com/catalogue-premium avec UTM.

Relancer un job (autre musique, correction) : pousser `shorts/jobs/<id>/RENDER` ou champ `jobs`. En local :
`python tools/new_short.py <CODE>` (R2 si WOOPLANS_MCP_TOKEN dans .env, sinon `shorts/rendus/<CODE>/` ou `--images`)
puis `python tools/make_short.py shorts/jobs/<id>`.

## Musique : base Mixkit
- `assets/music/library.json` : ~600 titres Mixkit (licence gratuite, usage commercial, sans attribution), avec
  étiquettes ; `use: true` = sélectionné pour les shorts (positif, entraînant, ≥ 60 s ; pas de Noël, country, rock,
  ambiances tristes ou sombres). Exclure / ajouter un titre à la main : `"force": false` / `"force": true`.
- Rotation automatique (`wooplans/music.py`) : chaque short prend le titre sélectionné le moins utilisé (journal
  `shorts/out/*.json`) ; dans un même lot, jamais deux fois la même musique. Imposer une musique : `"music": "mixkit:<id>"`.
- Workflow **`music-library`** : analyse le tempo des titres sélectionnés (au push de library.json) et parcourt Mixkit
  chaque mois (nouveaux titres). Les mp3 ne sont pas commités : téléchargés à la demande au rendu.
