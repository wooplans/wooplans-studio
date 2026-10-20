# Pipeline « visite guidée de plan » (Reels / TikTok / Shorts, 9:16)

Mis à jour le 19 oct. 2026 : **tout tourne sur GitHub, le PC de Tao peut être éteint.**

## Production sans le PC (vue d'ensemble)
```
Claude (cloud)                         GitHub Actions                              Zernio
plan 2D amélioré (PoYo) ─┐
script validé par Tao ───┤  push visite_plan/jobs/<id>/ + RENDER ─▶ visite-render ─▶ visite_plan/out/<id>.mp4 + <id>_thumb.jpg
voix (ElevenLabs) ───────┘                                                          │
                          accord de Tao ─▶ push PUBLISH.json ─────▶ publish-zernio ─▶ Facebook Reel + YouTube Short (programmés)
```
1. **Préparation (Claude, dans le cloud)** : plan amélioré, script, voix, `make_paths`, `sync`, `build_final prep`, `mkseg` → `visite_plan/jobs/<id>/`.
   Fichiers de marque communs (`assets/brand/*.png`, musique « Pop Two » `assets/music/`) : copiés automatiquement dans le job au rendu.
2. **Rendu** : pousser `visite_plan/jobs/<id>/RENDER` (n'importe quel contenu) ou lancer le workflow à la main. Le mode est détecté :
   - `nf.json` → visite sans 3D + hook + CTA (`scene_visite_nf.py`, `scene_bumpers_nf.py`, `bump_local_nf.py`) ;
   - `bump.json` → visite avec 3D + hook + estimation + CTA (`scene_visite.py`, `scene_bumpers.py`, `bump_local.py`) ; le job contient en plus `hook.m4a`, `estim.m4a`, `cta.m4a`, `subs_body.ass` ;
   - sinon → visite simple / format « sans 3D » cloud (segment `CTA` éventuel, `assemble.py`).
   Chaque segment, le hook, l'estimation et le CTA sont rendus **en parallèle** (un job GitHub chacun), puis `render_job.py build` assemble : voix, musique (baisse sous la voix), sous-titres, bande basse, 2 logos filigranes qui se promènent en continu, badge wooplans.com. Sortie : `visite_plan/out/<id>.mp4` + `<id>_thumb.jpg` (vignette 9:16).
3. **Contrôle** (Claude, avant toute publication) : télécharger la vidéo, extraire des images (étage d'un duplex : le plan de l'étage doit s'afficher pendant la visite de l'étage, puis retour au RDC pour les cotes), vérifier sous-titres, zones masquées, valeurs sourcées, aucun « expire ». **Tao valide.**
4. **Publication (seulement sur ordre de Tao)** : pousser `jobs/<id>/PUBLISH.json` → `publish-zernio` : vignette (si absente), vidéo + vignette envoyées à Zernio, post **programmé** (`scheduled_for` + `timezone`) sur Facebook (Reel, couverture = vignette) et YouTube (Short). Idempotent (registre + clé d'idempotence). Les textes passent par `check_copy` ; le lien du catalogue est `https://wooplans.com/catalogue-premium` avec UTM par plateforme (`wooplans/utm.py`).
   **TikTok @wooplans** est connecté à WoopSocial, pas à Zernio : tant qu'il n'est pas reconnecté à Zernio, Claude le publie depuis une session cloud avec le connecteur WoopSocial (la vidéo vient du dépôt, pas du PC).
5. **Vérifier la configuration** : workflow `check-setup` (secrets présents, comptes Zernio, tests).

Standard validé par Tao (V6 + remarques du 13 oct. 2026). Source de vérité des chiffres : le PDF plans + devis du plan.

## Étapes
1. **Entrée** : un dossier avec un ou plusieurs PDF (un PDF peut contenir plusieurs plans) + images de rendu éventuelles. Duplex : RDC + étage.
2. **Plan amélioré** : capture du plan de distribution (pdftoppm -r 300, recadrage), puis règle « plans 2D améliorés » (wooplans-catalog, docs/plans-2d-ameliores/REGLE.md : PoYo gpt-image-2.5-flare, low, 1K, SANS texte, puis étiquettes). **Tao valide le plan avant la vidéo.** Défaut à éviter : pas de pots de fleurs devant une porte / une entrée.
3. **Image du haut** : rendu du dossier, sinon extrait du PDF.
4. **Script de voix off** proposé à Tao (style conversationnel, surfaces arrondies à l'entier, aucune valeur absente du PDF, aucun prix, jamais « l'offre expire »). Chaque pièce est marquée « zoom » ou « sans zoom » (varier, ne pas zoomer partout). Tao corrige.
5. **Préparation (cloud Claude, léger)** : `make_paths.py` (pièces + trajets par les portes, à contrôler visuellement), `make_sync.py` (voix Piper « tom » en test, calage), `align.py` (Whisper, mots), `build_final.py prep` (voix mixée + sous-titres), `mkseg.py` (segments). Tout va dans `jobs/<id>/`.
6. **Rendu : GitHub Actions `visite-render` (aucun PC nécessaire, ≈ 8-16 min)**. Voir « Production sans le PC » ci-dessous. Le PC de Tao n'est plus qu'un secours (`visite_plan/local/`, `python visite_plan/render_job.py local <job> <sortie.mp4>`).
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
Tests : Piper `fr_FR-tom-medium` ou Edge TTS (gratuit). Production : ElevenLabs — « John Mala » (`MLsC4mBTBgYmNigbHkou`, eleven_v4) pour les visites avec 3D, « Diba » (`CHivAFig5q0FuNMEEmFi`) pour les visites sans 3D ; « LeTao » = voix de Tao (avatar). Aucune nouvelle voix (limite de 10).

## Code
Dépôt wooplans/wooplans-studio, dossier `visite_plan/` (scène ManimGX, sync, sous-titres). Secours local : `visite_plan/local/` (installateur + guetteur Windows) — plus nécessaire en fonctionnement normal.

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

## Hook + estimation + CTA + marque (V7 de D5-016 validée le 14 oct. 2026)
Voir le doc de projet « 02_PIPELINE_VISITE_PLAN.md ». Code :
- `scene_bumpers.py` : HookScene / EstimScene / CtaScene (ManimGX, zones sûres : tout texte important au-dessus de ≈ 1500 px).
- `local/bump_local.py` (appelé par `local/run_local.py` si le job contient `bump.json`) : rend les 3 scènes, reconstruit le corps (`body_silent.mp4` + `subs_body.ass` remontés + bande basse, coupe `body_cut` → `body_end`), concatène, applique filigranes + badge wooplans.com.
- `bump_audio.py` : voix (Piper en test), musique Audio as Code, bruitages synthétisés, écrit `bump.json` (repères partagés avec la scène).
- `bump_assets.py` : génère band_bottom.png, badge_url.png, wm_logo.png, wm_tile.png depuis le logo du brand kit (les PNG ne sont pas versionnés).
- `local/RELANCER_GUETTEUR.bat` : relance le guetteur Windows s'il est arrêté.

## Posts images Facebook : lot hebdomadaire (mis en place le 19 oct. 2026)
Objectif : 2 à 3 posts images par jour sur la page Facebook WooPlans, sans travail manuel par post.
- **Source** : `data/plans.json` (55 plans publiés du catalogue au 19 oct. 2026 : chambres, surface, terrain, estimation indicative). À resynchroniser avec le catalogue quand des plans sont ajoutés ou archivés.
  Les rendus sont lus sur la fiche publique `https://www.wooplans.com/catalogue/<slug>` (dossier `/media/public/<code>/`), convertis en JPEG (côté long ≤ 1600 px). Ils portent déjà le filigrane `wooplans.com` du catalogue : aucun second filigrane n'est ajouté (`WATERMARK` dans `tools/image_batch.py`).
- **Rythme** : 3 créneaux par jour (7 h 30, 12 h 30, 19 h, fuseau Africa/Douala) : 1 image, 1 album de 4 rendus, 1 image. Modifiable via `slots` dans `PLAN`.
- **Variété** : les plans les moins publiés passent d'abord, alternance villa / duplex, jamais deux fois le même plan le même jour, un rendu n'est repris qu'après avoir fait le tour du plan, 6 modèles de légende (fiche, question, terrain, budget, enregistrer, partager).
- **Garde-fous** : chaque légende passe par `check_copy` ; seuls les montants de `plans.json` et le prix actuel 39 000 FCFA sont autorisés (libellé « estimation indicative ») ; lien `https://wooplans.com/catalogue-premium` avec UTM `utm_medium=image_organique`, `utm_content=image_<code>`.
- **Procédure** (aucun PC nécessaire) :
  1. Pousser `batches/images/<lot>/PLAN` (`{"start": "2026-10-20", "days": 7, "seed": 1}`) → workflow `image-batch` : `batch.json`, `batch.md` (toutes les légendes), `apercu-N.jpg` (planches). **Rien n'est programmé.**
  2. Tao relit ; retirer un post = `"skip": true` dans `batch.json`, corriger une légende = éditer `caption`.
  3. Après l'accord explicite de Tao : pousser `batches/images/<lot>/APPROVED` → programmation sur Zernio (Facebook), enregistrée dans `registry/videos.json` (format `I`, anti-doublon et idempotent).
- Code : `wooplans/image_posts.py` (choix, légendes), `wooplans/image_tools.py` (JPEG, filigrane, planches), `tools/image_batch.py` (commandes `plan` et `schedule`), tests dans `tests/test_image_posts.py`.

## Format « rendus 3D en vidéo » (prototype du 20 oct. 2026, à valider par Tao)
Reel 9:16 d'environ 24 s fait des rendus du catalogue : plein écran avec travelling lent, musique de fond, **sans voix off**, sous-titres animés (pop, mot clé orange, prix qui s'incrémente), fin « wooplans.com ».
- **Commande** : `python tools/make_reel.py <code> sortie.mp4` (ex. `D4-026`), environ 3 min de calcul. Rendus lus sur la fiche publique ; textes et chiffres de `data/plans.json` (`check_copy`).
- **Scénario** (`wooplans/reel3d.py`) : accroche « Cette maison coûte combien ? », type et chambres, surface et niveaux, terrain (si connu), plan complet + devis, suspense, **estimation indicative** (compteur), « tout est dans le Catalogue Premium », carte finale (prix actuel 39 000 FCFA, lien en description).
- **Musique** : coupes calées sur les mesures (4 temps) de `assets/music/tracks.json`, produit par `tools/analyze_music.py` (librosa, une seule fois par morceau). Un seul morceau pour l'instant (Pop Two, Mixkit) ; pour en ajouter, déposer le MP3 dans `assets/music/`, lancer l'analyse, noter la licence.
- Filigrane anti-piratage « wooplans.com » qui défile du début à la fin (comme les visites), badge en haut à gauche, bande de marque en bas.


### Rendre des reels 3D sur GitHub (sans le PC de Tao)
Pousser `reels/BATCH.txt` (une ligne par plan : `CODE` ou `CODE fichier_musique.mp3`) ou lancer le workflow `reel-render` avec les codes. Un job par plan ; les vidéos sont dans les artefacts du run (`gh run download`). Musique par défaut : « Let's Play Africa » ; « Africa » (Arulo) est aussi installée (tempo plus régulier). Rien n'est programmé sans l'accord de Tao.
