# Campagne Facebook du guide (14 nov.) : état et reprise

Compte pub : **MyMusika** (`27743412105281008`, USD). Page : « Wooplans Catalogue » (`122100547778003681`). Pixel : `wooplansPixel` (`1127775973645411`). Aucun compte Instagram lié à ce compte pub (les pubs ne passeront que sur Facebook, sauf liaison).

## Déjà créé (tout en PAUSE, rien ne dépense)
| Objet | ID |
|---|---|
| Campagne « WooPlans · Guide budget 1 900 · CI » : Ventes, budget de campagne **5 $ par jour** (Advantage+ campaign budget), enchère « volume le plus élevé » | `52618106921693` |
| Ensemble « Ensemble 1 · CI · A+ audience · suggestion hommes 35+ » : Côte d'Ivoire seule, optimisé Achat (pixel), audience Advantage+ avec suggestion hommes 35–65 ans (même logique que vos ensembles précédents) | `52618106943693` |

## Images dans la bibliothèque Meta (hash)
| Fichier | Hash |
|---|---|
| `pub1_budget.png` (1080×1350) | `ea6a8e80c05636de1c8ab3a0dccd7005` |
| `pub2_grille.png` (1080×1350) | `7d35c70edd2b33a542c98f036c571c91` |
| `pub3_tranche.png` (1080×1350) | `1ce60d218d0ed368adf4e10d2fbac311` |
| carrousel carte 1 · couverture du guide (1080×1080) | `4f06bd2e84156410e49a5ca549ed08f9` |
| carte 2 · moins de 20 M | `4a09410d4f2dc6b18226a5ee1ee7d39c` |
| carte 3 · 20 à 40 M | `365cb56d6694338573e8bfa0d52f1403` |
| carte 4 · 40 à 60 M | `830b8c9b865ce9341e3b7d8214fcff70` |
| carte 5 · plus de 60 M | `171780313012662c49e4c5d49ab08abe` |

## Les 4 pubs (à créer dès que le lien Chariow est connu)
Lien : `{URL_CHARIOW}` avec `?utm_source=facebook&utm_medium=paid&utm_campaign=guide_budget&utm_content=v1` (v2, v3, v4). Bouton : « En savoir plus ». Tous les textes passent `check_copy` (1 900 FCFA autorisé).

1. **Pub 1 · budget** : « Vous avez un terrain ? Quelle maison construire avec votre budget ? 20 modèles classés par coût de construction, en images. Guide : 1 900 FCFA. » · titre « Quelle maison pour votre budget ? »
2. **Pub 2 · grille** : « Avant de construire, découvrez 20 maisons et leur coût de construction estimé : moins de 20 millions, 20 à 40, 40 à 60, plus de 60. Guide en images : 1 900 FCFA. » · titre « 20 maisons, 20 budgets »
3. **Pub 3 · tranche** : « Moins de 20 millions FCFA ? Voyez les villas 3 chambres que vous pouvez envisager. Le guide en images : 1 900 FCFA. » · titre « Le guide des maisons par budget »
4. **Pub 4 · carrousel** (5 cartes) : « 20 maisons classées par budget, de moins de 20 millions à plus de 60 millions de FCFA. Le guide en images : 1 900 FCFA. » · cartes « Le guide : 1 900 FCFA », « Moins de 20 M FCFA », « 20 à 40 M FCFA », « 40 à 60 M FCFA », « Plus de 60 M FCFA »

## Avant d'activer
1. Produit Chariow créé, prix 1 900 FCFA, PDF `guide/guide_budget.pdf` joint, redirection vers la page de remerciement.
2. Événement d'achat du pixel vérifié sur le checkout Chariow.
3. Accord de Tao sur les 4 aperçus de pub. Activation : campagne `52618106921693`.
4. « 100 modèles » : le catalogue en ligne en publie 98.

## Page de remerciement hébergée (dépôt `wooplans/wooplans`, branche `ccr-97a6d86d-lrpkla`)
- URL de redirection Chariow, **une fois la branche fusionnée dans `main` et déployée** : `https://www.wooplans.com/guide-merci` (domaine canonique www).
- Fichiers : `public/lp/guide-merci.html`, `public/lp/guide-maison-budget-520563a29f24.pdf` (nom non devinable), `src/app/guide-merci/route.ts` (sans index), `src/app/robots.ts`, `tests/guide-merci.test.ts`.
- La page envoie le pixel Meta : PageView + Purchase 1 900 XAF (pixel `1127775973645411`). Régénération : `python tools/build_page_merci.py --img <out/img> --download-url /lp/<pdf> --pixel 1127775973645411 --out <wooplans>/public/lp/guide-merci.html`.
- Le déploiement en production ne se fait que depuis `main`, `master` et `ccr-03cfaad2-40szss` (`deploy.yml`) : pousser ma branche ne change pas le site.
- Numéro WhatsApp : le site configure `237694327885` (wrangler.jsonc), la page affiche `+237 6 94 32 77 85` (numéro donné par Tao). Un des deux est faux.

## Pubs créées (14 nov., toutes en PAUSE ; lien Chariow `https://wooplans.mychariow.shop/prd_cyvad4d0`, UTM v1 à v4)
| Pub | ID pub | ID création |
|---|---|---|
| Pub 1 · budget · image | `52618116859093` | `1165902085788189` |
| Pub 2 · grille · image | `52618116864293` | `1908196117262288` |
| Pub 3 · tranche · image | `52618116869293` | `1130582602888603` |
| Pub 4 · carrousel (5 cartes) | `52618116874693` | `1181893604349143` |

État Meta : « en cours de traitement » (revue), statut PAUSED. Activation = campagne `52618106921693`, après accord de Tao.

## Produit Chariow `prd_cyvad4d0` : à corriger avant d'activer
- Nom « Guide 1 » → « Quelle maison construire avec votre budget ? (guide PDF) » ; description avec faute (« choisir ça maison ») ; type **service**, aucun fichier joint ; bouton « Hire service » ; `redirect_url` vide.
- Redirection à saisir : `https://www.wooplans.com/guide-merci` (après fusion de la PR #85 du dépôt du site).
