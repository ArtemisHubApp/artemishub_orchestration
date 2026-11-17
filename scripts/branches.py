"""Lista as branches remotas (menos main e staging) com o status e, com --delete, apaga só as mergeadas."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Literal

from artemis_repos import REPOS, ROOT, base_branch, git

Status = Literal["mergeada", "aberta", "desconhecido"]
_PROTEGIDAS = {"main", "staging"}


def _gh_pr_mergeado(repo_dir: Path, branch: str) -> bool | None:
    """True/False conforme o GitHub; None se o `gh` não existe ou falhou."""
    if shutil.which("gh") is None:
        return None
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--head", branch, "--state", "merged", "--json", "number"],
            cwd=repo_dir, capture_output=True, text=True, encoding="utf-8", check=False, timeout=60,
        )
        if result.returncode != 0:
            return None
        return bool(json.loads(result.stdout or "[]"))
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def _ref_existe(repo_dir: Path, ref: str) -> bool:
    return bool(git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", cwd=repo_dir, check=False))


def _e_ancestral(repo_dir: Path, branch: str, base: str) -> bool:
    ref = f"refs/heads/{branch}" if _ref_existe(repo_dir, f"refs/heads/{branch}") else f"origin/{branch}"
    if not _ref_existe(repo_dir, ref) or not _ref_existe(repo_dir, f"origin/{base}"):
        return False
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", ref, f"origin/{base}"], cwd=repo_dir, capture_output=True
    ).returncode == 0


def merged_status(repo_dir: Path, branch: str, base: str) -> Status:
    """`mergeada` só com prova (PR mergeado no gh ou ancestralidade); sem prova e sem gh, `desconhecido`."""
    pr = _gh_pr_mergeado(repo_dir, branch)
    if pr:
        return "mergeada"
    if _e_ancestral(repo_dir, branch, base):
        return "mergeada"
    return "aberta" if pr is False else "desconhecido"


def _remotas(repo_dir: Path) -> list[str]:
    refs = git("for-each-ref", "--format=%(refname:short)", "refs/remotes/origin", cwd=repo_dir).splitlines()
    nomes = [r.removeprefix("origin/") for r in refs if r.startswith("origin/")]
    return sorted(n for n in nomes if n != "HEAD" and n not in _PROTEGIDAS)


def main(root: Path = ROOT, delete: bool = False) -> int:
    for repo in REPOS:
        repo_dir = root / repo
        git("fetch", "--prune", "origin", cwd=repo_dir)
        base = base_branch(repo_dir)
        print(f"{repo}:")
        status = {b: merged_status(repo_dir, b, base) for b in _remotas(repo_dir)}
        if not status:
            print("  (nenhuma branch além de main/staging)")
            continue
        for branch, st in status.items():
            print(f"  {st:<12} {branch}")
        mergeadas = [b for b, st in status.items() if st == "mergeada"]
        if delete and mergeadas:
            resposta = input(f"Apagar {len(mergeadas)} branch(es) mergeada(s) de {repo} no remoto? [s/N] ")
            if resposta.strip().lower() == "s":
                for branch in mergeadas:
                    git("push", "origin", "--delete", branch, cwd=repo_dir)
                    print(f"  apagada: {branch}")
            else:
                print("  nada apagado.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delete", action="store_true", help="apaga no remoto só as branches mergeadas (com confirmação)")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    raise SystemExit(main(args.root, args.delete))
