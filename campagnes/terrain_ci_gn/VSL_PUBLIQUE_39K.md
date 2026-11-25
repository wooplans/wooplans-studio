# VSL du Catalogue Premium : version publique à 39 000 FCFA (à relire par Tao)

La VSL validée le 23 nov. (`campagnes/vsl_catalogue`, branche `claude/brave-planck-hlzt2d`) est la version des
acheteurs de l'extrait : elle annonce un prix réservé de 29 000 FCFA. Pour la mettre en héro de la page de vente
publique (39 000 FCFA), on change 2 phrases de voix off et 2 écrans. Tout le reste est gardé tel quel.
Textes passés dans `check_copy` : OK.

| Passage | Aujourd'hui (extrait) | Proposition (public) |
|---|---|---|
| s06 voix (2:32) | « Mais regardez : votre prix, vingt-neuf mille francs, c'est moins que le prix d'une brouette de chantier. Pour un projet qui coûtera des millions, choisir votre maison parmi cent modèles pour moins qu'une brouette, c'est la meilleure dépense de tout votre chantier. » | « Mais regardez : trente-neuf mille francs, c'est à peu près le prix d'une brouette de chantier. Pour un projet qui coûtera des millions, choisir votre maison parmi cent modèles pour le prix d'une brouette, c'est la meilleure dépense de tout votre chantier. » |
| s06 écran | « 29 000 FCFA · moins qu'une brouette (≈ 35 000 FCFA) » | « 39 000 FCFA · à peu près le prix d'une brouette (≈ 35 000 FCFA) » |
| s11 voix (3:54) | « Parce que vous avez acheté l'extrait, vous avez un prix réservé : vingt-neuf mille francs au lieu de trente-neuf mille. Cette réduction est valable pendant sept jours. Paiement par Mobaïle Money ou par carte, et votre accès est immédiat. » | « Le Catalogue Premium, c'est trente-neuf mille francs, en un seul paiement. Votre accès est immédiat et à vie, avec les nouveaux modèles inclus. Paiement par Mobaïle Money ou par carte. » |
| s11 + carte finale | « Votre prix réservé · Prix public : ~~39 000~~ · 29 000 FCFA · Réduction valable 7 jours » | « Catalogue Premium · 39 000 FCFA · Paiement unique, accès à vie · Remboursé sous 7 jours » |

Après accord : régénérer s06 et s11 (Gradium, même voix « WooPlans VSL (voix 2) »), refaire le rendu, mettre le fichier
à une nouvelle adresse (`vsl-catalogue-premium-public.mp4`) et la brancher dans le héro de /catalogue-premium
(déjà préparé sur la branche `ccr-c10227eb-9hrtqj` du site, à basculer sur le nouveau fichier).
