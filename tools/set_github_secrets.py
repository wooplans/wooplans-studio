"""Copie ZERNIO_API_KEY du .env de VIDEO AUTO (+ ELEVENLABS/POYO avec --all) vers les secrets GitHub de wooplans-studio.

À lancer une seule fois, sur ton ordinateur, avec la CLI GitHub connectée (`gh auth login`) :
  python tools/set_github_secrets.py            # envoie
  python tools/set_github_secrets.py --dry-run  # montre seulement les NOMS trouvés / manquants

Aucune valeur n'est affichée ni écrite ailleurs. ZERNIO_PROFILE_ID est imposé : profil « WooPlans » (pas le profil Default de Kilabi).
"""
import argparse
import subprocess
import sys
from pathlib import Path

REPO = "wooplans/wooplans-studio"
FROM_ENV = ["ZERNIO_API_KEY"]                                    # indispensable pour publier
OPTIONAL = ["ELEVENLABS_API_KEY", "POYO_API_KEY"]                # avec --all (génération hors session Claude)
# R2 / Telegram du .env sont ceux de Kilabi : NE PAS les copier (bucket et bot dédiés WooPlans si besoin un jour)
FIXED = {"ZERNIO_PROFILE_ID": "6aca547f2791f56cd0b63f4a"}


def read_env(path: Path) -> dict:
    out = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip("'\"")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default=str(Path(__file__).resolve().parents[2].parent / ".env"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all", action="store_true", help="copie aussi ELEVENLABS_API_KEY et POYO_API_KEY")
    a = ap.parse_args()
    env_path = Path(a.env)
    if not env_path.is_file():
        print(f"Fichier introuvable : {env_path} (utiliser --env)", file=sys.stderr)
        return 2
    env = read_env(env_path)
    if a.all:
        FROM_ENV.extend(OPTIONAL)
    todo = {k: env[k] for k in FROM_ENV if env.get(k)}
    todo.update(FIXED)
    missing = [k for k in FROM_ENV if not env.get(k)]
    for k in todo:
        if a.dry_run:
            print(f"trouvé   {k}")
            continue
        r = subprocess.run(["gh", "secret", "set", k, "--repo", REPO], input=todo[k], text=True, capture_output=True)
        print(f"{'OK      ' if r.returncode == 0 else 'ÉCHEC   '}{k}")
        if r.returncode != 0:
            print((r.stderr or "").strip().splitlines()[-1:] or "", file=sys.stderr)
    for k in missing:
        print(f"MANQUANT {k} (absent du .env)")
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
