"""Atualiza o orquestrador e cada submódulo (só fast-forward; repos sujos são pulados)."""

from __future__ import annotations

import argparse
from pathlib import Path

from artemis_repos import AVISO_HEAD_LOCAL, REPOS, ROOT, base_branch, checkout_base, git, head_so_local, is_dirty


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
        base = base_branch(repo_dir)
        atual = git("branch", "--show-current", cwd=repo_dir)
        if atual and atual != base:
            print(f"PULADO {repo}: está em {atual}, não em {base}")
            continue
        if head_so_local(repo_dir):
            print(f"PULADO {repo}: {AVISO_HEAD_LOCAL}")
            continue
        antes = git("rev-parse", "HEAD", cwd=repo_dir)
        checkout_base(repo_dir, base)
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
