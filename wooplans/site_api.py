"""Accès au site wooplans.com par son serveur MCP (JSON-RPC sur HTTPS, jeton WOOPLANS_MCP_TOKEN = MCP_TOKEN du site).

Sert au moteur de shorts : liste des modèles publiés (list_plans), inventaire R2 d'un modèle (list_plan_files) et
téléchargement des rendus d'origine (get_plan_file → lien temporaire signé). Lecture seule.
"""
import json
import os
import urllib.request
from pathlib import Path
from typing import List, Optional

URL = os.environ.get("WOOPLANS_MCP_URL", "https://wooplans.com/api/mcp")
UA = "wooplans-studio/1.0"


class SiteError(RuntimeError):
    pass


def call(tool: str, args: Optional[dict] = None) -> dict:
    token = os.environ.get("WOOPLANS_MCP_TOKEN", "").strip()
    if not token:
        raise SiteError("WOOPLANS_MCP_TOKEN absent (secret GitHub / .env) : accès aux originaux R2 impossible")
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": args or {}}}).encode()
    req = urllib.request.Request(URL, data=body, method="POST", headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        res = json.loads(r.read())
    if "error" in res:
        raise SiteError(f"{tool} : {res['error'].get('message')}")
    out = res["result"]
    if out.get("isError"):
        raise SiteError(f"{tool} : {out['content'][0].get('text', '')}")
    return out.get("structuredContent") or json.loads(out["content"][0]["text"])


def published_plans() -> List[dict]:
    return call("list_plans", {"status": "published"})["items"]


def original_renders(code: str) -> List[dict]:
    """Originaux des rendus d'un modèle, dans l'ordre du site, couverture en premier. Écarte les originaux absents
    et ceux qui portent déjà la pastille du site (watermarked true) ; `watermarked` null (indécidable) est gardé."""
    index = call("list_plan_files", {"code": code})
    renders = sorted(index.get("renders", []), key=lambda r: (not r.get("cover"), r.get("position", 0)))
    out = []
    for r in renders:
        o = r.get("original")
        if o and not o.get("missing") and o.get("watermarked") is not True:
            out.append({"key": o["key"], "width": o.get("width"), "height": o.get("height"), "position": r.get("position")})
    return out


def download(key: str, dest: Path) -> Path:
    link = call("get_plan_file", {"key": key, "inline": False, "minutes": 30})["download_url"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(link, headers={"User-Agent": UA}), timeout=300) as r:
        dest.write_bytes(r.read())
    return dest
