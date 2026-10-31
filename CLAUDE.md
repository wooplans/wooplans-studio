# WooPlans Studio : instructions pour les agents
Dépôt du pipeline de contenu WooPlans (Facebook, TikTok, YouTube Shorts → Catalogue Premium, 29 000 FCFA, https://wooplans.com/catalogue-premium).
Séparé de Kilabi : aucun fichier, compte, voix ni registre Kilabi ici. Aucun contenu WooPlans sur les comptes Kilabi / Secrets D'ébène.

## Règles
- Devis : toujours celui du site (fiche catalogue : `estimate_total` et lots, data/plans.json), même si le PDF du modèle donne un autre montant (décision de Tao du 31 oct.). Surfaces : tableau des surfaces du PDF du modèle (stockage R2 `private/<code>/*.pdf`). Jamais inventés.
- Dans les vidéos : jamais « l'offre expire dans X heures » ; dire « prix actuel : 29 000 FCFA ». Passer tout texte dans `wooplans.guardrails.check_copy`.
- Lien du catalogue dans toutes les publications : https://wooplans.com/catalogue-premium (avec UTM : `wooplans/utm.py`). Jamais cpbook.wooplans.com. Adresse affichée dans les vidéos : wooplans.com.
- Rien n'est programmé sans l'accord de Tao. Il relit la voix off et les scripts du format B avant GitHub. Une vignette est créée avant tout post (`tools/make_thumbnail.py`).
- Clés API uniquement dans .env / secrets GitHub. Avant tout commit : `python tools/secret_scan.py` (« Aucune fuite »).
- Voix : visites guidées avec 3D = Gradium (voix `TsRKBRWZGYldAeEI`, clé `GRADIUM_API_KEY`, décision de Tao du 31 oct., remplace « John Mala » MLsC4mBTBgYmNigbHkou) ; visites sans 3D = « Diba » (CHivAFig5q0FuNMEEmFi, validée le 18 oct. tant que LeTao est refusée par l'abonnement) ; « LeTao » = voix de Tao. Aucune nouvelle voix perso (limite 10). Images : Poyo gpt-image 2.5, low, 1K.
- Filigranes anti-piratage : 2 logos semi-transparents qui se promènent en continu, du début à la fin (décision du 16 oct.).
- Réponses à Tao en français, concises.

## Production SANS le PC de Tao (tout est sur GitHub)
- Rendu : workflow `visite-render` (pousser `visite_plan/jobs/<id>/RENDER`) → `visite_plan/out/<id>.mp4` + vignette. Modes détectés : `nf.json`, `bump.json`, sinon simple. Point d'entrée : `visite_plan/render_job.py`.
- Publication : workflow `publish-zernio` (pousser `jobs/<id>/PUBLISH.json`, SEULEMENT après l'accord de Tao) → Facebook Reel + YouTube Short programmés. TikTok @wooplans est sur WoopSocial (connecteur), pas sur Zernio.
- YouTube « Présentation de plan » (16:9, ~8 min) : workflow `youtube-render` (pousser `youtube_plan/jobs/<id>/RENDER`) → artefact mp4 + planche-contact à contrôler. Procédure : `youtube_plan/PIPELINE.md`.
- Vérification : workflow `check-setup`. Procédure complète : `visite_plan/PIPELINE.md`. Secrets : `SECRETS.md`.
- Le PC de Tao n'est qu'un secours (`visite_plan/local/`).

Tests : `python -m pytest -q tests`.
