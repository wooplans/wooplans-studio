# Campagne Facebook : Guide WooPlans des maisons (1 900 FCFA)

Scripts et textes : `pubs.py` (contrôlés par `tests/test_guide_ads.py` avec `check_copy`).
Rien n'est lancé sans l'accord de Tao. Page de destination : https://wooplans.com/guide-des-maisons
(lien avec UTM : `pubs.ad_link("<angle>")`).

## Objectif du test (14 jours, 25 $/jour max)

Prouver qu'un acheteur du guide coûte **au plus 1 900 FCFA** de pub. Si c'est le cas, l'acquisition se finance
seule et le budget peut monter sans perte.

| Indicateur | Cible | Seuil d'alerte |
|---|---|---|
| Coût par achat du guide | ≤ 1 900 FCFA | > 3 000 FCFA après 7 jours |
| CTR (lien) | ≥ 1,5 % | < 0,8 % |
| Conversion de la page | ≥ 5 % des visiteurs | < 2 % |
| Réponses aux 3 questions | ≥ 50 % des acheteurs | < 30 % |
| Guide → Catalogue Premium | 5 à 15 % sur 14 jours | < 3 % |

## Structure

- 1 campagne « Ventes », optimisation **Achat** (évènement Purchase du guide).
- 1 seul ensemble de publicités, ciblage large (Advantage+), 28–55 ans, Cameroun en premier
  (puis les autres pays une fois le coût par achat connu).
- 5 vidéos (angles ci-dessous) + 3 textes principaux + 3 titres : Meta combine.
- Pas de modification pendant les 3 premiers jours (phase d'apprentissage).

## Règles de coupe

- Jour 4 : couper toute pub qui a dépensé ~5 700 FCFA (3 × le prix) sans aucun achat.
- Jour 7 : si le coût par achat dépasse 3 000 FCFA, changer les vidéos ou la page, pas le budget.
- Une pub sous 1 900 FCFA par achat : dupliquer son angle (nouvelle accroche, même idée).

## Les 5 angles

| id | Accroche (3 premières secondes) |
|---|---|
| budget | « Avec votre budget, quelle maison pouvez-vous vraiment construire ? J'ai fait la liste. » |
| terrain | « Vous avez un terrain de 300 mètres carrés ? Voici ce que vous pouvez construire dessus. » |
| telephone | « J'ai mis 100 maisons dans ce guide, avec le budget de chacune. » |
| avant_architecte | « Avant de payer un architecte, faites ceci : choisissez votre modèle et connaissez votre budget. » |
| villa_duplex | « Même budget : une villa de 5 chambres ou un duplex de 4 chambres ? Regardez la différence. » |

## Tournage (Tao, face caméra)

- Format 9:16, lumière de face, son propre (micro-cravate si possible).
- Le **guide sur le téléphone** (PDF qui défile), jamais le livre imprimé : le livre est le Catalogue Premium,
  montré seulement après l'achat (vidéo de la page de remerciement).
- Sous-titres incrustés ; le texte à l'écran est dans `on_screen`.
- Fin de chaque vidéo : « Le guide est à 1 900 FCFA sur wooplans.com. »
- Avant envoi : vignette (`tools/make_thumbnail.py`) et relecture de Tao.
- Les chiffres des exemples (V3-027, D4-002, V5-006) viennent des fiches publiques du 14 nov. 2026 :
  à revérifier si une fiche change.

## Vidéo de la page de remerciement (Catalogue Premium imprimé)

« Vous avez le guide. Voici le catalogue complet. » Tao feuillette le livre, ouvre un modèle : rendus, plan
coté, devis poste par poste. Il précise que l'acheteur reçoit **la version numérique** (espace en ligne + fiches PDF).
Prix plein : 29 000 FCFA, sans réduction ni compte à rebours.

## Visuels prêts (dossier `creas/`, 1080×1350, Poyo gpt-image-2.6-fixed, logo officiel incrusté)

Modèles retenus (chiffres du site, 14 nov. 2026) : les plus achetés (D5-012 ×3, V4-005 ×2, V3-017 ×2, V4-036,
V4-032, D4-034…) puis les plus vus en organique (V3-037, V4-036, V3-014, V4-032, D4-040…).

| Fichier | Angle |
|---|---|
| crea-1-budget.jpg | Budget (V3-017 : 120 m², 17,3 à 21,1 M FCFA) |
| crea-2-terrain-350.jpg | Terrain 350 m² (D5-012 : 5 chambres, 234 m²) |
| crea-3-villa-ou-duplex.jpg | Villa V4-036 ou duplex D4-040, même budget |
| crea-4-guide-telephone.jpg | 100 maisons dans votre téléphone (V3-037, V4-005, D5-012, V4-032) |
| crea-5-avant-architecte.jpg | Avant de payer un architecte (V4-005) |
| crea-6-preferees-clients.jpg | Les maisons préférées de nos clients, avec leur budget |
| video-guide-9x16-voix.mp4 | 28 s : accroche, V3-017, D5-012, guide sur le téléphone, montage, écran final ; voix « John Mala », musique Mixkit, sous-titres, 2 filigranes animés (`tools/make_guide_ad.py`) |

Le logo n'est jamais dessiné par le générateur : le logo officiel (assets/brand/logo_white.png, mis à l'horizontale
comme sur le site) est incrusté ensuite. Textes mal écrits par le générateur corrigés à la main.

Voix off (à valider par Tao) : « Avec votre budget… quelle maison pouvez-vous vraiment construire ? Cette villa de
trois chambres : environ dix-sept à vingt et un millions de francs CFA. Ce duplex de cinq chambres tient sur un terrain
de trois cent cinquante mètres carrés. J'ai rangé cent villas et duplex dans un seul guide : classés par budget, avec
la surface et le terrain qu'il faut. Ouvrez-le sur votre téléphone, et trouvez la maison à votre portée. Le guide est
à mille neuf cents francs CFA, sur wooplans point com. »

## Variantes du visuel gagnant (15 nov., après le jour 1)

« crea-6-preferees-clients » a pris 91 % du budget le jour 1 (CTR 8,7 %, 1,30 $ par vente). Déclinaisons du même angle :

| Fichier | Accroche |
|---|---|
| crea-7-plus-demandees.jpg | Les 6 maisons les plus demandées (V3-018, V3-009, V3-037, V3-014, D4-040, D4-043) |
| crea-8-combien-coute.jpg | Combien coûte la maison de nos clients ? (D5-012, V4-005, V3-017, V4-036) |
| crea-9-preferees-story-9x16.jpg | Les maisons préférées de nos clients, format Story / Reels |

À ajouter dans le même ensemble de publicités après le jour 2 (pas avant, pour ne pas relancer l'apprentissage).
