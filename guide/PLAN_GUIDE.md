# Guide d'entrée payant (tripwire) : plan de production

Statut : **proposition, rien n'est produit, programmé ni publié**. Validation de Tao requise avant toute étape.

## 1. Rôle du guide dans l'entonnoir

Pub Facebook → page de vente du guide → achat (1 500 ou 2 000 FCFA, test) → page de remerciement avec offre catalogue → suivi WhatsApp/email → Catalogue Premium 39 000 FCFA (ou plan et devis d'un modèle).

Le guide **inspire et oriente** (« quelle maison pour mon budget »). Il ne remplace pas le catalogue : plans cotés, devis détaillés et comparaison restent dans le Catalogue Premium.

## 2. Thème et titre (à tester en pub)

Thème retenu : **le budget**, car c'est la première question de quelqu'un qui a un terrain.

Titres candidats (à passer dans `wooplans.guardrails.check_copy`) :
1. « Quelle maison construire avec votre budget ? 20 modèles classés par coût de construction »
2. « J'ai un terrain : quelle maison puis-je construire ? Le guide en images »
3. « 20 maisons, 20 budgets : trouvez la vôtre avant de construire »

Recommandation : titre 1, le plus concret (le chiffre et le budget sont dans le titre).

## 3. Contenu : 20 modèles classés par tranche de budget

Source unique : `data/plans.json` (champ `estimate_total`, issu du devis du PDF). **Aucune fourchette inventée** : on affiche « environ X millions FCFA (estimation du devis) », jamais une plage calculée.

Répartition actuelle de `plans.json` (55 modèles) :

| Tranche | Modèles disponibles | Types | Estimation min–max |
|---|---|---|---|
| Moins de 20 M FCFA | 12 | villas 3 et 4 chambres | 11,8 – 19,8 M |
| 20 à 40 M FCFA | 22 | villas 3/4 ch., duplex 4/5 ch. | 20,3 – 39,4 M |
| 40 à 60 M FCFA | 15 | duplex 4 et 5 chambres | 40,7 – 58,7 M |
| Plus de 60 M FCFA | 6 | duplex 4 et 5 chambres | 60,8 – 95,8 M |

Sélection proposée : **5 modèles par tranche = 20 modèles**, choisis pour varier chambres, surface et type. La sélection finale se fait parmi les modèles qui ont de beaux rendus propres (à vérifier avec `list_plan_files`, originaux sans filigrane).

Chaque modèle = 1 page : rendu de façade (image principale), code, nombre de chambres, niveaux, surface, terrain minimum (si renseigné dans `plans.json`, sinon omis), estimation du devis, une phrase de description. Pas de plan coté, pas de détail de devis.

## 4. Structure (environ 30 pages, format PDF vertical)

| Pages | Contenu |
|---|---|
| 1 | Couverture : titre, rendu fort, wooplans.com |
| 2 | À qui s'adresse ce guide / comment l'utiliser (3 lignes) |
| 3 | « Ce que veut dire une estimation » : ce qu'elle inclut, pourquoi elle varie (explication prudente, sans chiffre inventé) |
| 4 | Sommaire par tranche de budget |
| 5–24 | Les 20 modèles, 5 par tranche, avec un intercalaire de tranche |
| 25 | Comment choisir selon la taille du terrain et la famille (check-list) |
| 26 | Les 5 questions à se poser avant de construire (budget total, terrain, titre foncier, autorisation, phasage) |
| 27 | Ce que ce guide ne montre pas : plans cotés, devis détaillé, comparaison |
| 28 | **Page catalogue** : « Vous avez fait le premier pas » + ce que contient le Catalogue Premium + prix actuel 39 000 FCFA + lien |
| 29 | Contact / WhatsApp |

Page 28 : lien `https://wooplans.com/catalogue-premium` avec UTM (`wooplans/utm.py`), source `guide`. Jamais « l'offre expire dans X heures ».

## 5. Page de vente et paiement

- Page de vente dédiée (hors page catalogue), avec 4 à 6 aperçus de pages, le prix, le bouton de paiement (Chariow).
- Prix testés : 1 500 et 2 000 FCFA. Vérifier les frais Chariow et mobile money à ce montant.
- Collecter à l'achat : **numéro WhatsApp** (en plus de l'email).
- Page de remerciement : téléchargement du guide **et** offre catalogue immédiate (à vérifier : offre complémentaire Chariow au paiement).

## 6. Suivi après achat

1. Immédiat : page de remerciement avec l'offre catalogue.
2. WhatsApp à J+1 : « Avez-vous trouvé un modèle dans votre budget ? » (question, pas de relance agressive).
3. Email à J+2 : un modèle précis du guide, avec ce que le plan et devis ajoute.
4. Email/WhatsApp à J+5 puis J+10 : témoignage, question fréquente, lien catalogue.
5. Segmenter selon la tranche de budget consultée si le suivi des clics le permet.

## 7. Mesure (à mettre en place avant le test)

- Réparer le suivi des liens (ventes « non tracées ») avant de lancer.
- Événement d'achat Meta actif pour la campagne guide.
- Critères : coût par achat du guide inférieur ou égal à son prix (seuil à 2 000 FCFA : au moins 1,7 % des clics) ; au moins 3 % des acheteurs passent à un achat supérieur en 30 jours.
- Budget test : environ 35 $ par prix.

## 8. Production (si Tao valide)

| Étape | Outil / source | Responsable |
|---|---|---|
| Sélection des 20 modèles et vérification des rendus propres | `plans.json`, `list_plan_files` | Claude, validé par Tao |
| Textes (descriptions, pages 2, 3, 25–28) | `check_copy` | Claude, relu par Tao |
| Mise en page PDF | outil PDF / design à définir | Claude |
| Vignette de la pub | `tools/make_thumbnail.py` | Claude |
| Page de vente + produit Chariow | Chariow | Tao (validation avant mise en ligne) |
| Campagne de test Meta | Meta Ads | **uniquement après accord de Tao** |

## 9. Points ouverts

1. `data/plans.json` ne contient pas tous les modèles vendus (absents : V3-009, V3-014, V3-017, V4-032, D4-020…). À synchroniser avec le catalogue avant de choisir les 20 modèles.
2. Les ventes de WooPlans passent par le compte pub « MyMusika » : confirmer que cela respecte la séparation avec Kilabi.
3. Décider si l'estimation est affichée en millions arrondis ou au montant exact du devis.
4. Choix du titre et du prix de départ (1 500 ou 2 000 FCFA).
