# WooPlans Studio : instructions pour les agents
Dépôt du pipeline de contenu WooPlans (Facebook, TikTok, YouTube Shorts → Catalogue Premium, 39 000 FCFA, https://wooplans.com/catalogue-premium).
Séparé de Kilabi : aucun fichier, compte, voix ni registre Kilabi ici. Aucun contenu WooPlans sur les comptes Kilabi / Secrets D'ébène.

## Règles
- Prix, surfaces, devis : uniquement ceux du PDF plans + devis (data/plans.json). Jamais inventés.
- Dans les vidéos : jamais « l'offre expire dans X heures » ; dire « prix actuel : 39 000 FCFA ». Passer tout texte dans `wooplans.guardrails.check_copy`.
- Lien du catalogue dans toutes les publications : https://wooplans.com/catalogue-premium (avec UTM : `wooplans/utm.py`). Jamais cpbook.wooplans.com. Adresse affichée dans les vidéos : wooplans.com.
- Rien n'est programmé sans l'accord de Tao. Il relit la voix off et les scripts du format B avant GitHub. Une vignette est créée avant tout post (`tools/make_thumbnail.py`).
- Clés API uniquement dans .env / secrets GitHub. Avant tout commit : `python tools/secret_scan.py` (« Aucune fuite »).
- Voix : présentations avec 3D = ElevenLabs « John Mala » (MLsC4mBTBgYmNigbHkou, eleven_v4, décision de Tao du 14 oct.) ; visites sans 3D = « Diba » (CHivAFig5q0FuNMEEmFi, validée le 18 oct. tant que LeTao est refusée par l'abonnement) ; « LeTao » = voix de Tao. Aucune nouvelle voix perso (limite 10). Images : Poyo gpt-image 2.5, low, 1K.
- Filigranes anti-piratage : 2 logos semi-transparents qui se promènent en continu, du début à la fin (décision du 16 oct.).
- Réponses à Tao en français, concises.

## Production SANS le PC de Tao (tout est sur GitHub)
- Rendu : workflow `visite-render` (pousser `visite_plan/jobs/<id>/RENDER`) → `visite_plan/out/<id>.mp4` + vignette. Modes détectés : `nf.json`, `bump.json`, sinon simple. Point d'entrée : `visite_plan/render_job.py`.
- Publication : workflow `publish-zernio` (pousser `jobs/<id>/PUBLISH.json`, SEULEMENT après l'accord de Tao) → Facebook Reel + YouTube Short programmés. TikTok @wooplans est sur WoopSocial (connecteur), pas sur Zernio.
- YouTube « Présentation de plan » (16:9, ~8 min) : workflow `youtube-render` (pousser `youtube_plan/jobs/<id>/RENDER`) → artefact mp4 + planche-contact à contrôler. Procédure : `youtube_plan/PIPELINE.md`.
- Vérification : workflow `check-setup`. Procédure complète : `visite_plan/PIPELINE.md`. Secrets : `SECRETS.md`.
- Le PC de Tao n'est qu'un secours (`visite_plan/local/`).

Tests : `python -m pytest -q tests`.

## Pubs Meta : envoyer une vidéo (méthode décidée par Tao le 12 nov. 2026)
L'envoi direct de fichiers vers Meta (`ads_create_upload_url`) n'est pas ouvert sur le compte publicitaire : ne pas le redemander à Tao, passer par le site.
1. Copier le `.mp4` dans `public/ads/` du dépôt `wooplans/wooplans` (nom sans espaces), pousser, ouvrir la PR et la fusionner une fois le contrôle `check` réussi (accord donné par Tao pour cette méthode). Après le déploiement, le fichier est servi sur `https://www.wooplans.com/ads/<fichier>.mp4` : vérifier 200 et `video/mp4`.
2. Envoyer à Meta depuis cette adresse : `ads_creative_upload_media` avec `upload_source=URL`, `media_type=VIDEO`. Attendre le statut `ready` (`ads_get_ad_videos`), puis créer le créatif (vignette = un visuel du compte, `image_hash`) et l'annonce.
3. Retirer les fichiers de `public/ads/` par une seconde PR dès que la vidéo est `ready` chez Meta.
Les annonces sont créées en pause ; on ne les active qu'avec l'accord explicite de Tao.
