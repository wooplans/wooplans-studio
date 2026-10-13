# Pipeline « visite guidée de plan » (Reels / TikTok / Shorts, 9:16)

Standard validé par Tao (V6 + remarques du 13 oct. 2026). Source de vérité des chiffres : le PDF plans + devis du plan.

## Étapes
1. **Entrée** : un dossier avec un ou plusieurs PDF (un PDF peut contenir plusieurs plans) + images de rendu éventuelles. Duplex : RDC + étage.
2. **Plan amélioré** : capture du plan de distribution (pdftoppm -r 300, recadrage), puis règle « plans 2D améliorés » (wooplans-catalog, docs/plans-2d-ameliores/REGLE.md : PoYo gpt-image-2.5-flare, low, 1K, SANS texte, puis étiquettes). **Tao valide le plan avant la vidéo.** Défaut à éviter : pas de pots de fleurs devant une porte / une entrée.
3. **Image du haut** : rendu du dossier, sinon extrait du PDF.
4. **Script de voix off** proposé à Tao (style conversationnel, surfaces arrondies à l'entier, aucune valeur absente du PDF, aucun prix, jamais « l'offre expire »). Chaque pièce est marquée « zoom » ou « sans zoom » (varier, ne pas zoomer partout). Tao corrige.
5. **Préparation (cloud Claude, léger)** : `make_paths.py` (pièces + trajets par les portes, à contrôler visuellement), `make_sync.py` (voix Piper « tom » en test, calage), `align.py` (Whisper, mots), `build_final.py prep` (voix mixée + sous-titres), `mkseg.py` (segments). Tout va dans `jobs/<id>/`.
6. **Rendu : sur le PC de Tao (méthode par défaut, ≈ 75 s)**. Jamais dans le cloud Claude. Un guetteur Windows surveille `C:\Users\Dell\Documents\VIDEO AUTO\WOOPLANS\_rendu_auto\jobs\`. Claude dépose `jobs/<id>/` (plan.png, facade.png, paths.json, sync.json, segments.json, meta.json, voice_mix.m4a, subs.ass) puis un fichier `RENDER_PC` en dernier : la vidéo `<id>.mp4` sort toute seule dans ce dossier (marqueurs `DONE` / `ERREUR`, journal `watch.log`). Réglage clé : **2 rendus simultanés maximum** (le PC a 7,7 Go de RAM ; 6 en parallèle = 523 s, 2 = 73 s). Un `<id>` déjà rendu (`DONE`) ne se relance pas : utiliser un nouvel id. Secours : GitHub Actions `visite-render` (10 à 18 min, lent).
7. **Livraison** : copier dans le dossier de Tao ET envoyer dans la conversation.

## Standard visuel
- Façade fixe en haut, bande verte d'une ligne (nom du plan + chambres), zone plan animée sur fond BLANC.
- Voile orange translucide sur la pièce courante, rien n'assombrit le reste. Point vert pulsant avec traînée, uniquement par les portes/ouvertures.
- Voix continue (pas de silence) ; le point s'arrête pile quand la voix dit le nom de la pièce. Ordre : on entre par la Terrasse 1.
- Zoom variable (champ `zoom` du script). Fin : **zoom arrière** sur toute la maison (cotes bien visibles, pas au bord de l'écran) puis tracé des cotes profondeur et façade (du PDF), calés sur la voix.
- Sous-titres : un mot à la fois, surfaces en deux mots (« 27 m² », en orange), Poppins Bold blanc, contour vert #0F5B59.

## Job (`jobs/<id>/`)
`plan.png` (plan amélioré + marges pour les cotes), `facade.png`, `paths.json`, `sync.json`, `segments.json`, `meta.json` (bande, ratio façade, murs extérieurs en px, cotes), `voice_mix.m4a`, `subs.ass`, `RENDER_PC` (PC) ou `RENDER` (GitHub).

## Voix
Tests : Piper `fr_FR-tom-medium` (gratuit, téléchargé depuis huggingface.co/rhasspy/piper-voices). Production : ElevenLabs « LeTao » uniquement.

## Code
Dépôt wooplans/wooplans-studio, dossier `visite_plan/` (scène ManimGX, sync, sous-titres). Pack local : `visite_plan/local/` (installateur + guetteur Windows, déjà installé sur le PC de Tao).
