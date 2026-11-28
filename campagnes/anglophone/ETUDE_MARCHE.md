# WOOPLANS anglophone : étude de marché et problème du produit (points 1 et 2)

Rédigé le 28 nov. 2026. Rien n'est construit ni publié : ce document sert à ta décision.
Les montants WOOPLANS viennent de la base du site (108 modèles publiés, outil `list_plans` / `get_plan`) et de `src/lib/plan-pricing.ts`.
Les chiffres de marché sont ceux des sources citées : ce sont surtout des blogs de constructeurs et de vendeurs. Ils donnent un ordre de grandeur, pas une vérité.
Taux utilisés (fin nov. 2026, à revérifier) : 1 $ ≈ 596 FCFA (EUR/USD ≈ 1,10) ; 1 $ ≈ 131 KES, 11,8 GHS, 1 350 à 1 440 NGN.

---

## 0. Trois constats qui changent le plan

1. **Les devis sont un calcul au m², pas un métré.** Chaque devis = surface × prix au m² × coefficient de standing, réparti en 8 postes par pourcentages fixes (`src/lib/plan-pricing.ts`). Standard : 160 000 FCFA/m² pour une villa, 216 000 FCFA/m² pour un duplex (ex. V4-005 : 201 m² × 160 000 = 32 160 000 FCFA ; fondation 12,6 %, élévations 18,4 %, etc.). Il n'existe **aucune quantité** (m³ de béton, nombre de parpaings…) dans nos données.
   Conséquence : un produit « plans + quantités » ne peut pas être fait à partir de ce qu'on a ; il faudrait un métreur. Et convertir les FCFA en KES/NGN serait faux (voir §2.2).
2. **Le Nigeria ne paie pas surtout en Mobile Money.** On paie par virement bancaire instantané (NIP, ~45 %) et par carte (~25 %) ; le Mobile Money à la kényane y est marginal. Il faut vérifier quels moyens Chariow propose réellement au Nigeria avant tout budget.
3. **Le catalogue fait 108 modèles publiés** (et non 55 comme dans `data/plans.json` du studio). Il y a déjà 3 variantes de standing (bas 0,8 / standard 1 / élevé 1,2).

---

## 1. Étude de marché

### 1.1 Vue d'ensemble

| | Kenya | Ghana | Nigeria |
|---|---|---|---|
| Devise Chariow | KES ✅ | GHS ✅ | NGN ✅ |
| Déficit de logements | ~2 M (base floue : stock ou par an) | 1,7 à 1,8 M | 15 M (officiel) à 17-28 M |
| PIB/hab. nominal 2025 | ~2 500 $ | ~3 200 $ | plus faible depuis la dévaluation (à vérifier au FMI) |
| Paiement dominant | M-Pesa (~68 à 89 % du Mobile Money, 87 % des adultes l'utilisent) | MTN MoMo (~73 à 78 %), Telecel Cash (~23 %) | virement bancaire NIP (~45 %), carte (~25 %), USSD |
| CPM Meta (sources tierces) | 0,9 à 2,4 $ | pas de donnée trouvée | 0,8 à 2,2 $ |
| CPC Meta (sources tierces) | ~0,22 $ | ? | ~0,12 $ |
| Concurrence en ligne | forte et très bon marché | faible, surtout en dollars | moyenne, en nairas |

Pour comparaison : ta campagne francophone est à ~0,11 $ le clic.

**Construction : la maison individuelle autofinancée et bâtie par étapes est la norme dans les trois pays** (pas de crédit immobilier de masse). C'est exactement ton client. Le marché est donc grand, mais la concurrence se joue sur le prix des plans.

### 1.2 Vocabulaire local (à utiliser dans les pubs et la page)

- **Kenya** : *bungalow* = plain-pied ; *maisonette* = maison à étage (pas « duplex ») ; *mansion* pour le haut de gamme. Terrains en pieds ou en acres : *50 by 100* (≈ 465 m²), *1/8 acre* (≈ 506 m²). Surfaces des maisons : m² le plus souvent.
- **Nigeria** : *bungalow* ; *duplex* = maison à étage (*detached / semi-detached / terraced duplex*) ; *BQ* (*boys' quarters*, dépendance) très recherché. Terrains : *plot* (souvent 50 × 100 ft, ≈ 465 m² ; 600 m² à Lagos dans les lotissements). m² courant.
- **Ghana** : *storey building* ou *two-storey* pour un étage ; *bungalow* ; *self-contained* ; *chamber and hall* pour le bas de gamme. Terrains souvent en pieds (*70 × 100*, *plot*).
- Conseil : afficher **m² et sq ft**, et la taille de terrain en **pieds** (ex. « fits a 50×100 plot »). Nos `land_area` (250 à 750 m²) se traduisent bien : 450-500 m² ≈ « 1/8 acre » ou « 50×100 ».

Dans `get_plan`, une partie des compositions est déjà bilingue (« Living (Salon) », « Master's Bedroom ») : certains plans cotés sont peut-être déjà annotés en anglais. À vérifier modèle par modèle.

### 1.3 Concurrence et prix pratiqués

| Vendeur | Pays | Offre | Prix |
|---|---|---|---|
| [HPD Constructions](https://hpdconstructions.com/) / [HPD Consult](https://www.hpdconsult.com/product-tag/bungalow-design/) | KE | plan PDF par modèle, M-Pesa ou carte, envoi immédiat | 20 000 KES barré → **1 000 KES** (offre peut-être ancienne) ; d'autres à 1 500 ou 15 000 KES |
| [houseplans.co.ke](https://www.houseplans.co.ke/house-plans) | KE | dessins sur mesure | à partir de 25 000 KES ; bungalow 4 ch. 36 700 KES ; maisonette 3 ch. 60 000 KES |
| [Earch Designers](https://earchdesigners.co.ke/index.php?page=house-plans) | KE | ~110 plans, PDF immédiat | prix non visibles |
| [Maramani](https://www.maramani.com/collections/all) | panafricain (USD) | plan PDF ou CAD + **métré (BOQ) Excel en option** | 135 à 660 $ le plan ; BOQ +60 à 200 $ |
| [HousePlanNG](https://houseplanng.com/all-plans/) | NG | 131 plans, PDF ou AutoCAD | PDF 4 ch. **125 000 à 188 000 NGN** ; AutoCAD 375 000 à 563 000 NGN |
| [Ideal Dwelling](https://idealdwelling.mydwellinghub.com/) | NG | plans PDF | dès 100 000 NGN (2 ch.) |
| [nigerianhouseplans.com](https://nigerianhouseplans.com/) | NG | grands modèles | 550 000 à 900 000 NGN |
| [Jiji.ng](https://jiji.ng/142-architectural-drawing) | NG | petites annonces de dessinateurs | 19 500 à 800 000 NGN |
| [Afrohouseplans](https://www.afrohouseplans.com/collection/ghana-house-plans/) | GH | plans par modèle | dès 199-239 $ |
| [Ghana House Plans](https://ghanahouseplans.com/) | GH | plans tamponnés pour permis | ~1 997 $ |

À retenir :
- Tout le monde vend **un plan par modèle**. Personne ne vend un **catalogue entier avec budget** à prix fixe : c'est ton angle (« 100+ designs for the price of one plan »).
- Le Kenya est déjà **bradé** (plans à 1 000-1 500 KES). Ton catalogue doit s'y vendre comme « choisir avant de payer un architecte », pas comme un plan.
- Au Nigeria et au Ghana, un seul plan PDF coûte 70 à 200 $ : un catalogue à ~35-45 $ est clairement moins cher.
- Le Ghana a peu de concurrence en monnaie locale : bonne surprise.
- Points faibles face à eux : tes plans ne sont **pas tamponnés par un architecte local** (permis de construire) et tes PDF sont en français.

### 1.4 Les autres pays

Chariow encaisse en devise locale aussi en Ouganda (UGX), Tanzanie (TZS), Rwanda (RWF), Zambie (ZMW), Sierra Leone (SLE) et Afrique du Sud (ZAR) ([chariow.com/coverage](https://chariow.com/coverage)).

- **Ouganda : le meilleur 4e pays.** Anglophone, MTN + Airtel > 90 % du marché, 37,8 M de comptes Mobile Money actifs, 2,5 Md$ de transferts de la diaspora en 2025 (61 % par Mobile Money), surtout pour construire. Concurrent : Maramani a une collection Ouganda.
- **Tanzanie** : grand marché d'autoconstruction, mais le grand public parle swahili. Plus tard, avec une version en swahili.
- **Rwanda, Zambie** : marchés petits ; peu de données. Plus tard.
- **Afrique du Sud** : pouvoir d'achat élevé mais on y paie par carte, et le marché des plans est réglementé et différent. Pas prioritaire.
- **Sierra Leone, Liberia, Gambie** : petits ; Liberia et Gambie en USD seulement.

### 1.5 Pouvoir d'achat et diaspora

- PIB/hab. nominal 2025 : Ghana ~3 200 $, Côte d'Ivoire ~3 000 $, Kenya ~2 500 $, Cameroun ~2 000 $, Ouganda ~1 350 $ ([historysaid](https://historysaid.com/insights/richest-countries-in-africa), [statskenya](https://statskenya.co.ke/at-stats-kenya/about/list-of-african-countries-by-gross-domestic-product-per-capita-africa-gdp-per-capita/136)). Kenya et Ghana sont donc au niveau de tes meilleurs marchés francophones ; le Nigeria est plus bas par habitant, mais son marché est 5 à 10 fois plus grand.
- Diaspora : le Nigeria est le 1er récepteur de transferts d'Afrique (19,2 Md$ en 2021) ; plus de la moitié sert à construire ou acheter un terrain au Kenya et au Nigeria (études anciennes) ([PRB](https://www.prb.org/resources/remittances-from-sub-saharan-african-migrants-pay-for-schooling-health-care/)). Au Kenya, seuls 2,2 % des bénéficiaires investissent dans l'immobilier, mais la diaspora paie de plus en plus les promoteurs directement ([Standard, juil. 2026](https://www.standardmedia.co.ke/business/real-estate/article/2001552335/how-diaspora-property-investors-have-changed-tack-in-remittances)). La diaspora (UK, US) paie par carte : Chariow la sert aussi en USD.

### 1.6 Ce que tu dois confirmer avec Chariow (je ne peux pas le voir)

La page de couverture ne liste que les devises, pas les opérateurs. À faire, pays par pays :
1. Ouvrir un lien de paiement Chariow depuis un VPN ou un contact au Kenya, au Ghana et au Nigeria, et noter les moyens proposés (M-Pesa ? MTN MoMo, Telecel Cash, AT ? virement / USSD / OPay au Nigeria ?) et le montant exact affiché en KES/GHS/NGN.
2. Demander au support : frais de conversion XAF → KES/GHS/NGN, taux utilisé, plafonds par transaction, taux d'échec.
3. Commission : la page tarifs indique **15 % jusqu'à 5 000 $ de ventes, puis 10 %** ([chariow.com/en/pricing](https://chariow.com/en/pricing)). Confirmer que ton compte est bien à 10 %.

---

## 2. Le problème du produit

### 2.1 Vendable tel quel en anglais ?

| Élément | Vendable ? | Pourquoi |
|---|---|---|
| Rendus 3D | ✅ oui | pas de texte, universel |
| Surfaces, chambres, niveaux, terrain conseillé | ✅ oui | à traduire et afficher aussi en sq ft / pieds |
| Plans cotés | 🟡 oui, avec réserve | les cotes sont en mètres (compris partout) ; les noms des pièces sont en français sur une partie des plans → un lexique FR → EN suffit au départ |
| Devis en FCFA | ❌ non | prix des matériaux et de la main-d'œuvre francophones ; un acheteur kényan qui verrait « 32 160 000 FCFA » n'en ferait rien |
| Répartition du budget par poste (%) | ✅ oui | les pourcentages (fondation 12,6 %, élévations 18,4 %…) sont utiles partout, si on le dit comme une répartition indicative |
| Bonus « architecte sur WhatsApp » | ❓ | qui répond en anglais ? |
| Plans complets 200 000 / 300 000 FCFA | ❓ | livrés en anglais ? conformes aux règles locales ? pas de tampon local pour le permis |

### 2.2 Pourquoi on ne peut pas juste convertir les devis

Notre prix au m² standard vaut ~268 $ (villa) et ~362 $ (duplex). Les sources locales donnent :
- **Kenya** : 50 000 à 65 000 KES/m² en finition moyenne ≈ **380 à 500 $/m²**, donc plus cher que notre base ([Integrum](https://integrum.co.ke/2025-construction-costs-in-kenya-322/), [Aalis Studios](https://aalisstudios.com/blog/construction-cost-per-square-metre-kenya.html)).
- **Nigeria** : 150 000 à 310 000 NGN/m² à Lagos en 2026 ≈ **110 à 220 $/m²**, donc moins cher ([nigeriabuildingcost.ng](https://nigeriabuildingcost.ng/), [Lands of Nigeria](https://landsofnigeria.com/2025-nigerian-construction-cost-index-cement-labor-material-prices/)). Les chiffres de 2025 sont déjà périmés (inflation des matériaux).
- **Ghana** : pas de source locale fiable trouvée.

Convertir donnerait un budget faux d'environ –30 % au Kenya et +60 à +140 % à Lagos. On ne le fait pas.

### 2.3 Options et coûts

**Option A : « Design catalogue » sans prix local (le plus rapide)**
Rendus + plans cotés + surfaces + répartition du budget en %, avec un **calculateur** : le client saisit le prix au m² que lui donne son maçon (ou choisit bas / moyen / haut), et l'outil calcule le total et les 8 postes. Aucun prix inventé.
- Travail : traduction des fiches (108 descriptions, par IA puis ta relecture), lexique des plans, calculateur sur le site.
- Coût : ~2 à 4 jours de développement, < 20 $ d'IA.
- Limite : moins fort que « devis inclus ».

**Option B : A + « guide des coûts » par pays avec sources**
Comme A, mais le calculateur propose des fourchettes publiées (ex. Kenya 50 000 à 65 000 KES/m²), affichées comme « estimations publiées par des tiers, à confirmer avec votre entrepreneur », avec la source et la date. Mise à jour chaque trimestre.
- Coût : A + ~1 jour de recherche par pays et par trimestre.
- Risque : sources fragiles (surtout au Ghana) ; à dire clairement.
- **C'est ma recommandation pour le test.**

**Option C : devis locaux faits par un métreur (quantity surveyor) local**
Un métreur kényan / nigérian / ghanéen produit un vrai BOQ pour les 10 à 20 modèles les plus vendus. Seul moyen honnête d'avoir « devis inclus » ou « plans + quantités ».
- Coût : à demander (Maramani facture le BOQ 60 à 200 $ au client, ce qui donne une idée de la valeur, pas du coût). Délai de plusieurs semaines.
- À ne lancer que si le test A/B vend.

**Option D : traduction complète des PDF et des plans cotés**
Refaire les annotations des plans en anglais.
- Coût : élevé (travail de dessin modèle par modèle). À réserver aux 20 meilleurs modèles, après le test.

**À éviter** : un produit « plans + quantités » sans métreur (nous n'avons pas les quantités) et toute conversion de devis FCFA → devise locale.

---

## 3. Prix (premiers chiffres, à valider après le relevé Chariow)

Repères : 29 000 FCFA ≈ 48,6 $ ; 39 000 FCFA ≈ 65,4 $. Net = prix − 10 % Chariow − ~3 % de conversion (à confirmer pour ces devises).

| Pays | Prix proposé | Barré | ≈ $ | Net ≈ | Justification |
|---|---|---|---|---|---|
| Kenya | **KES 4,999** | 7,999 | 38 $ | ~19 900 FCFA | plans unitaires à 1 000-36 000 KES ; prix « 4,999 » habituel |
| Ghana | **GHS 499** | 799 | 42 $ | ~22 000 FCFA | un plan seul ≈ 199 $ ; peu de concurrence locale |
| Nigeria | **NGN 49,900** | 79,900 | 36 $ | ~18 600 FCFA | un plan PDF 125 000-188 000 NGN ; ton catalogue = « 1/3 du prix d'un plan » |

- Point mort : une vente rapporte ~18 600 à 22 000 FCFA net (31 à 37 $) ; au-delà de ce coût par vente, on perd de l'argent. Exemple : à 20 $ par vente (≈ 12 000 FCFA), il reste ~8 000 FCFA par vente, donc ~12 ventes/jour (~240 $ de pub/jour) pour 100 000 FCFA de profit. Ce marché est un **relais de croissance**, pas un remplaçant du francophone.
- Chariow convertit depuis le FCFA : pour obtenir « 4,999 KES » pile au paiement, il faut créer un produit en XAF dont la conversion tombe sur ce montant (comme pour le produit Afrique de l'Ouest à 28 155). On relève le montant réel affiché au paiement, puis on l'inscrit dans `src/config/projet.json` (`localPrices`).
- Ne pas afficher de compte à rebours tant que le test 29 000 FCFA n'est pas tranché (vers le 5 déc.).

---

## 4. Décisions à prendre (avant que je construise quoi que ce soit)

1. **Pays de départ** : Nigeria + Ghana + Kenya ensemble, ou commencer par Ghana + Kenya (paiement Mobile Money plus sûr) et ajouter le Nigeria après vérification du paiement ?
2. **Option produit** : A, B (recommandée) ou C ?
3. **Prix** : ceux du tableau, ou autre chose ?
4. **Bonus et plans complets** : qui répond en anglais sur WhatsApp ? Les plans complets sont-ils proposés aux anglophones (en anglais, sans tampon local) ?
5. **Tests Chariow** à faire de ton côté (§1.6) : moyens de paiement affichés et montants exacts dans les 3 pays.

Après ta réponse, je passe aux points 3 à 6 (page anglaise, pubs, campagne, plan d'action).

---

## Sources

- Couverture et tarifs Chariow : [chariow.com/coverage](https://chariow.com/coverage), [chariow.com/en/pricing](https://chariow.com/en/pricing)
- Déficit de logements : [CSIS](https://www.csis.org/analysis/solving-africas-housing-deficit), [The Guardian Nigeria](https://guardian.ng/?p=2899878), [Banque mondiale](https://www.worldbank.org/content/dam/Worldbank/document/Africa/Report/stocktaking-of-the-housing-sector-in-sub-saharan-africa-full-report.pdf), [MFW4A / CAHF](https://www.mfw4a.org/our-work/housing-finance)
- Coûts de construction : [Integrum (KE)](https://integrum.co.ke/2025-construction-costs-in-kenya-322/), [Aalis Studios (KE)](https://aalisstudios.com/blog/construction-cost-per-square-metre-kenya.html), [Makao Bora (KE)](https://makaobora.com/construction-cost-estimation-budgeting-in-kenya/), [nigeriabuildingcost.ng](https://nigeriabuildingcost.ng/), [Lands of Nigeria](https://landsofnigeria.com/2025-nigerian-construction-cost-index-cement-labor-material-prices/), [The Africanvestor](https://theafricanvestor.com/blogs/news/nigeria-construction-costs-too-expensive)
- Paiements : [PaymentBrief Ghana](https://paymentbrief.com/markets/ghana), [PaymentBrief Nigeria](https://paymentbrief.com/markets/nigeria), [Mordor Intelligence](https://www.mordorintelligence.com/industry-reports/telco-mobile-money-market), [Africa Biz News (Findex 2025)](https://africabiznews.com/af/tech/african-countries-highest-mobile-money-adoption-2025), [Kora](https://www.korahq.com/blog/best-payment-gateways-for-businesses-in-nigeria)
- Coûts Meta : [Adamigo](https://www.adamigo.ai/blog/meta-ads-cpm-cpc-benchmarks-by-country-2026), [Adligator](https://adligator.com/blog/meta-ads-cpm-by-country-benchmarks), [Stackmatix](https://stackmatix.com/blog/facebook-ads-cpm-by-country-2026), [Grey](https://grey.co/blog/facebook-ads-cost-nigeria)
- Vocabulaire (annonces) : [Kenya Property Centre](https://kenyapropertycentre.com/for-sale/houses/detached-bungalows/showtype?bedrooms=3), [Nigeria Property Centre](https://nigeriapropertycentre.com/houses/detached-duplexes/showtype?bedrooms=4), [meQasa](https://meqasa.com/3-bedroom-houses-for-sale-in-accra), [HPD maisonettes](https://hpdconstructions.com/product-tag/maisonette-plan/)
- Ouganda : [African Exponent](https://africanexponent.com/why-ugandas-housing-boom-runs-on-remittances/), [Maramani Ouganda](https://www.maramani.com/collections/uganda-house-plans)
- Taux de change : [Wise USD/GHS](https://wise.com/us/currency-converter/usd-to-ghs-rate), [Monierate USD/KES](https://monierate.com/converter/usd-to-kes), [Curnance USD/NGN](https://www.curnance.com/convert/usd-to-ngn), [PoundSterlingLive EUR/USD](https://www.poundsterlinglive.com/history/EUR-usd-2026)
