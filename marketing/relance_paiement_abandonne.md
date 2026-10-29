# Relance des paiements abandonnés ou échoués (Chariow)

Produits à cocher dans le workflow : Catalogue Premium (licence), Plan et devis Wooplans, et l'ancien CATALOGUE PREMIUM 2026 tant qu'il reçoit des commandes.
Déclencheurs : Abandoned Sale + Failed Sale. Option « ne pas relancer si le client possède déjà le produit » : activée.
Variables Chariow : {{customerName}}, {{checkoutUrl}}. Remplacer [NUMÉRO WHATSAPP] par le numéro de service.

## Action 1 : email, 2 minutes après

Objet : Votre paiement WooPlans n'est pas passé ?

Bonjour {{customerName}},

Votre commande WooPlans n'a pas été finalisée. Cela arrive souvent avec Mobile Money : solde insuffisant, code de confirmation non validé à temps, ou réseau lent.

Votre commande vous attend. Pour la reprendre en une minute :
{{checkoutUrl}}

Prix actuel du Catalogue Premium : 29 000 FCFA, paiement unique.

Un problème pour payer ? Répondez simplement à cet email, ou écrivez-nous sur WhatsApp au [NUMÉRO WHATSAPP]. Nous vous aidons à finaliser.

À très vite,
Romuald TAO
Équipe WooPlans
wooplans.com

## Action 2 : WhatsApp (WaChap), 10 minutes après

Bonjour {{customerName}}, ici Romuald de WooPlans.
J'ai vu que votre paiement n'est pas passé. Souvent c'est Mobile Money (solde ou code de validation).
Voici votre lien pour reprendre la commande : {{checkoutUrl}}
Si vous bloquez, répondez-moi ici, je vous aide.

## Action 3 : email, 24 heures après (1 440 minutes)

Objet : Une question avant de choisir votre plan ?

Bonjour {{customerName}},

Hier, vous avez commencé une commande sur WooPlans sans la terminer. Si quelque chose vous fait hésiter, dites-le-moi : je réponds personnellement.

Les questions qu'on nous pose le plus :
- Quand est-ce que je reçois l'accès ? Juste après le paiement.
- Je peux payer par Mobile Money ? Oui, directement sur la page de paiement.
- Et si le plan doit être adapté à mon terrain ? Écrivez-nous : nous étudions votre demande.

Votre lien est toujours valable :
{{checkoutUrl}}

Prix actuel : 29 000 FCFA.

Bonne journée,
Romuald TAO
Équipe WooPlans
