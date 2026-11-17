"""Fixtures: uma organizacao falsa (orquestrador + 5 remotos bare locais) sem tocar na rede."""

import os
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

REPOS = ["artemishub_docs", "artemishub_frontend", "artemishub_backend", "artemishub_agents", "artemishub_rag"]

_IDENTIDADE = {
    "GIT_AUTHOR_NAME": "Teste",
    "GIT_AUTHOR_EMAIL": "teste@example.com",
    "GIT_COMMITTER_NAME": "Teste",
    "GIT_COMMITTER_EMAIL": "teste@example.com",
}


def git(*args: str, cwd: Path) -> str:
    """Roda git com identidade fixa e file:// liberado para submodulos."""
    env = {**os.environ, **_IDENTIDADE, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
    result = subprocess.run(
        ["git", "-c", "protocol.file.allow=always", "-c", "init.defaultBranch=main", *args],
        cwd=cwd, env=env, capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


@dataclass
class FakeOrg:
    root: Path
    remotes: dict[str, Path]

    def push_commit(self, repo: str, branch: str, filename: str) -> str:
        """Cria um commit novo na branch do remoto (via clone temporario) e devolve o SHA."""
        remote = self.remotes[repo]
        clone = Path(tempfile.mkdtemp(prefix=f"_tmp_clone_{repo}_", dir=remote.parent))
        try:
            git("clone", "-q", "--branch", branch, str(remote), str(clone), cwd=remote.parent)
            (clone / filename).write_text(f"{filename} {uuid.uuid4()}\n", encoding="utf-8")
            git("add", filename, cwd=clone)
            git("commit", "-q", "-m", f"feat: {filename}", cwd=clone)
            git("push", "-q", "origin", branch, cwd=clone)
            return git("rev-parse", "HEAD", cwd=clone)
        finally:
            _remover(clone)


def _remover(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


def _criar_org(tmp_path: Path, com_staging: bool) -> FakeOrg:
    remotes_dir = tmp_path / "remotes"
    remotes_dir.mkdir()
    remotes: dict[str, Path] = {}
    for repo in REPOS:
        bare = remotes_dir / f"{repo}.git"
        git("init", "-q", "--bare", str(bare), cwd=tmp_path)
        semente = tmp_path / f"_seed_{repo}"
        git("clone", "-q", str(bare), str(semente), cwd=tmp_path)
        (semente / "README.md").write_text(f"# {repo}\n", encoding="utf-8")
        git("add", "README.md", cwd=semente)
        git("commit", "-q", "-m", "chore: inicio", cwd=semente)
        git("push", "-q", "origin", "main", cwd=semente)
        if com_staging:
            git("push", "-q", "origin", "main:staging", cwd=semente)
        _remover(semente)
        remotes[repo] = bare

    root = tmp_path / "orq"
    root.mkdir()
    git("init", "-q", cwd=root)
    branch = "staging" if com_staging else "main"
    for repo in REPOS:
        git("submodule", "add", "-q", "-b", branch, remotes[repo].as_uri(), repo, cwd=root)
    git("commit", "-q", "-m", "chore: submodulos", cwd=root)
    return FakeOrg(root=root, remotes=remotes)


@pytest.fixture
def fake_org(tmp_path: Path) -> FakeOrg:
    return _criar_org(tmp_path, com_staging=True)


@pytest.fixture
def fake_org_sem_staging(tmp_path: Path) -> FakeOrg:
    return _criar_org(tmp_path, com_staging=False)


@pytest.fixture(autouse=True)
def _git_isolado(monkeypatch):
    """Os scripts rodam git de verdade: libera file:// (remotos falsos) e ignora a config da pessoa."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "protocol.file.allow")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "always")
