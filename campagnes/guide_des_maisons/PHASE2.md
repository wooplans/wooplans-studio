# Campagne du guide, phase 2 (à partir du mardi 17 novembre)

Point de départ (jour 1, 15 nov.) : 5,68 $ dépensés, 4 guides vendus, 1,42 $ par vente.
« Les maisons préférées de nos clients » prend 91 % du budget (CTR 8,7 %, 1,30 $ par vente).
Objectif : rester autour de 2 $ par vente, au-delà ça devient serré.

Rien ne bouge avant la fin du jour 2 (16 nov. au soir). Les décisions se prennent sur les 2 jours cumulés.

## Étape 1 : décider le 16 au soir

| Coût par vente (jours 1 + 2) | Décision |
|---|---|
| ≤ 2 $ | Étapes 2 et 3 le 17 au matin |
| Entre 2 et 2,5 $ | Étape 2 seulement (nouveaux visuels), budget inchangé |
| > 2,5 $ | Pas de hausse ; étape 2, et vérifier la page (conversion < 4 %) |

## Étape 2 : renouveler les visuels (même ensemble de publicités)

- Ajouter : `crea-7-plus-demandees`, `crea-8-combien-coute`, `crea-9-preferees-story-9x16` (Story / Reels).
- Garder le gagnant « préférées ». Ne pas couper les pubs qui n'ont presque pas diffusé : elles ne coûtent rien.
- Couper une pub qui a dépensé 6 $ sans vente.
- Toutes les 1 à 2 semaines, une nouvelle déclinaison du gagnant (autres maisons, autre accroche) : la fatigue
  apparaît quand la fréquence dépasse 2,5 et que le CTR baisse de moitié.

## Étape 3 : monter le budget par paliers

+25 % par jour tant que le coût par vente reste ≤ 2 $ sur les 2 derniers jours :
10 $ → 12,5 $ → 15,5 $ → 19,5 $ → 24 $ → 30 $.
Si le coût par vente dépasse 2,5 $ deux jours de suite : revenir au palier précédent et attendre 3 jours.
Jamais plus de +25 % d'un coup (au-delà, Facebook relance l'apprentissage).

## Étape 4 : élargir l'audience (un nouvel ensemble de publicités à la fois)

Chaque nouveau pays a son propre ensemble, pour lire son coût par vente séparément. Même campagne (budget
Advantage+ au niveau de la campagne), mêmes visuels gagnants, Advantage+ Audience.

| Ordre | Quand | Ensemble de publicités | Pourquoi |
|---|---|---|---|
| 1 | CI ≤ 2 $ pendant 3 jours | **Cameroun** | Marché principal du site, prix en FCFA, la plupart des acheteurs actuels |
| 2 | Cameroun ≤ 2 $ pendant 3 jours | **Sénégal + Bénin + Togo + Burkina Faso** | Afrique de l'Ouest francophone, Mobile Money, même devise que la CI |
| 3 | En parallèle, petit budget | **Gabon + Congo** | Pouvoir d'achat plus élevé, terrains plus grands |
| 4 | Après 50 ventes du guide | **Diaspora : France + Belgique + Canada** (carte bancaire) | Gros budgets de construction ; tester à 5 $/jour, au coût par vente du pays d'origine |

Budget de départ de chaque nouvel ensemble : 5 à 10 $/jour, ciblage large, 18+ (suggestion 25–55).

## Étape 5 : audiences personnalisées (dans le Gestionnaire, pixel 1127775973645411)

| Audience | Définition | Usage |
|---|---|---|
| Acheteurs du guide 180 j | Pages vues : URL contient `/guide-des-maisons/merci` | Exclure de la campagne du guide ; base des sosies |
| Visiteurs du guide 14 j | URL contient `/guide-des-maisons`, en excluant `/guide-des-maisons/merci` | Relance des visiteurs |
| Sosies 1 % des acheteurs du guide | Dès 100 acheteurs, pays par pays | Nouvel ensemble à tester contre le ciblage large |

## Étape 6 : deux petites campagnes de relance (dès 30 acheteurs du guide)

1. **Visiteurs qui n'ont pas acheté** (3 $/jour, objectif Ventes sur l'achat du guide) : visuel « Combien coûte la
   maison de nos clients ? », texte « Votre guide des maisons vous attend · 1 900 FCFA ».
2. **Acheteurs du guide → Catalogue Premium** (3 $/jour, objectif Ventes sur l'achat du catalogue, lien
   `wooplans.com/catalogue-premium?utm_source=facebook&utm_medium=paid&utm_campaign=guide_vers_catalogue`) :
   la vidéo du catalogue imprimé feuilleté (dès qu'elle est tournée), texte « Vous avez le guide. Voici
   l'intérieur de chaque maison : plans cotés et devis poste par poste. 29 000 FCFA. »
   Exclure les membres Premium (liste des clients du catalogue).

## Suivi chaque soir

- Meta : dépense, ventes, coût par vente, CTR, fréquence, par ensemble de publicités.
- Site (tableau de bord, ou résumé « get_business_summary ») : ventes du guide, et **Guide → Catalogue**
  (acheteurs du guide passés au catalogue, reconnus par l'email ou le WhatsApp).
- WhatsApp (Tao) : conversations ouvertes, catalogues vendus en conversation, leads « terrain + moins de 6 mois ».
