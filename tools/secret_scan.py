"""Scan anti-fuite avant GitHub. N'affiche JAMAIS une valeur : fichier:ligne + type + 4 premiers caractères masqués.
Deux détecteurs : (1) les valeurs réelles de .env cherchées en littéral dans l'arbre ; (2) motifs génériques de clés.
Respecte .gitignore (git check-ignore si dépôt, sinon liste d'exclusions de base). Code retour 1 si fuite."""
import os, re, sys, pathlib, fnmatch

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", "node_modules", "_secrets", ".venv", "lumo_test", "_deps_wheels"}
TEXT_EXT = {'.py', '.json', '.md', '.txt', '.bat', '.sh', '.yml', '.yaml', '.toml', '.cfg', '.ini', '.js', '.ts', '.tsx', '.html', '.env', '.example', '.ps1', '.csv'}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".mp4", ".wav", ".mp3", ".ttf", ".otf", ".whl", ".zip", ".pyc", ".gif", ".webp", ".pdf"}
PATTERNS = {
    "cle_generique": re.compile(r"""(?i)(api[_-]?key|secret|token|password|passwd|access[_-]?key)["']?\s*[:=]\s*["']([A-Za-z0-9_\-/+=.]{20,})["']"""),
    "sk_": re.compile(r"\bsk[-_][A-Za-z0-9_\-]{20,}"),
    "r8_replicate": re.compile(r"\br8_[A-Za-z0-9]{20,}"),
    "bearer": re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-.=]{25,}"),
}


def env_values():
    f = ROOT / ".env"
    vals = {}
    if f.exists():
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                v = v.strip().strip("'\"")
                if len(v) >= 12 and re.search(r"(?i)(KEY|SECRET|TOKEN|PASS|ACCOUNT|ACCESS)", k):   # pas les noms de modèle ni les URL publiques
                    vals[k.strip()] = v
    return vals


def gitignore_patterns():
    f = ROOT / ".gitignore"
    return [l.strip().rstrip("/") for l in f.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith(("#", "!"))] if f.exists() else []


def ignored(rel: str, pats):
    parts = rel.split("/")
    return any(fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(parts[-1], p) or any(fnmatch.fnmatch(x, p) for x in parts[:-1])
               or rel.startswith(p + "/") for p in pats)


SCOPE = ["wooplans", "tests", "tools", "scripts", "docs", "data", ".github"]
INCLUDES = ["--include=*" + e for e in sorted(TEXT_EXT)]
GREP_RX = (r"sk[-_][A-Za-z0-9_-]{20,}|r8_[A-Za-z0-9]{20,}|[Bb]earer +[A-Za-z0-9_.=-]{25,}|"
           r"(api[_-]?key|secret|token|password|passwd|access[_-]?key)[\"']? *[:=] *[\"'][A-Za-z0-9_/+=.-]{20,}[\"']")


def _grep(args, stdin=None):
    import subprocess, shutil
    grep_bin = shutil.which("grep") or (r"C:\Program Files\Git\usr\bin\grep.exe" if os.name == "nt" and os.path.exists(r"C:\Program Files\Git\usr\bin\grep.exe") else "grep")
    r = subprocess.run([grep_bin, "-rInH", "--exclude-dir=.git", "--exclude-dir=__pycache__", "--exclude-dir=node_modules",
                        "--exclude-dir=_secrets", "--exclude-dir=_deps_wheels"] + INCLUDES + args,
                       input=stdin, capture_output=True, text=True, errors="ignore", cwd=ROOT)
    return r.stdout.splitlines()


def main(include_ignored=False, whole=False):
    """grep (rapide sur le dossier relié) pour trouver les candidats ; analyse Python seulement sur les lignes trouvées."""
    ev, pats, hits = env_values(), gitignore_patterns(), []
    targets = ["."] if whole else [d for d in SCOPE if (ROOT / d).exists()]
    lines = _grep(["-E", GREP_RX] + targets)
    if ev:
        lines += _grep(["-F", "-f", "-"] + targets, stdin="\n".join(ev.values()) + "\n")
    for ln in lines:
        try:
            rel, num, text = ln.split(":", 2)
        except ValueError:
            continue
        rel = rel[2:] if rel.startswith("./") else rel
        if rel == ".env" or (not include_ignored and ignored(rel, pats)):
            continue
        for k, v in ev.items():
            if v in text:
                hits.append((rel, int(num), f"valeur de {k} (.env)"))
        for kind, rx in PATTERNS.items():
            m = rx.search(text)
            if m and "os.environ" not in text and "getenv" not in text:
                val = m.group(m.lastindex or 0)
                if re.search(r"(?i)(your|xxx|example|changeme|placeholder|\.\.\.)", val):
                    continue
                hits.append((rel, int(num), f"{kind} ({val[:4]}…)"))
    for rel, i, kind in sorted(set(hits)):
        print(f"FUITE {rel}:{i}  {kind}")
    print(f"\n{len(set(hits))} occurrence(s)" if hits else "Aucune fuite détectée.", "(fichiers ignorés par .gitignore inclus)" if include_ignored else "(fichiers non ignorés)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main("--include-ignored" in sys.argv, "--all" in sys.argv))
