# Campagne « Catalogue Premium à froid » (VSL) — Côte d'Ivoire et Guinée

Demande de Tao (25 nov. 2026) : vendre directement le Catalogue Premium (39 000 FCFA) à froid grâce à la VSL,
CI + GN, hommes de 35 ans et plus, 15 $/jour, 7 visuels pour voir lesquels convertissent. Rien n'est publié sans son accord.

## Réglages (brouillon Mymusika)

| | |
|---|---|
| Campagne | 52620342537693 · Ventes · 15 $/jour (budget de campagne) |
| Ensemble de pubs | 52620342543293 · CI + GN · hommes 35-65 ans (ciblage strict, demande de Tao) · optimisé sur Achat (pixel du site) |
| Destination | https://www.wooplans.com/catalogue-premium (VSL en héro, après fusion de la PR #155) |
| Suivi | `utm_source=facebook&utm_medium=paid_social&utm_campaign=catalogue_vsl_ci_gn&utm_content=<modèle>` |
| Pubs | 7 visuels (gabarit `visuels/gabarit.html`) : V3-017, V4-005, D5-012, V4-036, V4-032, D4-034, D4-026 |

## Textes (passés dans `check_copy`)

**Texte principal 1**
> Vous avez un terrain ? Avant de payer un architecte, choisissez la maison qui va dessus.
> Le Catalogue Premium WooPlans : 100 villas et duplex, avec le plan coté de chaque maison, le devis de construction poste par poste et la taille de terrain qu'il faut.
> Prix actuel : 39 000 FCFA, paiement unique, accès immédiat sur votre téléphone.
> 👉 Regardez la vidéo de 5 minutes sur la page.

**Texte principal 2**
> Un architecte vous fera 2 ou 3 propositions, et chacune se paie. Avec le Catalogue Premium, vous comparez 100 maisons chez vous, en famille, avec le devis de chacune.
> Prix actuel : 39 000 FCFA. Remboursé sous 7 jours si le catalogue ne vous convient pas.

**Texte principal 3**
> Votre terrain attend. Quelle maison allez-vous y construire ?
> Villas et duplex de 3 à 5 chambres, plans cotés et devis poste par poste, dans un seul catalogue. Prix actuel : 39 000 FCFA, accès immédiat.

**Titres** : « Vous avez un terrain ? » · « 100 maisons avec leur devis » · « Catalogue Premium · 39 000 FCFA »
**Bouton** : Acheter

## Mesure de la VSL (page de vente)

- PostHog : `vsl_preview_play` (aperçu muet affiché), `vsl_open`, `vsl_play`, `vsl_progress` (10, 25, 50, 75, 95 %), `vsl_end`,
  `vsl_close` (secondes réellement regardées, % max), `vsl_cta` (bouton d'achat en fin de vidéo).
- Base du site : table `video_events`, vidéo `vsl-public` (open, play, half, end, cta).
- Pixel Meta : `VSL_50` et `VSL_95` → audiences de reciblage « a regardé la moitié / la fin de la VSL ».

## Brouillons (25 nov. 2026, non publiés)

7 pubs dans l'ensemble 52620342543293 : V3-017, V4-005, D5-012, V4-036, V4-032, D4-034, D4-026.
Visuels servis par le site : https://www.wooplans.com/assets/pubs/catalogue/catalogue-<modèle>.jpg (PR wooplans #155).
Bouton « Acheter maintenant », 3 textes et 3 titres par pub (Meta choisit).

## Pubs vidéo « 100 plans » (25 nov. 2026, publiées avec l'accord de Tao)

Anciennes vidéos C et D (présentateur avec le livre) : phrases « 50 plans » coupées, couverture passée à « 100 PLANS DE MAISON »
plan par plan sur Runware (P-Video-Edit avec la couverture en référence, FLUX Video Edit fast sur les plans difficiles), ≈ 2,1 $.
« en promotion » gardé à la fin (choix de Tao).

| Pub | Ad ID | Vidéo Meta | Lien |
|---|---|---|---|
| Vidéo C · 100 plans · sous-titrée (17 s) | 52620381717093 | 1493448875994256 | `utm_content=video-C` |
| Vidéo D · 100 plans · sous-titrée (25 s) | 52620381724693 | 1683704220124194 | `utm_content=video-D` |

Sous-titres style Hormozi incrustés (Inter Display Black, majuscules, contour noir, mot prononcé en jaune), demande de Tao :
« le sous titre est important dans les vidéo de pub ». Les 2 premières versions sans sous-titres (52620379131493, 52620379140493)
ont été supprimées à sa demande. Même ensemble de pubs (52620342543293), mêmes 3 textes et 3 titres, bouton « Acheter »,
vignette = image du livre « 100 ».
