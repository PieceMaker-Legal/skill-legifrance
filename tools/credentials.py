"""Identifiants PISTE de Skill Legifrance : chemins, écriture, guide, contrôle OAuth."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple


PISTE_ENVIRONMENTS = {
    "production": {
        "oauth": "https://oauth.piste.gouv.fr/api/oauth/token",
        "api": "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app",
    },
    "sandbox": {
        "oauth": "https://sandbox-oauth.piste.gouv.fr/api/oauth/token",
        "api": "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app",
    },
}

DEFAULT_ENV_DIR = Path.home() / ".config" / "skill-legifrance"
DEFAULT_ENV_FILE = DEFAULT_ENV_DIR / ".env"
MCP_ENV_FILE = Path.home() / ".config" / "mcp-legifrance" / ".env"

CREDENTIAL_KEYS = (
    "LEGIFRANCE_CLIENT_ID",
    "LEGIFRANCE_CLIENT_SECRET",
    "LEGIFRANCE_ENV",
)

PISTE_GUIDE = """\
Mise en place du client PISTE (API Légifrance)
==============================================

Les recherches Légifrance passent par PISTE (AIFE). Créez une application
et souscrivez à l'API Légifrance, puis enregistrez le client OAuth ici.

1. Compte : https://piste.gouv.fr/registration
2. Portail : https://piste.gouv.fr/  (connexion)
3. Menu APPLICATIONS → Créer une application
4. Souscrire à l'API « Légifrance » (DILA)
5. Générer un identifiant OAuth (client_id + client_secret)
6. Production et sandbox ont des identifiants DISTINCTS
7. Guide officiel :
   https://piste.gouv.fr/images/com_apiportal/documentation/UserGuide_navigation_FR.pdf

Enregistrement (ne jamais coller le secret dans un chat ensuite) :

  python3 scripts/legifrance.py setup \\
    --client-id '…' --client-secret '…' --env production --check
"""


def env_file_candidates() -> List[Path]:
    explicit = (os.environ.get("LEGIFRANCE_ENV_FILE") or "").strip()
    if explicit:
        return [Path(explicit).expanduser()]
    return [DEFAULT_ENV_FILE, MCP_ENV_FILE]


def target_env_file() -> Path:
    return env_file_candidates()[0]


def resolved_env_file() -> Optional[Path]:
    for path in env_file_candidates():
        if path.is_file():
            return path
    return None


def _dotenv_value(value: str) -> str:
    if any(char in value for char in ' \t#\'"\\$'):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def _parse_env_lines(text: str) -> Tuple[Dict[str, str], List[str]]:
    values: Dict[str, str] = {}
    others: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            others.append(raw)
            continue
        key, _, rest = line.partition("=")
        key = key.strip()
        if key in CREDENTIAL_KEYS:
            values[key] = rest.strip().strip("'").strip('"')
        else:
            others.append(raw)
    return values, others


def read_env_file(path: Optional[Path] = None) -> Dict[str, str]:
    path = path or resolved_env_file()
    if path is None or not path.is_file():
        return {}
    values, _ = _parse_env_lines(path.read_text(encoding="utf-8"))
    return values


def write_credentials(
    client_id: str,
    client_secret: str,
    env: str = "production",
    path: Optional[Path] = None,
) -> Path:
    client_id = (client_id or "").strip()
    client_secret = (client_secret or "").strip()
    env = (env or "production").strip().lower()
    if not client_id or not client_secret:
        raise ValueError("client_id et client_secret sont requis.")
    if env not in PISTE_ENVIRONMENTS:
        raise ValueError("LEGIFRANCE_ENV doit être production ou sandbox.")
    if "\n" in client_id or "\n" in client_secret:
        raise ValueError("les identifiants ne doivent pas contenir de retour à la ligne.")

    destination = path or target_env_file()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(destination.parent, 0o700)
    except OSError:
        pass

    others: List[str] = []
    if destination.is_file():
        _, others = _parse_env_lines(destination.read_text(encoding="utf-8"))

    lines = [line for line in others if line.strip()]
    lines.extend([
        f"LEGIFRANCE_CLIENT_ID={_dotenv_value(client_id)}",
        f"LEGIFRANCE_CLIENT_SECRET={_dotenv_value(client_secret)}",
        f"LEGIFRANCE_ENV={env}",
        "",
    ])
    payload = "\n".join(lines)
    tmp = destination.with_name(destination.name + ".tmp")
    tmp.write_text(payload, encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(destination)
    os.chmod(destination, 0o600)
    return destination


def credentials_configured(values: Optional[Dict[str, str]] = None) -> bool:
    values = values if values is not None else read_env_file()
    client_id = (os.environ.get("LEGIFRANCE_CLIENT_ID") or values.get("LEGIFRANCE_CLIENT_ID") or "").strip()
    client_secret = (
        os.environ.get("LEGIFRANCE_CLIENT_SECRET") or values.get("LEGIFRANCE_CLIENT_SECRET") or ""
    ).strip()
    if client_id.startswith("${") or client_secret.startswith("${"):
        client_id, client_secret = "", ""
    return bool(client_id and client_secret)


def status_lines(values: Optional[Dict[str, str]] = None) -> List[str]:
    path = resolved_env_file()
    values = values if values is not None else read_env_file(path)
    env_name = (
        os.environ.get("LEGIFRANCE_ENV")
        or values.get("LEGIFRANCE_ENV")
        or "production"
    ).strip().lower()
    present = credentials_configured(values)
    lines = [
        f"fichier: {path if path is not None else target_env_file()} ({'présent' if path is not None else 'absent'})",
        f"client_id: {'configuré' if present else 'manquant'}",
        f"client_secret: {'configuré' if present else 'manquant'}",
        f"environnement: {env_name}",
    ]
    if not present:
        lines.append("action: python3 scripts/legifrance.py setup --client-id … --client-secret … --check")
    return lines


def verify_oauth(client_id: str, client_secret: str, env: str = "production") -> Tuple[bool, str]:
    import requests

    env = (env or "production").strip().lower()
    if env not in PISTE_ENVIRONMENTS:
        return False, "LEGIFRANCE_ENV doit être production ou sandbox."
    url = PISTE_ENVIRONMENTS[env]["oauth"]
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "openid",
            },
            timeout=30,
        )
    except requests.RequestException as error:
        return False, f"Impossible de joindre PISTE: {error}"

    payload: Dict[str, object] = {}
    try:
        parsed = response.json()
        if isinstance(parsed, dict):
            payload = parsed
    except ValueError:
        payload = {}

    if response.ok and payload.get("access_token"):
        return True, f"Jeton OAuth obtenu ({env})."
    detail = payload.get("error_description") or payload.get("error") or response.reason
    return False, f"Échec OAuth HTTP {response.status_code}: {detail}"
