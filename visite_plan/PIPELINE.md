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

## Format « visite sans 3D » (validé par Tao le 18 oct. 2026, job modèle : `jobs/V2-2CH-01`)
Pour un plan seul (image 2D, sans rendu 3D ni PDF). Vidéo 9:16 d'environ 53 s.

1. **Plan** : image fournie par Tao. Retouche locale (pas de Poyo, pour garder la géométrie exacte) : fond blanc, objets parasites retirés (règle…), étiquettes en français en Poppins Bold bleu. Tao valide le plan.
2. **Script** (Tao valide) : une phrase par pièce, champ `zoom` alterné, **aucun chiffre sans PDF** (ni surface, ni cote, ni prix). « WC » se dit « toilette ». Ordre : entrée par la véranda, pièces de jour, service, chambres. La visite **s'arrête à la chambre parentale**, puis segment `CTA` : « Envie de découvrir d'autres plans ? Rendez-vous sur wooplans point com ! ».
3. **Trajets** : `jobs/<id>/make_paths.py` (polygones + trajets par les portes) → `paths_check.png` à contrôler.
4. **Voix** : ElevenLabs, une prise par segment (`eleven_multilingual_v2`). LeTao est refusée par l'abonnement actuel (voix clonée) : **Diba** (`CHivAFig5q0FuNMEEmFi`), choisie par Tao, en attendant.
5. **Synchro sans Whisper** (Hugging Face bloqué dans le cloud Claude) : dans le dossier de travail, `voix/sync/NN.wav` (silences de bord retirés) + `voix/script.json` (champ `sub` = texte des sous-titres, vide pour le CTA), puis
   `python visite_plan/sync_audio.py` → `python visite_plan/build_final.py prep --wm --band` ; copier `voix/sync.json`, `final/voice_mix.m4a`, `final/subs.ass` dans le job ; `python visite_plan/mkseg.py jobs/<id>`.
6. **Job** : `meta.json` = `{"band": "Villa · 2 chambres", "facade": false, "plan_px": [w, h], "bottom_px": 440}` ; `cta_logo.png` (logo blanc), `wm_logo.png` (filigrane fixe, vert ~19 %), `band.png` (bande du bas 1080×440 : logo + « Tous nos plans sur » + bouton wooplans.com, contenu dans les 200 px du haut pour rester visible sous l'interface Reels/Shorts/TikTok).
7. **Rendu** : GitHub Actions `visite-render`, déclenché en poussant `jobs/<id>/RENDER` sur une branche `ccr-*` (≈ 5 min, la vidéo revient dans `visite_plan/out/<id>.mp4`). Le PC de Tao n'a pas encore la version « sans 3D » de la scène.
8. **Montage** (automatique au rendu) : filigrane fixe en fond, « wooplans.com » qui défile, bande verte du bas, sous-titres au-dessus de la bande ; tout disparaît pendant le CTA (fond vert, logo, accroche, bouton cliqué, « Lien en description »).
9. **Publication** (après accord de Tao) : `jobs/<id>/PUBLISH.json` (date locale + `timezone`, légende Facebook, titre/description YouTube, lien wooplans.com avec UTM via `wooplans.utm.build_link(..., base="https://wooplans.com/")`), poussé → workflow `publish-zernio` (`tools/publish_zernio.py` : comptes WooPlans seulement, `check_copy`, registre). **Prérequis manquants au 18 oct.** : secret GitHub `ZERNIO_API_KEY` (et `ZERNIO_PROFILE_ID`), TikTok @wooplans à connecter dans Zernio. Facebook Story : à ajouter (`contentType: "story"`, sans légende).

### Plans « style WooPlans » et pièces précises (19 oct. 2026)
Chaque job a un `redraw_job.py` (relancer après toute retouche) qui produit `plan.png`, `paths.json` et `paths_check.png` :
- `tools/redraw.py` : plan **redessiné** (fond blanc, murs noirs d'épaisseur constante, fenêtres bleues en façade, portes avec battant,
  sols par type de pièce, mobilier du plan source en gris, étiquettes Inter Bold) à partir des polygones des pièces et des portes
  relevés sur le plan source (`auto_gaps=False` + `portes=` pour les captures floues ou les croquis) ; ou plan source **conservé**
  (`keep_src=True`) quand il est déjà au style (rendu réaliste), avec étiquettes refaites et pièces détectées par remplissage
  entre les murs (`seed`, `box` pour les pièces ouvertes, `closures` / `openings` pour les murs mal détectés).
- Trajet du point : plus court chemin dans la maison, hors des murs, donc par les portes (`tools/restyle.shortest_path`).
- Contrôler `paths_check.png` : un voile par pièce collé aux murs, aucun trajet à travers un mur.
