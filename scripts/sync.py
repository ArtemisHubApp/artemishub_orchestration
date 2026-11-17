"""Atualiza o orquestrador e cada submódulo (só fast-forward; repos sujos são pulados)."""

from __future__ import annotations

import argparse
from pathlib import Path

from artemis_repos import REPOS, ROOT, base_branch, checkout_base, git, is_dirty


def main(root: Path = ROOT) -> int:
    if git("rev-parse", "--abbrev-ref", "@{u}", cwd=root, check=False):
        git("pull", "--ff-only", cwd=root)
    else:
        print("orquestrador: sem upstream configurado; pull ignorado")

    for repo in REPOS:
        repo_dir = root / repo
        if is_dirty(repo_dir):
            print(f"PULADO {repo}: há mudanças locais não commitadas")
            continue
        antes = git("rev-parse", "HEAD", cwd=repo_dir)
        checkout_base(repo_dir, base_branch(repo_dir))
        depois = git("rev-parse", "HEAD", cwd=repo_dir)
        if antes == depois:
            print(f"{repo}: sem novidades")
        else:
            print(f"{repo}:")
            print(git("log", "--oneline", f"{antes}..{depois}", cwd=repo_dir))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    raise SystemExit(main(parser.parse_args().root))
