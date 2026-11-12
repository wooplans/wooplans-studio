# Catalogue A3 · « modèle A »

Catalogue imprimable : **une fiche A3 par modèle** (rendus, descriptif, terrain, devis, plans de distribution), avec couverture, **sommaire cliquable** et **pages numérotées**. Le document est coupé en deux parties : **Duplex** puis **Villas**.

Mise en page validée par Tao le 12 nov. (« modèle A »). Pour le terrain et le devis, **la source est le site wooplans.com** (décision de Tao du 12 nov.), pas le PDF « APS et devis ».

## Produire / mettre à jour le document

Dire à Claude : **« régénère le catalogue A3 »**. Claude resynchronise les données du site, puis génère le PDF. Détail :

| Étape | Commande | Ce que ça fait | Qui peut la lancer |
|---|---|---|---|
| 1. Données publiques | `python tools/catalogue_a3.py sync-public --discover` | relit chaque fiche publique : chambres, surface, dimensions, **terrain**, rendus, nouveaux modèles | tout le monde, sans secret (aussi en GitHub Actions) |
| 2. Données Premium | `python tools/catalogue_a3.py ingest <fichier>` | **devis par lot**, plans de distribution, descriptif complet, depuis le connecteur wooplans | **Claude** (le connecteur n'existe que dans une session Claude) |
| 3. Génération | `python tools/catalogue_a3.py build [--part duplex\|villa]` | couverture, sommaire, séparateurs, fiches ; écrit `catalogue_a3/out/catalogue-a3-<partie>.pdf` + `RAPPORT-<partie>.md` | tout le monde (Chromium requis) |
| 2 bis. Originaux R2 | `python tools/catalogue_a3.py fetch-originals <tsv>` | télécharge les rendus **originaux sans filigrane** (≈ 1 672 × 941 px) dans `catalogue_a3/orig/<code>/` (lignes `code<TAB>nom_public<TAB>lien`) ; les liens viennent de `get_plan_file` (connecteur wooplans) et le choix des rendus est enregistré par `ingest` (`originals`) | **Claude** (connecteur) |
| Contrôle | `python tools/catalogue_a3.py check` | dit quels modèles ont changé sur le site depuis la dernière synchronisation | tout le monde |

Pourquoi deux sources : la fiche publique ne contient pas le devis par lot ni les plans (réservés à l'espace Premium). Le workflow GitHub `catalogue-a3` reconstruit donc le PDF avec les données publiques à jour **et** les derniers devis/plans enregistrés dans le dépôt ; pour rafraîchir les devis et les plans, passer par Claude (étape 2).

## Contenu du dossier

- `data/<code>.json` : instantané d'un modèle (une fiche par modèle, versionné).
- `plans/<code>-<n>.<ext>` : plans de distribution, dans l'ordre d'affichage du site (versionnés ; **dépôt privé obligatoire**, ce sont des fichiers Premium).
- `overrides.json` : choix validés à la main (ex. D4-004 : rendus 1, 2 et 8 ; V4-002 : façade propre de la visite).
- `fonts/`, `assets/` : police Poppins et logo.
- `cache/` (téléchargé à la volée), `orig/` (originaux R2), `hires/<code>/<1-3>.png` (originaux manuels, optionnels), `out/` : **non versionnés**.

## Règles de mise en page

- Trois rendus : les 3 premiers rendus du site (couverture d'abord) qui ont un **original R2** (`orig/<code>/`, sans filigrane) ; à défaut, les rendus publics du site (960 px, filigranés « wooplans.com »). Priorité : `hires/<code>/` (manuel) puis `overrides.json`, puis originaux R2, puis rendus publics. Le workflow GitHub n'a pas accès à R2 (connecteur réservé à Claude) : il retombe sur les rendus publics ; pour un PDF propre, passer par Claude.
- 1 plan : liste « Composition » sous le plan. Plusieurs plans : liste « Caractéristiques » dans la colonne de gauche. Les libellés « rez-de-chaussée » / « étage » ne sont mis que pour 2 plans sur 2 niveaux ; sinon « Plan de distribution 1/3 », etc. (le site ne dit pas ce que contient chaque fichier : un fichier peut être un tableau de surfaces).
- Si le texte d'une colonne déborde, il est resserré automatiquement (jusqu'à 70 %), et la fiche est signalée dans `RAPPORT-<partie>.md`.
- Un modèle auquel il manque le devis, un plan ou les rendus **n'est pas imprimé** : il est listé dans `RAPPORT-<partie>.md` (à corriger sur le site, puis régénérer).
- Chaque texte passe par `wooplans.guardrails.check_copy` ; les écarts sont listés dans `RAPPORT-<partie>.md`.

## À savoir

- Le site fait foi : si une valeur du site est fausse (ex. surface ou terrain différents du plan), la corriger **sur le site**, puis régénérer.
- Les trois totaux d'un même modèle peuvent différer entre le PDF « APS et devis », la fiche en ligne et `data/plans.json` : seule la fiche en ligne est utilisée ici.
- Aucune publication, aucun envoi : le PDF est un fichier à relire par Tao avant impression.
