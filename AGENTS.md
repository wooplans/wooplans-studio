# WooPlans Studio : instructions pour les agents
Dépôt du pipeline de contenu WooPlans (Facebook, TikTok, YouTube Shorts → Catalogue Premium, 39 000 FCFA, https://cpbook.wooplans.com/digital).
Séparé de Kilabi : aucun fichier, compte, voix ni registre Kilabi ici. Aucun contenu WooPlans sur les comptes Kilabi / Secrets D'ébène.

## Règles
- Prix, surfaces, devis : uniquement ceux du PDF plans + devis (data/plans.json). Jamais inventés.
- Dans les vidéos : jamais « l'offre expire dans X heures » ; dire « prix actuel : 39 000 FCFA ». Passer tout texte dans `wooplans.guardrails.check_copy`.
- Rien n'est programmé sans l'accord de Tao. Il relit la voix off et les scripts du format B avant GitHub.
- Clés API uniquement dans .env / secrets GitHub. Avant tout commit : `python tools/secret_scan.py` (« Aucune fuite »).
- Voix : ElevenLabs « LeTao » uniquement, aucune nouvelle voix. Images : Poyo gpt-image 2.5, low, 1K.
  Exception validée par Tao (18 oct. 2026) : tant que l'abonnement ElevenLabs refuse LeTao (voix clonée), voix « Diba » (CHivAFig5q0FuNMEEmFi) pour les visites.
- Visites guidées de plan (avec ou sans 3D) : suivre visite_plan/PIPELINE.md (format « visite sans 3D » = job modèle V2-2CH-01).
- Réponses à Tao en français, concises.
Tests : `python -m pytest -q tests`.
