# Guide d'entrée payant (tripwire) : plan de production

Statut : **titre et prix décidés (14 nov.), rien n'est produit, programmé ni publié**. Validation de Tao requise avant toute étape de production.

Décisions : titre n°1 ; prix du guide **1 900 FCFA** (un seul prix, pas de test 1 500 / 2 000).

## 1. Rôle du guide dans l'entonnoir

Pub Facebook → page de vente du guide → achat (1 900 FCFA) → page de remerciement avec offre catalogue → suivi WhatsApp/email → Catalogue Premium 39 000 FCFA (ou plan et devis d'un modèle).

Le guide **inspire et oriente** (« quelle maison pour mon budget »). Il ne remplace pas le catalogue : plans cotés, devis détaillés et comparaison restent dans le Catalogue Premium.

## 2. Thème et titre

Thème : **le budget**, première question de quelqu'un qui a un terrain.

Titre retenu : **« Quelle maison construire avec votre budget ? 20 modèles classés par coût de construction »** (passe `check_copy`).

## 3. Contenu : 20 modèles classés par tranche de budget

Source unique : `data/plans.json` (champ `estimate_total`, issu du devis du PDF). **Aucune fourchette inventée** : on affiche « environ X millions FCFA (estimation du devis) », jamais une plage calculée.

Répartition de `plans.json` après synchronisation avec le catalogue en ligne (98 modèles publiés) :

| Tranche | Modèles disponibles | Types | Estimation min–max |
|---|---|---|---|
| Moins de 20 M FCFA | 19 | villas 2, 3 et 4 chambres | 11,0 – 19,8 M |
| 20 à 40 M FCFA | 41 | villas 3, 4 et 5 ch., duplex 4 ch. | 20,3 – 37,3 M |
| 40 à 60 M FCFA | 15 | duplex 4 et 5 ch., villa 5 ch. | 40,5 – 58,5 M |
| Plus de 60 M FCFA | 23 | duplex 4 et 5 chambres | 60,5 – 114,9 M |

Sélection proposée : **5 modèles par tranche = 20 modèles**, choisis pour varier chambres, surface et type. La sélection finale se fait parmi les modèles qui ont de beaux rendus propres (à vérifier avec `list_plan_files`, originaux sans filigrane).

Chaque modèle = 1 page : rendu de façade (image principale), code, nombre de chambres, niveaux, surface, terrain minimum (si renseigné dans `plans.json`, sinon omis), estimation du devis, une phrase de description. Pas de plan coté, pas de détail de devis.

## 4. Structure (30 pages, format A5 vertical)

| Pages | Contenu |
|---|---|
| 1 | Couverture : titre, façade, wooplans.com |
| 2 | Comment utiliser ce guide |
| 3 | « Une estimation, pas un prix ferme » |
| 4 | Sommaire par tranche de budget, avec une 5e carte « Étape suivante : Catalogue Premium, pages 29 et 30 » |
| 5–28 | 4 intercalaires de tranche + 20 modèles (5 par tranche) |
| 29 | **Fin du guide, étape suivante** : plans de distribution floutés et extrait du devis par lots du Duplex D4-006, comparaison de 3 modèles du guide |
| 30 | **Catalogue Premium WooPlans** : ce qu'il contient, « Prix actuel : 39 000 FCFA », bouton avec lien UTM |

Retirées après relecture de Tao (14 nov.) : pages de conseils (4 vérifications, 5 questions, « ce que ce guide ne montre pas ») et page de contact. Le guide se termine par deux pages dédiées au catalogue.

Lien du bouton : `wooplans/utm.py` (`build_guide_link`), source `guide_pdf`.

## 5. Page de vente et paiement

- Page de vente dédiée (hors page catalogue), avec 4 à 6 aperçus de pages, le prix, le bouton de paiement (Chariow).
- Prix : **1 900 FCFA**. Vérifier les frais Chariow et mobile money à ce montant.
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
- Critères : coût par achat du guide inférieur ou égal à son prix (seuil à 1 900 FCFA : au moins 1,8 % des clics, avec un clic à environ 34 FCFA) ; au moins 3 % des acheteurs passent à un achat supérieur en 30 jours.
- Budget test : environ 35 $ à 70 $ (1 000 à 2 000 clics) pour un seul prix.

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

1. **Écart de prix résolu (Tao, 14 nov.)** : les prix du catalogue en ligne font foi, pas ceux des PDF. Après synchronisation, les estimations de **tous les duplex** sont 20 % plus hautes qu'avant (ex. D4-001 : 95 760 000 → 114 912 000 FCFA ; D4-034 : 25 → 30,9 M), et le terrain de nombreux modèles a augmenté (souvent +50 m²). Ce sont les valeurs du catalogue en ligne, validées. Les anciennes vidéos publiées citent peut-être les anciens montants : à vérifier si l'on y revient.
2. Les ventes de WooPlans passent par le compte pub « MyMusika » : confirmer que cela respecte la séparation avec Kilabi.
3. Décider si l'estimation est affichée en millions arrondis ou au montant exact du devis.
4. Vérifier que les rendus des 20 modèles retenus sont propres (originaux sans filigrane).
