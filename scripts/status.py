"""Mostra, para cada repo, a branch, mudanças locais, adiantamento/atraso e worktrees."""

from __future__ import annotations

import argparse
from pathlib import Path

from artemis_repos import REPOS, ROOT, git, is_dirty

_CANDIDATAS_UPSTREAM = ("@{u}", "origin/staging", "origin/main")


def _ahead_behind(repo_dir: Path) -> tuple[int, int]:
    """Commits à frente/atrás do upstream, usando só refs locais (sem rede)."""
    for ref in _CANDIDATAS_UPSTREAM:
        contagem = git("rev-list", "--left-right", "--count", f"HEAD...{ref}", cwd=repo_dir, check=False)
        if contagem:
            ahead, behind = contagem.split()
            return int(ahead), int(behind)
    return 0, 0


def collect(root: Path = ROOT) -> list[dict]:
    rows = []
    for repo in REPOS:
        repo_dir = root / repo
        ahead, behind = _ahead_behind(repo_dir)
        listadas = git("worktree", "list", "--porcelain", cwd=repo_dir).splitlines()
        rows.append(
            {
                "repo": repo,
                "branch": git("branch", "--show-current", cwd=repo_dir) or "(detached)",
                "dirty": is_dirty(repo_dir),
                "ahead": ahead,
                "behind": behind,
                "worktrees": sum(1 for linha in listadas if linha.startswith("worktree ")) - 1,
            }
        )
    return rows


def main(root: Path = ROOT) -> int:
    rows = collect(root)
    cabecalho = ("repo", "branch", "sujo", "à frente", "atrás", "worktrees")
    linhas = [
        (r["repo"], r["branch"], "sim" if r["dirty"] else "não", str(r["ahead"]), str(r["behind"]), str(r["worktrees"]))
        for r in rows
    ]
    larguras = [max(len(c) for c in col) for col in zip(cabecalho, *linhas)]
    for linha in (cabecalho, *linhas):
        print("  ".join(c.ljust(w) for c, w in zip(linha, larguras)).rstrip())
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    raise SystemExit(main(parser.parse_args().root))
