#!/usr/bin/env python3
"""CLI Légifrance — même contrat que les outils du MCP, sans JSON-RPC."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parent.parent
VENV = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"
STAMP = VENV / ".requirements.sha256"
LOCK = ROOT / ".bootstrap.lock"
LOCAL_USER_ID = "local-skill-user"

sys.path.insert(0, str(ROOT))


def venv_python() -> Path:
    if os.name == "nt":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def requirements_digest() -> str:
    return hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()


def ready() -> bool:
    try:
        return venv_python().is_file() and STAMP.read_text(encoding="utf-8").strip() == requirements_digest()
    except OSError:
        return False


def acquire_lock() -> None:
    deadline = time.monotonic() + 180
    while True:
        try:
            LOCK.mkdir()
            return
        except FileExistsError:
            try:
                stale = time.time() - LOCK.stat().st_mtime > 300
            except OSError:
                stale = False
            if stale:
                shutil.rmtree(LOCK, ignore_errors=True)
                continue
            if ready():
                return
            if time.monotonic() >= deadline:
                raise RuntimeError("installation Python concurrente bloquée depuis plus de 3 minutes")
            time.sleep(0.25)


def bootstrap() -> None:
    if ready():
        return
    acquire_lock()
    if ready():
        return
    try:
        if not venv_python().is_file():
            subprocess.run(
                [sys.executable, "-m", "venv", str(VENV)],
                check=True,
                stdout=sys.stderr,
                stderr=sys.stderr,
            )
        subprocess.run(
            [str(venv_python()), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(REQUIREMENTS)],
            check=True,
            stdout=sys.stderr,
            stderr=sys.stderr,
        )
        STAMP.write_text(f"{requirements_digest()}\n", encoding="utf-8")
    finally:
        shutil.rmtree(LOCK, ignore_errors=True)


def configure_environment() -> None:
    from tools.credentials import resolved_env_file

    if os.environ.get("LEGIFRANCE_ENV_FILE"):
        return
    found = resolved_env_file()
    if found is not None:
        os.environ["LEGIFRANCE_ENV_FILE"] = str(found)


def ensure_runtime(argv: List[str]) -> None:
    bootstrap_only = "--bootstrap-only" in argv
    if Path(sys.executable).resolve() != venv_python().resolve():
        bootstrap()
        if bootstrap_only:
            return
        configure_environment()
        os.execv(
            str(venv_python()),
            [str(venv_python()), str(Path(__file__).resolve()), *argv],
        )
    if bootstrap_only:
        return
    configure_environment()


def flatten_array(values: Optional[List[Any]]) -> Optional[List[Any]]:
    if values is None:
        return None
    flat: List[Any] = []
    for value in values:
        if isinstance(value, str) and "," in value:
            flat.extend(part.strip() for part in value.split(",") if part.strip())
        else:
            flat.append(value)
    return flat


def add_schema_arguments(parser: argparse.ArgumentParser, schema: Dict[str, Any]) -> None:
    properties = schema.get("properties") or {}
    required = set(schema.get("required") or [])
    for name, spec in properties.items():
        flag = f"--{name}"
        help_text = spec.get("description") or name
        kwargs: Dict[str, Any] = {"dest": name, "help": help_text}
        json_type = spec.get("type")
        if json_type == "array":
            kwargs["action"] = "append"
            kwargs["metavar"] = name
        elif json_type == "integer":
            kwargs["type"] = int
            if "minimum" in spec:
                kwargs["metavar"] = name
        elif json_type == "string" and "enum" in spec:
            kwargs["choices"] = spec["enum"]
        if name in required:
            kwargs["required"] = True
        elif "default" in spec:
            kwargs["default"] = spec["default"]
        parser.add_argument(flag, **kwargs)


def build_parser() -> argparse.ArgumentParser:
    from config.mcp_definitions import INITIALIZE_INSTRUCTIONS, MCP_TOOLS

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--bootstrap-only", action="store_true", help=argparse.SUPPRESS)
    common.add_argument(
        "--json",
        action="store_true",
        help="Rend la réponse handler brute en JSON au lieu du texte.",
    )

    parser = argparse.ArgumentParser(
        prog="legifrance",
        description=(
            "Recherche et consultation des sources juridiques officielles françaises "
            "via Légifrance/PISTE et le BODACC."
        ),
        epilog=INITIALIZE_INSTRUCTIONS,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[common],
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMANDE")

    list_parser = subparsers.add_parser(
        "list",
        parents=[common],
        help="Liste les commandes disponibles.",
    )
    list_parser.set_defaults(_meta="list")

    ping_parser = subparsers.add_parser(
        "ping",
        parents=[common],
        help="Vérifie que le script démarre, sans appel réseau.",
    )
    ping_parser.set_defaults(_meta="ping")

    setup_parser = subparsers.add_parser(
        "setup",
        parents=[common],
        help="Guide PISTE, enregistrement du client OAuth, contrôle du jeton.",
        description=(
            "Crée le client PISTE local : guide d'inscription, écriture de "
            "~/.config/skill-legifrance/.env, vérification OAuth optionnelle."
        ),
    )
    setup_parser.add_argument("--client-id", dest="client_id", help="Identifiant OAuth PISTE.")
    setup_parser.add_argument(
        "--client-secret",
        dest="client_secret",
        help="Secret OAuth PISTE. Ne s'affiche pas dans la sortie.",
    )
    setup_parser.add_argument(
        "--env",
        dest="piste_env",
        choices=sorted({"production", "sandbox"}),
        default="production",
        help="Environnement PISTE. production et sandbox ont des identifiants distincts.",
    )
    setup_parser.add_argument(
        "--check",
        action="store_true",
        help="Demande un jeton OAuth après enregistrement, ou pour un client déjà posé.",
    )
    setup_parser.set_defaults(_meta="setup")

    for tool in MCP_TOOLS:
        sub = subparsers.add_parser(
            tool["name"],
            parents=[common],
            help=tool.get("description", ""),
            description=tool.get("description", ""),
        )
        add_schema_arguments(sub, tool.get("inputSchema") or {})
        sub.set_defaults(_tool=tool["name"], _schema=tool.get("inputSchema") or {})

    return parser


def arguments_from_namespace(namespace: argparse.Namespace, schema: Dict[str, Any]) -> Dict[str, Any]:
    properties = schema.get("properties") or {}
    payload: Dict[str, Any] = {}
    for name, spec in properties.items():
        if not hasattr(namespace, name):
            continue
        value = getattr(namespace, name)
        if spec.get("type") == "array":
            value = flatten_array(value)
        if value is None:
            continue
        payload[name] = value
    return payload


def render_text(result: Dict[str, Any]) -> str:
    chunks: List[str] = []
    for item in result.get("content") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "text" and item.get("text"):
            chunks.append(str(item["text"]))
        elif item.get("type") == "resource":
            resource = item.get("resource") or {}
            text = resource.get("text")
            if text:
                chunks.append(str(text))
    if not chunks:
        return ""
    text = "\n\n".join(chunks)
    if not text.endswith("\n"):
        text += "\n"
    return text


def run_setup(namespace: argparse.Namespace) -> int:
    from tools.credentials import (
        PISTE_GUIDE,
        credentials_configured,
        read_env_file,
        status_lines,
        verify_oauth,
        write_credentials,
    )

    client_id = (getattr(namespace, "client_id", None) or "").strip()
    client_secret = (getattr(namespace, "client_secret", None) or "").strip()
    env_name = (getattr(namespace, "piste_env", None) or "production").strip().lower()
    check = bool(getattr(namespace, "check", False))

    if (client_id and not client_secret) or (client_secret and not client_id):
        print("setup exige --client-id et --client-secret ensemble.", file=sys.stderr)
        return 2

    if client_id and client_secret:
        path = write_credentials(client_id, client_secret, env=env_name)
        os.environ["LEGIFRANCE_ENV_FILE"] = str(path)
        print(f"Client PISTE enregistré dans {path} (permissions 600).")
        print("\n".join(status_lines()))
        if check:
            ok, message = verify_oauth(client_id, client_secret, env_name)
            print(message)
            return 0 if ok else 1
        return 0

    print(PISTE_GUIDE.rstrip())
    print()
    print("\n".join(status_lines()))
    if check:
        values = read_env_file()
        stored_id = (os.environ.get("LEGIFRANCE_CLIENT_ID") or values.get("LEGIFRANCE_CLIENT_ID") or "").strip()
        stored_secret = (
            os.environ.get("LEGIFRANCE_CLIENT_SECRET") or values.get("LEGIFRANCE_CLIENT_SECRET") or ""
        ).strip()
        stored_env = (
            os.environ.get("LEGIFRANCE_ENV") or values.get("LEGIFRANCE_ENV") or env_name
        ).strip().lower()
        if not stored_id or not stored_secret:
            print("Contrôle OAuth impossible : identifiants manquants.", file=sys.stderr)
            return 1
        ok, message = verify_oauth(stored_id, stored_secret, stored_env)
        print(message)
        return 0 if ok else 1
    return 0 if credentials_configured() else 1


def run_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    from tools.handlers import handle_tool_call

    return handle_tool_call(name, arguments, LOCAL_USER_ID)


def dispatch(namespace: argparse.Namespace) -> int:
    meta = getattr(namespace, "_meta", None)
    if meta == "list":
        from config.mcp_definitions import MCP_TOOLS

        print("setup\tGuide PISTE, enregistrement du client OAuth, contrôle du jeton.")
        print("ping\tVérifie que le script démarre, sans appel réseau.")
        for tool in MCP_TOOLS:
            print(f"{tool['name']}\t{tool.get('description', '').splitlines()[0]}")
        return 0
    if meta == "ping":
        print("ok")
        return 0
    if meta == "setup":
        return run_setup(namespace)

    name = getattr(namespace, "_tool", None)
    if not name:
        return 2
    schema = getattr(namespace, "_schema") or {}
    arguments = arguments_from_namespace(namespace, schema)
    result = run_tool(name, arguments)
    if getattr(namespace, "json", False):
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_text(result))
    return 1 if result.get("isError") else 0


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--bootstrap-only" in argv:
        return 0
    parser = build_parser()
    if not argv:
        parser.print_help(sys.stderr)
        return 2
    namespace = parser.parse_args(argv)
    return dispatch(namespace)


if __name__ == "__main__":
    try:
        ensure_runtime(sys.argv[1:])
        if "--bootstrap-only" in sys.argv[1:]:
            raise SystemExit(0)
        raise SystemExit(main())
    except Exception as error:
        print(f"Impossible d'exécuter Skill Legifrance : {error}", file=sys.stderr)
        raise SystemExit(1) from error
