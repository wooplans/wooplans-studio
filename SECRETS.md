# Secrets GitHub à créer (Settings → Secrets and variables → Actions)
Aucune valeur dans le dépôt. Noms seulement. Vérification : workflow **check-setup** (affiche OK / MANQUANT, jamais les valeurs).

| Secret | Obligatoire ? | Rôle |
|---|---|---|
| ZERNIO_API_KEY | **oui (publication)** | Zernio : programmation Facebook / YouTube |
| ZERNIO_PROFILE_ID | **oui (publication)** | profil Zernio « WooPlans » = `6aca547f2791f56cd0b63f4a` (pas le profil Default de Kilabi) |
| WOOPLANS_MCP_TOKEN | **oui (shorts)** | jeton du serveur MCP du site (= secret `MCP_TOKEN` de wooplans.com, le même que celui du connecteur) : le workflow `short-render` y prend les rendus d'origine dans R2 (lecture seule) |
| ELEVENLABS_API_KEY | non | génération de voix hors session Claude (Claude utilise le connecteur ElevenLabs) |
| POYO_API_KEY | non | génération d'images hors session Claude (Claude utilise le connecteur Poyo) |
| R2_*, TELEGRAM_* | non | seulement si on ajoute stockage / notifications ; bucket et bot **dédiés à WooPlans** (jamais ceux de Kilabi) |

**Le rendu (`visite-render`) n'a besoin d'aucun secret.** Sans les 2 secrets Zernio, les vidéos sont rendues mais pas programmées.
Installation en une fois, depuis un ordinateur où `gh` est connecté (`gh auth login`) : `python tools/set_github_secrets.py` (copie ZERNIO_API_KEY du .env de VIDEO AUTO et impose ZERNIO_PROFILE_ID ; `--dry-run` pour tester).
