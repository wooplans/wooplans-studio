# wooplans-studio
Pipeline de contenu WooPlans. Voir CLAUDE.md pour les règles.

- `wooplans/utm.py` : liens /digital par plateforme et par vidéo (UTM).
- `wooplans/guardrails.py` : interdit les phrases d'expiration et les montants non sourcés.
- `wooplans/registry.py` : anti-doublon des vidéos.
- `wooplans/zernio_client.py` / `zernio_check.py` : publication et vérification des 3 pages.
- `data/plans.json` : fiches plans (étape 2).
