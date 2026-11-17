"""Módulo comum dos scripts do orquestrador (somente biblioteca padrão)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPOS: tuple[str, ...] = (
    "artemishub_docs",
    "artemishub_frontend",
    "artemishub_backend",
    "artemishub_agents",
    "artemishub_rag",
)

_PREFIXO = "artemishub_"


def resolve_repo(name: str) -> str:
    """Aceita o nome curto (`rag`) ou o completo (`artemishub_rag`)."""
    completo = name if name.startswith(_PREFIXO) else _PREFIXO + name
    if completo not in REPOS:
        validos = ", ".join(f"{r.removeprefix(_PREFIXO)} ({r})" for r in REPOS)
        raise SystemExit(f"Repositório desconhecido: {name!r}. Opções válidas: {validos}.")
    return completo


def git(*args: str, cwd: Path, check: bool = True) -> str:
    """Roda git em `cwd` e devolve o stdout sem espaços nas pontas."""
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=False)
    if check and result.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} falhou em {cwd}:\n{result.stderr.strip()}")
    return result.stdout.strip()


def base_branch(repo_dir: Path) -> str:
    """`staging` se existir em origin; senão `main`, com aviso em stderr."""
    if git("ls-remote", "--heads", "origin", "refs/heads/staging", cwd=repo_dir):  # nome exato, sem sufixo
        return "staging"
    print(f"AVISO: {repo_dir.name} ainda não tem staging; usando main.", file=sys.stderr)
    return "main"


def is_dirty(repo_dir: Path) -> bool:
    """True se houver mudanças locais (rastreadas ou não)."""
    return bool(git("status", "--porcelain", cwd=repo_dir))


def worktrees_root(root: Path = ROOT) -> Path:
    """Pasta das worktrees, irmã do orquestrador (fora de qualquer repo)."""
    return root.parent / "artemishub-worktrees"


def checkout_base(repo_dir: Path, base: str) -> None:
    """Fica na branch `base` atualizada (fetch + checkout + pull --ff-only), sem descartar nada.

    Se a branch local ainda não existe, cria rastreando `origin/<base>`.
    """
    git("fetch", "origin", cwd=repo_dir)
    if git("branch", "--list", base, cwd=repo_dir):
        git("checkout", base, cwd=repo_dir)
        git("pull", "--ff-only", cwd=repo_dir)
    else:
        git("checkout", "-b", base, "--track", f"origin/{base}", cwd=repo_dir)
