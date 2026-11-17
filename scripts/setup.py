"""Prepara o orquestrador: baixa os submódulos e deixa cada um na branch base."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from artemis_repos import REPOS, ROOT, base_branch, checkout_base, git


def main(root: Path = ROOT) -> int:
    if shutil.which("git") is None:
        print("ERRO: git não foi encontrado no PATH. Instale o git e tente de novo.", file=sys.stderr)
        return 1
    if sys.version_info < (3, 11):
        atual = ".".join(map(str, sys.version_info[:3]))
        print(f"ERRO: é preciso Python 3.11 ou mais novo (encontrado {atual}).", file=sys.stderr)
        return 1

    git("submodule", "update", "--init", "--recursive", cwd=root)
    bases = []
    for repo in REPOS:
        repo_dir = root / repo
        base = base_branch(repo_dir)
        checkout_base(repo_dir, base)
        bases.append(base)

    print(f"Pronto: {len(REPOS)} repos em {', '.join(sorted(set(bases)))}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    raise SystemExit(main(parser.parse_args().root))
