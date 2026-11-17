"""Cria, lista e limpa worktrees em <pai do orquestrador>/artemishub-worktrees/<repo>/<branch>/."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from artemis_repos import REPOS, ROOT, base_branch, git, is_dirty, resolve_repo, worktrees_root
from branches import e_ancestral, merged_status

BRANCH_RE = re.compile(r"^(feat|fix|chore|docs|refactor|test|ci)/\d+-[a-z0-9]+(-[a-z0-9]+)*$")


def validate_branch(name: str) -> None:
    if not BRANCH_RE.fullmatch(name):
        raise SystemExit(
            f"Nome de branch inválido: {name!r}. Padrão: tipo/<nº issue>-<slug> em minúsculas "
            "(tipos: feat, fix, chore, docs, refactor, test, ci); "
            "use feat/<nº issue>-<slug>, por exemplo feat/20-ocr-diretrizes."
        )


def new(repo: str, branch: str, root: Path = ROOT) -> Path:
    validate_branch(branch)
    repo = resolve_repo(repo)
    repo_dir = root / repo
    destino = worktrees_root(root) / repo / branch
    if destino.exists():
        raise SystemExit(f"O caminho já existe: {destino}")
    git("fetch", "origin", cwd=repo_dir)
    base = base_branch(repo_dir)
    destino.parent.mkdir(parents=True, exist_ok=True)
    # --no-track: a branch nova não segue origin/<base>; o 1º push é `git push -u origin <branch>`.
    git("worktree", "add", "--no-track", "-b", branch, str(destino), f"origin/{base}", cwd=repo_dir)
    return destino


def list_(root: Path = ROOT) -> list[dict]:
    itens = []
    for repo in REPOS:
        blocos = git("worktree", "list", "--porcelain", cwd=root / repo).split("\n\n")
        for bloco in blocos[1:]:  # o primeiro é o checkout principal
            campos = dict(l.split(" ", 1) for l in bloco.splitlines() if " " in l)
            if "worktree" in campos and "branch" in campos:
                itens.append(
                    {
                        "repo": repo,
                        "branch": campos["branch"].removeprefix("refs/heads/"),
                        "path": Path(campos["worktree"]),
                    }
                )
    return itens


def _teve_commit_proprio(repo_dir: Path, branch: str, base: str) -> bool:
    """Prova de que a branch não é só uma worktree recém-criada (cuja ponta também é ancestral da base).

    Vale: ter sido publicada (`origin/<branch>`), ter commits fora de `origin/<base>`,
    ou o reflog da branch ter mais que a entrada de criação.
    """
    if git("rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{branch}", cwd=repo_dir, check=False):
        return True
    if git("rev-list", "--max-count=1", f"origin/{base}..refs/heads/{branch}", cwd=repo_dir, check=False):
        return True
    reflog = git("reflog", "show", "--format=%H", f"refs/heads/{branch}", "--", cwd=repo_dir, check=False)
    return len(reflog.splitlines()) > 1


def _apaga_branch_se_contida(repo_dir: Path, branch: str, base: str) -> None:
    """Apaga a branch local só se a ponta já está em `origin/<base>` (equivale a `branch -d`, nunca `-D`).

    Sem upstream (--no-track), `git branch -d` compararia com o HEAD do checkout principal; por isso a prova
    é a ancestralidade em `origin/<base>`, e o `update-ref` só apaga se a ponta ainda for a mesma.
    """
    ref = f"refs/heads/{branch}"
    sha = git("rev-parse", "--verify", "--quiet", ref, cwd=repo_dir, check=False)
    if sha and e_ancestral(repo_dir, ref, base):
        git("update-ref", "-d", ref, sha, cwd=repo_dir, check=False)


def ignorados(path: Path) -> list[str]:
    """Arquivos ignorados pelo git na worktree (`.env`, `.venv/`, `data/`...): `worktree remove` apaga junto."""
    saida = git("status", "--porcelain", "--ignored", cwd=path, check=False)
    return [linha[3:] for linha in saida.splitlines() if linha.startswith("!! ")]


def prune(root: Path = ROOT, dry_run: bool = True) -> list[Path]:
    """Remove só worktrees limpas cuja branch está `mergeada`; devolve as removidas (ou que seriam).

    Worktree cuja branch nunca teve commit próprio (recém-criada) nunca é removida.
    """
    removidas = []
    for repo in REPOS:
        repo_dir = root / repo
        git("fetch", "origin", cwd=repo_dir, check=False)
        base = base_branch(repo_dir)
        for item in (i for i in list_(root) if i["repo"] == repo):
            path, branch = item["path"], item["branch"]
            if not _teve_commit_proprio(repo_dir, branch, base):
                continue
            if merged_status(repo_dir, branch, base) != "mergeada" or is_dirty(path):
                continue
            if not dry_run:
                git("worktree", "remove", str(path), cwd=repo_dir)
                _apaga_branch_se_contida(repo_dir, branch, base)
            removidas.append(path)
    return removidas


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=root, help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_new = sub.add_parser("new", help="cria uma worktree a partir de origin/staging")
    p_new.add_argument("repo")
    p_new.add_argument("branch")
    sub.add_parser("list", help="lista as worktrees")
    p_prune = sub.add_parser("prune", help="remove worktrees limpas de branches mergeadas")
    p_prune.add_argument("--yes", action="store_true", help="remove de verdade (sem isso, só mostra)")
    args = parser.parse_args(argv)

    if args.cmd == "new":
        print(f"Worktree criada em {new(args.repo, args.branch, args.root)}")
    elif args.cmd == "list":
        for i in list_(args.root):
            print(f"{i['repo']}  {i['branch']}  {i['path']}")
    else:
        removidas = prune(args.root, dry_run=not args.yes)
        verbo = "Removida" if args.yes else "Seria removida"
        for p in removidas:
            extras = [] if args.yes else ignorados(p)
            print(f"{verbo}: {p}")
            if extras:
                print(f"  atenção: apaga também arquivos ignorados: {', '.join(extras)}")
        if not removidas:
            print("Nada para limpar.")
        elif not args.yes:
            print("Use --yes para remover.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
